from pydantic import BaseModel


class LocationSearchResult(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    country: str = ""
    country_code: str = ""
    admin1: str = ""
    feature_code: str = ""

    @property
    def region(self) -> str:
        parts = [part for part in (self.admin1, self.country) if part and part != self.name]
        return ", ".join(dict.fromkeys(parts))


class LocationSearchResponse(BaseModel):
    results: list[LocationSearchResult]
