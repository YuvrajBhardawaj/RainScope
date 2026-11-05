import logging

from fastapi import HTTPException

from app.repositories.forecast_repository import get_repository
from app.schemas.forecast import ForecastModel, ForecastResponse, GridResponse, Location
from app.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)


class ForecastController:
    def __init__(self):
        self.service = ForecastService(get_repository())

    def forecast(
        self, location: Location, model: ForecastModel, *, refresh: bool = False,
    ) -> ForecastResponse:
        try:
            return self.service.get_forecast(location, model, refresh=refresh)
        except Exception:
            logger.exception("Forecast request failed for model %s", model.value)
            raise HTTPException(
                status_code=503,
                detail="Forecast data is unavailable from the configured provider. Please try again later.",
            ) from None

    def grid(self, location: Location, model: ForecastModel) -> GridResponse:
        return GridResponse(**self.service.get_grid(location, model))
