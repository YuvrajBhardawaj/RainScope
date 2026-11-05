import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Forecast, ForecastGrid, ForecastModel, GeocodingResult, Place } from '../models/forecast.model';

@Injectable({ providedIn: 'root' })
export class ForecastApiService {
  constructor(private readonly http: HttpClient) {}

  getForecast(place: Place, model: ForecastModel): Observable<Forecast> {
    return this.http.get<Forecast>('/api/forecast', {
      params: { lat: place.lat, lon: place.lon, name: place.name, region: place.region, model },
    });
  }

  getGrid(place: Place, model: ForecastModel): Observable<ForecastGrid> {
    return this.http.get<ForecastGrid>('/api/forecast/grid', { params: { lat: place.lat, lon: place.lon, model } });
  }

  searchLocations(query: string): Observable<{ results: GeocodingResult[] }> {
    return this.http.get<{ results: GeocodingResult[] }>('/api/locations/search', { params: { q: query } });
  }
}
