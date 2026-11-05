from fastapi import HTTPException

from app.repositories.forecast_repository import get_repository
from app.schemas.forecast import ForecastModel, ForecastResponse, GridResponse, Location
from app.services.forecast_service import ForecastService


class ForecastController:
    def __init__(self):
        self.service = ForecastService(get_repository())

    def forecast(self, location: Location, model: ForecastModel) -> ForecastResponse:
        try:
            return self.service.get_forecast(location, model)
        except Exception as error:
            raise HTTPException(
                status_code=503,
                detail=f"Forecast data is unavailable from the configured provider: {error}",
            ) from error

    def grid(self, location: Location, model: ForecastModel) -> GridResponse:
        return GridResponse(**self.service.get_grid(location, model))
