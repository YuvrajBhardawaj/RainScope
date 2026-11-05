import { Pipe, PipeTransform } from '@angular/core';
import { ForecastPoint } from '../../core/models/forecast.model';

@Pipe({ name: 'peakTime', standalone: true })
export class PeakTimePipe implements PipeTransform {
  transform(points: ForecastPoint[] | undefined): string {
    if (!points?.length) return 'No rainfall expected';
    const peak = points.reduce((a, b) => a.rainfall > b.rainfall ? a : b);
    return `Expected around ${new Date(peak.time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC', hour12: false })} UTC`;
  }
}
