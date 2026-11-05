import shutil
import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch

import eccodes
import numpy as np

from app.repositories.forecast_repository import (
    EcmwfOpenDataRepository,
    DemoForecastRepository,
    get_repository,
    _longitude_for_grid,
    _tp_accumulations_to_mm,
)
from app.schemas.forecast import ForecastModel, Location
from app.services.forecast_service import ForecastService
from app.controllers.forecast_controller import ForecastController
from fastapi import HTTPException


class PrecipitationProcessingTests(unittest.TestCase):
    def test_tp_meters_convert_to_millimeters(self):
        np.testing.assert_allclose(
            _tp_accumulations_to_mm(np.array([0.002, 0.0055, 0.012, 0.014]), "m"),
            [2, 5.5, 12, 14],
        )

    def test_tp_mass_per_area_units_are_already_millimeters(self):
        np.testing.assert_allclose(
            _tp_accumulations_to_mm(np.array([2, 5.5]), "kg m**-2"), [2, 5.5]
        )

    def test_unknown_units_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported or missing"):
            _tp_accumulations_to_mm(np.array([0.002]), None)

    def test_missing_and_negative_tp_values_are_rejected(self):
        for values in ([0.001, np.nan], [0.001, -0.002]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                _tp_accumulations_to_mm(np.array(values), "m")

    def test_accumulations_become_intervals(self):
        self.assertEqual(
            EcmwfOpenDataRepository._accumulated_to_intervals(
                np.array([2, 5.5, 12, 14])
            ),
            [2, 3.5, 6.5, 2],
        )

    def test_accumulation_reset_starts_a_new_interval(self):
        self.assertEqual(
            EcmwfOpenDataRepository._accumulated_to_intervals(
                np.array([2, 5.5, 1, 2.5])
            ),
            [2, 3.5, 1, 1.5],
        )

    def test_small_negative_rounding_noise_is_clamped(self):
        self.assertEqual(
            EcmwfOpenDataRepository._accumulated_to_intervals(np.array([1, 0.98])),
            [1, 0],
        )

    def test_invalid_accumulations_are_rejected(self):
        for values in (np.array([]), np.array([np.nan]), np.array([-0.1])):
            with self.subTest(values=values), self.assertRaises(ValueError):
                EcmwfOpenDataRepository._accumulated_to_intervals(values)

    def test_longitudes_match_grid_coordinate_convention(self):
        self.assertEqual(_longitude_for_grid(-1, np.array([0, 90, 180, 270, 359])), 359)
        self.assertEqual(_longitude_for_grid(359, np.array([-180, -90, 0, 90, 180])), -1)

    def test_grib_nearest_point_extraction_sorts_steps_and_wraps_longitude(self):
        # Build a compact, real GRIB2 fixture with ecCodes: two accumulated tp
        # fields intentionally written out of step order on a 0..358 grid.
        with tempfile.TemporaryDirectory(prefix="rainscope-grib-fixture-") as fixture_dir:
            fixture_path = Path(fixture_dir) / "tp.grib2"
            with fixture_path.open("wb") as stream:
                for step, value_at_358, value_at_0 in ((6, 0.007, 0.002), (3, 0.003, 0.001)):
                    message = eccodes.codes_grib_new_from_samples("regular_ll_sfc_grib2")
                    try:
                        eccodes.codes_set(message, "shortName", "tp")
                        eccodes.codes_set(message, "stepType", "accum")
                        eccodes.codes_set(message, "dataDate", 20261105)
                        eccodes.codes_set(message, "dataTime", 0)
                        eccodes.codes_set(message, "step", step)
                        eccodes.codes_set(message, "Ni", 180)
                        eccodes.codes_set(message, "longitudeOfLastGridPointInDegrees", 358.0)
                        eccodes.codes_set(message, "iDirectionIncrementInDegrees", 2.0)
                        values = np.zeros((31, 180), dtype=float)
                        values[24, 179] = value_at_358  # latitude 12, longitude 358
                        values[24, 0] = value_at_0       # reveals failure to wrap -1°
                        eccodes.codes_set_values(message, values.reshape(-1))
                        eccodes.codes_write(message, stream)
                    finally:
                        eccodes.codes_release(message)

            class FakeClient:
                def __init__(self, **kwargs):
                    self.options = kwargs
                    self.session = type("Session", (), {
                        "request": lambda session, *args, **kwargs: None,
                    })()

                def retrieve(self, **kwargs):
                    shutil.copyfile(fixture_path, kwargs["target"])

            location = Location(name="Test", region="", latitude=12, longitude=-1)
            with patch("ecmwf.opendata.Client", FakeClient), \
                    patch.object(EcmwfOpenDataRepository, "_cycle_candidates", return_value=[("20261105", 0)]):
                result = EcmwfOpenDataRepository().get_precipitation(location, ForecastModel.IFS)

        self.assertEqual(result["values_mm"], [3, 4])
        self.assertEqual(result["valid_times"], [
            "2026-11-05T03:00:00Z", "2026-11-05T06:00:00Z"
        ])
        self.assertEqual(result["mode"], "live")

    def test_ecmwf_http_requests_receive_a_bounded_timeout(self):
        class Session:
            def request(self, method, url, **kwargs):
                return kwargs.get("timeout")

        session = Session()
        EcmwfOpenDataRepository._set_request_timeout(session, timeout=(10, 30))

        self.assertEqual(session.request("GET", "https://example.test", timeout=None), (10, 30))


class ForecastServiceTests(unittest.TestCase):
    def setUp(self):
        self.location = Location(name="Erode", region="India", latitude=11.3, longitude=77.7)

    def test_service_rejects_mismatched_arrays_instead_of_truncating(self):
        class InvalidRepository:
            def get_precipitation(self, location, model):
                return {"values_mm": [1, 2], "valid_times": ["t1"],
                        "source": "fixture", "mode": "live", "run_time": "run"}

        with self.assertRaisesRegex(ValueError, "mismatched"):
            ForecastService(InvalidRepository()).get_forecast(self.location, ForecastModel.IFS)

    def test_bad_payload_is_not_cached(self):
        class InvalidRepository:
            calls = 0

            def get_precipitation(inner, location, model):
                inner.calls += 1
                return {"values_mm": [float("nan")], "valid_times": ["t1"],
                        "source": "fixture", "mode": "live", "run_time": "run"}

        repository = InvalidRepository()
        service = ForecastService(repository)
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, "invalid precipitation"):
                service.get_forecast(self.location, ForecastModel.IFS)
        self.assertEqual(repository.calls, 2)

    def test_cache_is_separated_by_model_and_aifs_risk_is_duration_adjusted(self):
        class ModelRepository:
            calls = []

            def get_precipitation(inner, location, model):
                inner.calls.append(model)
                return {"values_mm": [4], "valid_times": ["2026-11-05T06:00:00Z"],
                        "source": "fixture", "mode": "live", "run_time": "2026-11-05T00:00:00Z"}

        repository = ModelRepository()
        service = ForecastService(repository)
        ifs = service.get_forecast(self.location, ForecastModel.IFS)
        aifs = service.get_forecast(self.location, ForecastModel.AIFS)
        aifs_again = service.get_forecast(self.location, ForecastModel.AIFS)

        self.assertEqual(ifs.model, "IFS")
        self.assertEqual(aifs.model, "AIFS")
        self.assertEqual(aifs_again.model, "AIFS")
        self.assertEqual(len(repository.calls), 2)
        self.assertEqual(ifs.forecast[0].intensity, "Moderate")
        self.assertEqual(aifs.forecast[0].rainfall, 4)
        self.assertEqual(aifs.forecast[0].intensity, "Light")
        self.assertEqual(aifs.summary.riskLevel, "Low")

    def test_refresh_bypasses_cache_and_updates_the_cached_run_label(self):
        class ChangingRepository:
            calls = 0

            def get_precipitation(inner, location, model):
                inner.calls += 1
                return {"values_mm": [inner.calls], "valid_times": [f"t{inner.calls}"],
                        "source": "fixture", "mode": "live", "run_time": f"run{inner.calls}"}

        repository = ChangingRepository()
        service = ForecastService(repository)
        first = service.get_forecast(self.location, ForecastModel.IFS)
        cached = service.get_forecast(self.location, ForecastModel.IFS)
        refreshed = service.get_forecast(self.location, ForecastModel.IFS, refresh=True)

        self.assertEqual(repository.calls, 2)
        self.assertEqual(first.runTime, "run1")
        self.assertEqual(cached.runTime, "run1")
        self.assertEqual(refreshed.runTime, "run2")


class ProviderBehaviorTests(unittest.TestCase):
    def test_unknown_provider_does_not_silently_select_demo(self):
        with patch.dict(os.environ, {"FORECAST_PROVIDER": "typo"}):
            with self.assertRaisesRegex(ValueError, "FORECAST_PROVIDER"):
                get_repository()

    def test_provider_selection_is_explicit(self):
        with patch.dict(os.environ, {"FORECAST_PROVIDER": "demo"}):
            self.assertIsInstance(get_repository(), DemoForecastRepository)
        with patch.dict(os.environ, {"FORECAST_PROVIDER": "ecmwf"}):
            self.assertIsInstance(get_repository(), EcmwfOpenDataRepository)

    def test_live_failure_returns_explicit_503_without_demo_payload(self):
        class FailedRepository:
            def get_precipitation(self, location, model):
                raise RuntimeError("private transport detail")

        controller = ForecastController.__new__(ForecastController)
        controller.service = ForecastService(FailedRepository())
        with self.assertRaises(HTTPException) as error:
            controller.forecast(
                Location(name="Erode", region="India", latitude=11, longitude=77),
                ForecastModel.IFS,
            )

        self.assertEqual(error.exception.status_code, 503)
        self.assertIn("unavailable", error.exception.detail)
        self.assertNotIn("private transport detail", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
