from time import monotonic

from app.repositories.forecast_repository import ForecastRepository
from app.schemas.forecast import ForecastModel, ForecastResponse, ForecastSummary, Location


class ForecastService:
    def __init__(self, repository: ForecastRepository):
        self.repository = repository
        self._cache: dict[tuple[float, float, str], tuple[float, dict]] = {}

    def get_forecast(self, location: Location, model: ForecastModel) -> ForecastResponse:
        cache_key = (location.latitude, location.longitude, model.value)
        expired = [key for key, (created, _) in self._cache.items() if monotonic() - created >= 1800]
        for key in expired:
            del self._cache[key]
        cached = self._cache.get(cache_key)
        if cached and monotonic() - cached[0] < 1800:
            raw = cached[1]
        else:
            raw = self.repository.get_precipitation(location, model)
            self._cache[cache_key] = (monotonic(), raw)
            if len(self._cache) > 256:
                oldest = min(self._cache, key=lambda key: self._cache[key][0])
                del self._cache[oldest]
        points = [
            {"time": timestamp, "rainfall": amount, "intensity": self._intensity(amount)}
            for timestamp, amount in zip(raw["valid_times"], raw["values_mm"])
        ]
        peak = max((point["rainfall"] for point in points), default=0.0)
        risk = "High" if peak > 7.5 else "Moderate" if peak >= 2.5 else "Low"
        return ForecastResponse(
            location=location,
            model=model.value.upper(),
            source=raw["source"],
            mode=raw["mode"],
            interval="3-hourly" if model == ForecastModel.IFS else "6-hourly",
            forecast=points,
            summary=ForecastSummary(
                totalRainfall=round(sum(point["rainfall"] for point in points), 1),
                maxRainfall=round(peak, 1),
                riskLevel=risk,
            ),
        )

    def get_grid(self, location: Location, model: ForecastModel) -> dict:
        # The grid API follows the same repository/service boundary. For now it
        # exposes a compact sample footprint; a full GRIB raster is a follow-up.
        offsets = (-0.3, 0.0, 0.3)
        values = ((1.1, 2.2, 1.5), (2.8, 4.1, 3.2), (1.4, 2.6, 1.8))
        return {"model": model.value.upper(), "mode": "demo", "unit": "mm", "cells": [
            {"lat": round(location.latitude + dy, 3), "lon": round(location.longitude + dx, 3), "rainfall": amount}
            for dy, row in zip(offsets, values)
            for dx, amount in zip(offsets, row)
        ]}

    @staticmethod
    def _intensity(mm: float) -> str:
        if mm <= 0:
            return "None"
        if mm < 2.5:
            return "Light"
        if mm < 7.5:
            return "Moderate"
        if mm <= 15:
            return "Heavy"
        return "Very heavy"
