from enum import Enum

from pydantic import BaseModel, Field


class ForecastModel(str, Enum):
    IFS = "ifs"
    AIFS = "aifs"


class Location(BaseModel):
    name: str
    region: str
    latitude: float
    longitude: float


class ForecastPoint(BaseModel):
    time: str
    rainfall: float = Field(ge=0)
    intensity: str


class ForecastSummary(BaseModel):
    totalRainfall: float
    maxRainfall: float
    riskLevel: str


class ForecastResponse(BaseModel):
    location: Location
    model: str
    source: str
    mode: str
    runTime: str
    unit: str = "mm"
    interval: str
    forecast: list[ForecastPoint]
    summary: ForecastSummary


class GridCell(BaseModel):
    lat: float
    lon: float
    rainfall: float


class GridResponse(BaseModel):
    model: str
    mode: str
    unit: str
    cells: list[GridCell]
