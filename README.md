# RainScope

## Problem statement

**Project 1: Precipitation forecast app. Fetch precipitation forecasts from ECMWF Open Data (IFS or AIFS), process them, and deploy a web application that presents the forecast through an innovative front end and user experience.**

RainScope is being built against that exact problem statement. It is an Angular + FastAPI application for location-based precipitation forecasts, rainfall summaries, an interval chart, and a nearby precipitation map. Forecast numbers are marked `DEMO DATA` unless the ECMWF provider is explicitly enabled and returns decoded data.

## Project structure

```text
backend/app/
  repositories/  ECMWF Open Data and demo data sources
  services/      interval summaries, risk classification, caching
  controllers/   HTTP-facing orchestration/error mapping
  routes/        FastAPI endpoint definitions
  schemas/       request/response models
frontend/src/app/
  core/models/   typed forecast and location contracts
  core/services/ HTTP API and BehaviorSubject state
  features/dashboard/pages/      routed dashboard page
  features/dashboard/components/  search, summary, chart, insights, map
  shared/pipes/  reusable forecast display helpers
```

Request direction is `route → controller → service → repository`; the repository is the data-access boundary and can be switched between the deterministic demo adapter and ECMWF Open Data.

## Application flow

1. The dashboard page coordinates location/model selection and presents the state stream.
2. `ForecastStateService` owns `BehaviorSubject`s for selected location, model, and refresh events. Its observable state switches to the newest API request and publishes loading, forecast, or error state.
3. `ForecastApiService` sends the forecast and map-grid requests to FastAPI.
4. The route validates query parameters, the controller handles provider failures, and `ForecastService` applies a 30-minute cache and computes interval labels and summary values.
5. `EcmwfOpenDataRepository` retrieves the `tp` parameter, decodes GRIB2 through cfgrib/ecCodes, samples the nearest grid cell, converts accumulated precipitation to interval rainfall, and tries recent forecast cycles when the newest run is not available.
6. Reusable Angular components render the returned forecast; the map shows spatial grid cells, and CSV export uses the same forecast response.

## Run locally

Use two terminals. Python 3.10+ and Node.js 20.19+ are recommended for the generated Angular 19 setup.

**Backend (PowerShell):**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```powershell
cd frontend
npm install
npm start
```

Open `http://localhost:4200`. Swagger docs are at `http://localhost:8000/docs`. The Angular proxy forwards `/api` to FastAPI.

## Enable ECMWF Open Data

The default provider is the clearly labeled demo adapter. Set `FORECAST_PROVIDER=ecmwf` in the backend environment to use the real repository. Install the Python packages from `backend/requirements.txt`; GRIB decoding needs ecCodes and cfgrib. If the selected live cycle is not available, the API reports a provider error instead of silently substituting sample rainfall.

The repository uses `ifs` for the ECMWF IFS model and `aifs-single` for deterministic AIFS. ECMWF currently documents IFS operational runs at 00/06/12/18 UTC with 3-hour steps for the near range; AIFS Single uses 6-hour steps. See [ECMWF Open Data forecast catalogue](https://confluence.ecmwf.int/spaces/DAC/pages/272310539/ECMWF+open+data+real-time+forecasts+from+IFS+and+AIFS) and [AIFS data details](https://confluence.ecmwf.int/spaces/DAC/pages/738041086/ECMWF+open+data+AIFS+machine-learning+data).

City search is currently a small local list; geocoding, deployment configuration, and a live ECMWF raster grid are follow-up work. Risk bands are illustrative application thresholds, not official warnings or flood predictions.
