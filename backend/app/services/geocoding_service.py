from app.repositories.geocoding_repository import GeocodingRepository
from app.schemas.location import LocationSearchResponse


class GeocodingService:
    def __init__(self, repository: GeocodingRepository):
        self.repository = repository

    def search(self, query: str) -> LocationSearchResponse:
        results = self.repository.search(query.strip())
        return LocationSearchResponse(results=results)
