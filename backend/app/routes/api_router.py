from fastapi import APIRouter, Query

from app.controllers.forecast_controller import ForecastController
from app.controllers.location_controller import LocationController
from app.schemas.forecast import ForecastModel, ForecastResponse, GridResponse, Location
from app.schemas.location import LocationSearchResponse

api_router = APIRouter()
controller = ForecastController()
location_controller = LocationController()


@api_router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "RainScope API"}


@api_router.get("/locations/search", response_model=LocationSearchResponse)
def search_locations(q: str = Query(min_length=2, max_length=100)) -> LocationSearchResponse:
    return location_controller.search(q)


@api_router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    lat: float = Query(11.341, ge=-90, le=90),
    lon: float = Query(77.717, ge=-180, le=180),
    name: str = Query("Erode", min_length=1, max_length=80),
    region: str = Query("Tamil Nadu, India", max_length=120),
    model: ForecastModel = ForecastModel.IFS,
    refresh: bool = Query(False, description="Bypass the 30-minute forecast cache"),
) -> ForecastResponse:
    return controller.forecast(
        Location(name=name, region=region, latitude=lat, longitude=lon), model, refresh=refresh,
    )


@api_router.get("/forecast/grid", response_model=GridResponse)
def get_forecast_grid(
    lat: float = Query(11.341, ge=-90, le=90),
    lon: float = Query(77.717, ge=-180, le=180),
    model: ForecastModel = ForecastModel.IFS,
) -> GridResponse:
    return controller.grid(
        Location(name="Selected location", region="", latitude=lat, longitude=lon), model,
    )
