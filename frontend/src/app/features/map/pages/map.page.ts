import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ForecastModel, Place } from '../../../core/models/forecast.model';
import { ForecastStateService } from '../../../core/services/forecast-state.service';
import { PrecipitationMapComponent } from '../../dashboard/components/precipitation-map.component';
import { LocationSearchComponent } from '../../dashboard/components/location-search.component';
import { AppSidebarComponent } from '../../../shared/components/app-sidebar.component';

@Component({
  selector: 'app-map-page', standalone: true,
  imports: [CommonModule, PrecipitationMapComponent, LocationSearchComponent, AppSidebarComponent],
  template: `<main class="shell"><app-sidebar></app-sidebar><section class="workspace"><header class="topbar"><div class="brand">Rain<span>scope</span><small>PRECIPITATION INTELLIGENCE</small></div><div class="top-right"><span class="status-dot"></span><span>Forecast system operational</span></div></header><section class="intro"><div><div class="eyebrow">EXPLORE <span> / </span> SPATIAL FORECAST</div><h1>Rainfall, <em>around you.</em></h1><p>Explore expected precipitation across nearby locations.</p></div></section><app-location-search [model]="(model$ | async) ?? 'ifs'" (locationChange)="selectLocation($event)" (modelChange)="selectModel($event)"></app-location-search><section *ngIf="location$ | async as location" class="map-page"><div class="map-location"><strong>{{location.name}}</strong><span>{{location.region}}</span></div><app-precipitation-map [location]="location" [model]="(model$ | async) ?? 'ifs'"></app-precipitation-map><p class="map-explainer">Choose a grid cell to inspect its illustrative rainfall amount. Live ECMWF forecast values are available in the dashboard; this surrounding grid layer is still demo data.</p></section></section></main>`,
})
export class MapPage {
  private readonly state = inject(ForecastStateService);
  readonly location$ = this.state.location$;
  readonly model$ = this.state.model$;
  selectLocation(location: Place) { this.state.selectLocation(location); }
  selectModel(model: ForecastModel) { this.state.selectModel(model); }
}
