from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
import os
import tempfile
from pathlib import Path

import numpy as np
import xarray as xr

from app.schemas.forecast import ForecastModel, Location


class ForecastRepository(ABC):
    @abstractmethod
    def get_precipitation(self, location: Location, model: ForecastModel) -> dict:
        """Return raw interval rainfall values and their provenance."""


class DemoForecastRepository(ForecastRepository):
    """Repeatable, clearly marked sample data for local UI development."""

    def get_precipitation(self, location: Location, model: ForecastModel) -> dict:
        interval_hours = 3 if model == ForecastModel.IFS else 6
        values = ([0.0, 0.4, 1.2, 3.8, 6.4, 4.1, 1.7, 0.3]
                  if interval_hours == 3 else [0.0, 1.2, 6.4, 1.7])
        return {
            "values_mm": values,
            "valid_times": [
                (datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
                 + timedelta(hours=interval_hours * index)).isoformat().replace("+00:00", "Z")
                for index in range(len(values))
            ],
            "run_time": datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z"),
            "source": "Illustrative sample",
            "mode": "demo",
        }


class EcmwfOpenDataRepository(ForecastRepository):
    """Downloads the tp parameter and decodes nearest-grid-point precipitation."""

    def get_precipitation(self, location: Location, model: ForecastModel) -> dict:
        from ecmwf.opendata import Client

        model_name = "ifs" if model == ForecastModel.IFS else "aifs-single"
        # IFS has 3-hour steps through 144 h; AIFS is 6-hourly. Request one day.
        steps = list(range(3, 25, 3)) if model == ForecastModel.IFS else [6, 12, 18, 24]
        with tempfile.TemporaryDirectory(prefix="rainscope-") as temp_dir:
            client = Client(
                source="ecmwf",
                model=model_name,
                maximum_retries=1,
                retry_after=1,
                use_server_retry_after=False,
                **({} if model == ForecastModel.AIFS else {"resol": "0p25"}),
            )
            self._set_request_timeout(client.session, timeout=(10, 30))
            last_error = None
            for cycle in self._cycle_candidates():
                target = Path(temp_dir) / f"tp-{cycle[0]}-{cycle[1]}.grib2"
                try:
                    client.retrieve(date=cycle[0], time=cycle[1], type="fc", stream="oper",
                                    param="tp", step=steps, target=str(target))
                    dataset = xr.open_dataset(
                        target, engine="cfgrib", backend_kwargs={"filter_by_keys": {"shortName": "tp"}},
                    )
                    try:
                        data = dataset["tp"]
                        lat_name = "latitude" if "latitude" in data.coords else "lat"
                        lon_name = "longitude" if "longitude" in data.coords else "lon"
                        if lat_name not in data.coords or lon_name not in data.coords:
                            raise ValueError("ECMWF tp data is missing latitude or longitude coordinates")
                        query_lon = _longitude_for_grid(location.longitude, data[lon_name].values)
                        point = data.sel({lat_name: location.latitude, lon_name: query_lon}, method="nearest")
                        accumulations_mm = _tp_accumulations_to_mm(point.values, data.attrs.get("units"))
                        steps_coord = np.asarray(point.coords.get("step", steps)).reshape(-1)
                        if len(steps_coord) != len(accumulations_mm):
                            raise ValueError("ECMWF tp values and forecast steps have different lengths")
                        step_hours = [self._step_hours(step) for step in steps_coord]
                        if not step_hours or any(step <= 0 for step in step_hours) or len(set(step_hours)) != len(step_hours):
                            raise ValueError("ECMWF tp forecast steps are empty or invalid")
                        ordered = sorted(zip(step_hours, accumulations_mm), key=lambda pair: pair[0])
                        step_hours = [step for step, _ in ordered]
                        accumulations_mm = np.asarray([value for _, value in ordered], dtype=float)
                        interval_mm = self._accumulated_to_intervals(accumulations_mm)
                        valid_times = [
                            (datetime.strptime(cycle[0] + f"{cycle[1]:02d}", "%Y%m%d%H")
                             .replace(tzinfo=timezone.utc) + timedelta(hours=step)).isoformat().replace("+00:00", "Z")
                            for step in step_hours
                        ]
                    finally:
                        dataset.close()
                    run_time = datetime.strptime(cycle[0] + f"{cycle[1]:02d}", "%Y%m%d%H").replace(tzinfo=timezone.utc)
                    return {"values_mm": interval_mm, "valid_times": valid_times,
                            "run_time": run_time.isoformat().replace("+00:00", "Z"),
                            "source": f"ECMWF Open Data ({model_name.upper()})", "mode": "live"}
                except Exception as error:
                    last_error = error
            raise RuntimeError(f"No usable ECMWF cycle found in recent runs: {last_error}") from last_error

    @staticmethod
    def _cycle_candidates() -> list[tuple[str, int]]:
        # ECMWF publishes four operational cycles daily. Older recent cycles
        # are attempted when a newly initialized forecast has not been released.
        now = datetime.now(timezone.utc)
        cycle_hour = (now.hour // 6) * 6
        latest = now.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)
        cycles = []
        for offset in range(6):
            candidate = latest - timedelta(hours=6 * offset)
            cycles.append((candidate.strftime("%Y%m%d"), candidate.hour))
        return cycles

    @staticmethod
    def _step_hours(value) -> int:
        return int(value / np.timedelta64(1, "h")) if isinstance(value, np.timedelta64) else int(value)

    @staticmethod
    def _set_request_timeout(session, timeout: tuple[int, int]) -> None:
        # ecmwf-opendata does not expose requests' timeout through Client.
        # Its HTTP downloader passes timeout=None, so set a bounded default
        # on the underlying requests.Session to avoid indefinitely hung reads.
        original_request = session.request

        def request_with_timeout(method, url, **kwargs):
            if kwargs.get("timeout") is None:
                kwargs["timeout"] = timeout
            return original_request(method, url, **kwargs)

        session.request = request_with_timeout

    @staticmethod
    def _accumulated_to_intervals(accumulations_mm: np.ndarray) -> list[float]:
        accumulations = np.asarray(accumulations_mm, dtype=float).reshape(-1)
        if not len(accumulations):
            raise ValueError("ECMWF tp forecast contains no precipitation values")
        if not np.isfinite(accumulations).all():
            raise ValueError("ECMWF tp forecast contains missing or non-finite precipitation values")
        if (accumulations < 0).any():
            raise ValueError("ECMWF tp forecast contains negative accumulated precipitation")

        previous = 0.0
        intervals = []
        for accumulated in accumulations:
            amount = float(accumulated - previous)
            # A negative difference indicates an accumulation reset or a changed field.
            if amount < -0.05:
                amount = float(accumulated)
            intervals.append(round(max(0.0, amount), 2))
            previous = float(accumulated)
        return intervals


def _longitude_for_grid(longitude: float, grid_longitudes: np.ndarray) -> float:
    """Convert conventional longitude to the coordinate convention in a GRIB grid."""
    values = np.asarray(grid_longitudes, dtype=float)
    if values.size == 0 or not np.isfinite(values).all():
        raise ValueError("ECMWF longitude coordinate is empty or invalid")
    if values.min() >= 0 and values.max() > 180:
        return float(longitude % 360)
    return float(((longitude + 180) % 360) - 180)


def _tp_accumulations_to_mm(values: np.ndarray, units: str | None) -> np.ndarray:
    """Convert ECMWF total precipitation (tp) from its declared GRIB unit to mm."""
    normalized_units = (units or "").strip().lower().replace(" ", "")
    if normalized_units in {"m", "mofwater"}:
        multiplier = 1000.0
    elif normalized_units in {"mm", "kgm-2", "kgm**-2", "kg/m2"}:
        multiplier = 1.0
    else:
        raise ValueError(f"Unsupported or missing ECMWF tp unit: {units!r}")

    accumulations = np.ma.asarray(values, dtype=float).filled(np.nan).reshape(-1) * multiplier
    if not len(accumulations) or not np.isfinite(accumulations).all():
        raise ValueError("ECMWF tp forecast contains missing or non-finite precipitation values")
    if (accumulations < 0).any():
        raise ValueError("ECMWF tp forecast contains negative accumulated precipitation")
    return accumulations


def get_repository() -> ForecastRepository:
    provider = os.getenv("FORECAST_PROVIDER", "ecmwf").lower()
    if provider == "demo":
        return DemoForecastRepository()
    if provider == "ecmwf":
        return EcmwfOpenDataRepository()
    raise ValueError("FORECAST_PROVIDER must be either 'ecmwf' or 'demo'")
