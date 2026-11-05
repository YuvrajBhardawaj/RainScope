import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject, catchError, distinctUntilChanged, map, Observable, of, shareReplay, startWith, switchMap, timer } from 'rxjs';
import { ForecastApiService } from '../../../core/services/forecast-api.service';
import { ForecastModel, GeocodingResult, LocationSearchState, Place } from '../../../core/models/forecast.model';

@Component({
  selector: 'app-location-search', standalone: true, imports: [CommonModule, FormsModule],
  template: `
    <div class="controls" *ngIf="searchState$ | async as search">
      <div class="search-wrap" [class.search-open]="query.length >= 2">
        <span class="pin">⌖</span>
        <input [(ngModel)]="query" (ngModelChange)="searchFor($event)" (keydown)="onKeydown($event, search.results)"
          placeholder="Search any city or postcode…" aria-label="Search a city, region, or postcode" role="combobox"
          aria-autocomplete="list" [attr.aria-expanded]="query.length >= 2" aria-controls="location-results">
        <span class="shortcut" *ngIf="!query">Type a city</span><span class="search-spinner" *ngIf="search.loading"></span>
        <div class="suggestions" id="location-results" role="listbox" *ngIf="query.length >= 2">
          <div class="search-message" *ngIf="search.loading">Finding places…</div>
          <button *ngFor="let place of search.results; let i = index" role="option" [attr.aria-selected]="i === activeIndex"
            [class.highlighted]="i === activeIndex" (mouseenter)="activeIndex = i" (click)="select(place)">
            <span class="result-marker">⌖</span><span class="result-copy"><strong>{{place.name}}</strong><small>{{place.admin1 ? place.admin1 + ', ' : ''}}{{place.country}}</small></span>
            <span class="result-type">{{place.feature_code === 'PPLC' ? 'Capital' : 'Place'}}</span>
          </button>
          <div class="search-message" *ngIf="!search.loading && !search.error && !search.results.length">No matching places. Try a longer name or add the country.</div>
          <div class="search-message search-error" *ngIf="search.error">{{search.error}}</div>
          <div class="search-attribution" *ngIf="search.results.length">Location data: GeoNames via Open-Meteo</div>
        </div>
      </div>
      <label class="model-chip"><span class="pulse"></span><span>MODEL</span><select [ngModel]="model" (ngModelChange)="modelChange.emit($event)"><option value="ifs">ECMWF IFS</option><option value="aifs">ECMWF AIFS</option></select></label>
      <button class="export" (click)="exportCsv.emit()">↓ <span>Export CSV</span></button>
      <button class="refresh" (click)="refresh.emit()">↻ <span>Refresh forecast</span></button>
    </div>`,
  styleUrl: './location-search.component.css',
})
export class LocationSearchComponent {
  @Output() locationChange = new EventEmitter<Place>();
  @Input() model: ForecastModel = 'ifs';
  @Output() modelChange = new EventEmitter<ForecastModel>();
  @Output() refresh = new EventEmitter<void>();
  @Output() exportCsv = new EventEmitter<void>();
  query = '';
  activeIndex = -1;
  private readonly querySubject = new BehaviorSubject('');
  readonly searchState$: Observable<LocationSearchState> = this.querySubject.pipe(
    map(query => query.trim()),
    distinctUntilChanged(),
    switchMap(query => {
      if (query.length < 2) return of({ results: [], loading: false, error: null } as LocationSearchState);
      return timer(250).pipe(switchMap(() => this.api.searchLocations(query)),
        map(response => ({ results: response.results, loading: false, error: null }) as LocationSearchState),
        startWith({ results: [], loading: true, error: null } as LocationSearchState),
        catchError(() => of({ results: [], loading: false, error: 'Place search is temporarily unavailable. Please try again.' } as LocationSearchState)),
      );
    }),
    startWith({ results: [], loading: false, error: null } as LocationSearchState),
    shareReplay({ bufferSize: 1, refCount: true }),
  );
  constructor(private readonly api: ForecastApiService) {}

  searchFor(query: string) { this.activeIndex = -1; this.querySubject.next(query); }
  select(place: GeocodingResult) {
    const region = [place.admin1, place.country].filter(Boolean).join(', ');
    this.locationChange.emit({ name: place.name, region, lat: place.latitude, lon: place.longitude });
    this.query = ''; this.querySubject.next(''); this.activeIndex = -1;
  }
  onKeydown(event: KeyboardEvent, results: GeocodingResult[]) {
    if (event.key === 'ArrowDown' && results.length) { event.preventDefault(); this.activeIndex = (this.activeIndex + 1) % results.length; }
    else if (event.key === 'ArrowUp' && results.length) { event.preventDefault(); this.activeIndex = (this.activeIndex - 1 + results.length) % results.length; }
    else if (event.key === 'Enter' && results.length) { event.preventDefault(); this.select(results[this.activeIndex >= 0 ? this.activeIndex : 0]); }
    else if (event.key === 'Escape') { this.query = ''; this.querySubject.next(''); this.activeIndex = -1; }
  }
}
