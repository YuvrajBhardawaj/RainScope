from fastapi import HTTPException

from app.repositories.geocoding_repository import GeocodingRepository
from app.schemas.location import LocationSearchResponse
from app.services.geocoding_service import GeocodingService


class LocationController:
    def __init__(self):
        self.service = GeocodingService(GeocodingRepository())

    def search(self, query: str) -> LocationSearchResponse:
        try:
            return self.service.search(query)
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
