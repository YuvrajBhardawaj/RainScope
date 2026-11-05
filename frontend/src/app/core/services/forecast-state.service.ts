import { Injectable } from '@angular/core';
import { BehaviorSubject, catchError, combineLatest, map, of, shareReplay, startWith, switchMap } from 'rxjs';
import { ForecastApiService } from './forecast-api.service';
import { ForecastModel, ForecastState, Place } from '../models/forecast.model';

const DEFAULT_LOCATION: Place = { name: 'Erode', region: 'Tamil Nadu, India', lat: 11.341, lon: 77.717 };

@Injectable({ providedIn: 'root' })
export class ForecastStateService {
  private readonly locationSubject = new BehaviorSubject<Place>(DEFAULT_LOCATION);
  private readonly modelSubject = new BehaviorSubject<ForecastModel>('ifs');
  private readonly refreshSubject = new BehaviorSubject<number>(0);

  readonly location$ = this.locationSubject.asObservable();
  readonly model$ = this.modelSubject.asObservable();
  readonly state$ = combineLatest([this.locationSubject, this.modelSubject, this.refreshSubject]).pipe(
    switchMap(([location, model]) => this.api.getForecast(location, model).pipe(
      map(forecast => ({ forecast, loading: false, error: null }) as ForecastState),
      startWith({ forecast: null, loading: true, error: null } as ForecastState),
      catchError(() => of({ forecast: null, loading: false, error: 'Forecast data could not be loaded. Check the API and selected model.' } as ForecastState)),
    )),
    shareReplay({ bufferSize: 1, refCount: true }),
  );

  constructor(private readonly api: ForecastApiService) {}
  selectLocation(location: Place) { this.locationSubject.next(location); }
  selectModel(model: ForecastModel) { this.modelSubject.next(model); }
  refresh() { this.refreshSubject.next(this.refreshSubject.value + 1); }
}
