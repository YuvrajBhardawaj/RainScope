import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, ElementRef, Input, OnChanges, OnDestroy, SimpleChanges, ViewChild } from '@angular/core';
import * as L from 'leaflet';
import { Subscription, catchError, of } from 'rxjs';
import { ForecastModel, ForecastGrid, Place } from '../../../core/models/forecast.model';
import { ForecastApiService } from '../../../core/services/forecast-api.service';

@Component({
  selector: 'app-precipitation-map', standalone: true, imports: [CommonModule],
  template: `<article class="panel map-panel"><div class="panel-head"><div><div class="panel-kicker">SPATIAL PRECIPITATION</div><h3>Nearby rainfall</h3></div><span class="map-data-tag">{{grid?.mode === 'live' ? 'ECMWF GRID' : 'DEMO GRID'}}</span></div><div #mapElement class="map-canvas" role="img" aria-label="Map showing precipitation around the selected location"></div><div class="map-legend"><span><i class="low"></i>Light</span><span><i class="mid"></i>Moderate</span><span><i class="high"></i>Heavy</span><small *ngIf="error">Map grid unavailable</small><small *ngIf="grid?.mode === 'demo'">Illustrative grid cells</small></div></article>`,
})
export class PrecipitationMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input({ required: true }) location!: Place;
  @Input() model: ForecastModel = 'ifs';
  @ViewChild('mapElement') mapElement!: ElementRef<HTMLDivElement>;
  grid: ForecastGrid | null = null;
  error = false;
  private map?: L.Map;
  private layer?: L.LayerGroup;
  private request?: Subscription;

  constructor(private readonly api: ForecastApiService) {}
  ngAfterViewInit() {
    this.map = L.map(this.mapElement.nativeElement, { zoomControl: false, scrollWheelZoom: false }).setView([this.location.lat, this.location.lon], 9);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors', maxZoom: 18 }).addTo(this.map);
    L.control.zoom({ position: 'topright' }).addTo(this.map);
    this.layer = L.layerGroup().addTo(this.map);
    this.loadGrid();
    setTimeout(() => this.map?.invalidateSize(), 0);
  }
  ngOnChanges(changes: SimpleChanges) {
    if ((changes['location'] || changes['model']) && this.map) {
      this.map.setView([this.location.lat, this.location.lon], this.map.getZoom());
      this.loadGrid();
    }
  }
  ngOnDestroy() { this.request?.unsubscribe(); this.map?.remove(); }

  private loadGrid() {
    this.request?.unsubscribe();
    this.request = this.api.getGrid(this.location, this.model).pipe(catchError(() => { this.error = true; return of(null); })).subscribe(grid => {
      if (!grid || !this.map || !this.layer) return;
      this.grid = grid; this.error = false; this.layer.clearLayers();
      grid.cells.forEach(cell => {
        const color = cell.rainfall >= 7.5 ? '#d58b5d' : cell.rainfall >= 2.5 ? '#74a87b' : '#b9d0a4';
        L.rectangle([[cell.lat - 0.15, cell.lon - 0.15], [cell.lat + 0.15, cell.lon + 0.15]], {
          color, fillColor: color, fillOpacity: 0.38, weight: 1,
        }).bindTooltip(`${cell.rainfall.toFixed(1)} mm`).addTo(this.layer!);
      });
      L.circleMarker([this.location.lat, this.location.lon], { radius: 6, color: '#fff', weight: 2, fillColor: '#264939', fillOpacity: 1 }).bindTooltip(this.location.name).addTo(this.layer);
    });
  }
}
