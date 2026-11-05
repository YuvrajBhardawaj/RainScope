import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Forecast } from '../../../core/models/forecast.model';

@Component({
  selector: 'app-rainfall-chart', standalone: true, imports: [CommonModule],
  template: `<article class="panel chart-panel"><div class="panel-head"><div><div class="panel-kicker">PRECIPITATION OUTLOOK</div><h3>Rainfall forecast</h3></div><div class="units">mm <span>·</span> {{forecast.interval}} intervals <span class="dots">•••</span></div></div><div class="chart"><div class="y-labels"><span>20</span><span>15</span><span>10</span><span>5</span><span>0</span></div><div class="plot"><div class="gridline" *ngFor="let line of [0,1,2,3,4]"></div><div class="bar-area"><div class="bar-item" *ngFor="let point of forecast.forecast"><div class="bar-tip">{{point.rainfall | number:'1.1-1'}} mm · {{point.intensity}}</div><div class="bar" [class.heavy]="point.intensity === 'Heavy' || point.intensity === 'Very heavy'" [style.height]="barHeight(point.rainfall)"></div><span>{{point.time | date:'HH:mm':'UTC'}}</span></div></div></div></div><div class="chart-legend"><span class="legend-swatch"></span> Expected rainfall <span class="legend-note">Times shown in UTC</span></div></article>`,
})
export class RainfallChartComponent {
  @Input({ required: true }) forecast!: Forecast;
  barHeight(mm: number) { return `${Math.max(5, Math.min(100, mm / 20 * 100))}%`; }
}
