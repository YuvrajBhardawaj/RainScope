import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ForecastModel, ForecastState, Place } from '../../../core/models/forecast.model';
import { ForecastStateService } from '../../../core/services/forecast-state.service';
import { ForecastInsightsComponent } from '../components/forecast-insights.component';
import { ForecastSummaryComponent } from '../components/forecast-summary.component';
import { LocationSearchComponent } from '../components/location-search.component';
import { RainfallChartComponent } from '../components/rainfall-chart.component';
import { PrecipitationMapComponent } from '../components/precipitation-map.component';
import { AppSidebarComponent } from '../../../shared/components/app-sidebar.component';

@Component({
  selector: 'app-dashboard-page', standalone: true,
  imports: [CommonModule, LocationSearchComponent, ForecastSummaryComponent, RainfallChartComponent, ForecastInsightsComponent, PrecipitationMapComponent, AppSidebarComponent],
  templateUrl: './dashboard.page.html',
})
export class DashboardPage {
  private readonly state = inject(ForecastStateService);
  readonly state$ = this.state.state$;
  readonly model$ = this.state.model$;
  readonly location$ = this.state.location$;
  selectLocation(location: Place) { this.state.selectLocation(location); }
  selectModel(model: ForecastModel) { this.state.selectModel(model); }
  refresh() { this.state.refresh(); }
  exportCsv(forecast: ForecastState['forecast']) {
    if (!forecast) return;
    const rows = [['Time (UTC)', 'Rainfall (mm)', 'Intensity'], ...forecast.forecast.map(point => [point.time, String(point.rainfall), point.intensity])];
    const blob = new Blob([rows.map(row => row.join(',')).join('\n')], { type: 'text/csv' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'rainscope-forecast.csv'; link.click(); URL.revokeObjectURL(link.href);
  }
}
