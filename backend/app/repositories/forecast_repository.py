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
            client = Client(source="ecmwf", model=model_name, **({} if model == ForecastModel.AIFS else {"resol": "0p25"}))
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
                        point = data.sel({lat_name: location.latitude, lon_name: location.longitude}, method="nearest")
                        accumulations_mm = np.asarray(point.values, dtype=float).reshape(-1) * 1000.0
                        interval_mm = self._accumulated_to_intervals(accumulations_mm)
                        steps_coord = np.asarray(point.coords.get("step", steps)).reshape(-1)
                        valid_times = [
                            (datetime.strptime(cycle[0] + f"{cycle[1]:02d}", "%Y%m%d%H")
                             .replace(tzinfo=timezone.utc) + timedelta(hours=self._step_hours(step))).isoformat().replace("+00:00", "Z")
                            for step in steps_coord
                        ]
                    finally:
                        dataset.close()
                    return {"values_mm": interval_mm, "valid_times": valid_times,
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
    def _accumulated_to_intervals(accumulations_mm: np.ndarray) -> list[float]:
        previous = 0.0
        intervals = []
        for accumulated in accumulations_mm:
            amount = float(accumulated - previous)
            # A negative difference indicates an accumulation reset or a changed field.
            if amount < -0.05:
                amount = float(accumulated)
            intervals.append(round(max(0.0, amount), 2))
            previous = float(accumulated)
        return intervals


def get_repository() -> ForecastRepository:
    if os.getenv("FORECAST_PROVIDER", "demo").lower() == "ecmwf":
        return EcmwfOpenDataRepository()
    return DemoForecastRepository()
