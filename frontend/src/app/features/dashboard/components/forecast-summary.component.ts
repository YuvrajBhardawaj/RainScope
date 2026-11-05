import { Component, Input } from '@angular/core';
import { DecimalPipe, UpperCasePipe } from '@angular/common';
import { Forecast } from '../../../core/models/forecast.model';
import { PeakTimePipe } from '../../../shared/pipes/peak-time.pipe';

@Component({
  selector: 'app-forecast-summary', standalone: true, imports: [DecimalPipe, UpperCasePipe, PeakTimePipe],
  template: `<section class="metrics"><article class="metric total"><div class="metric-label">TOTAL EXPECTED RAINFALL <span>ⓘ</span></div><div class="value">{{forecast.summary.totalRainfall | number:'1.1-1'}}<small>mm</small></div><div class="metric-foot">Next 24 hours <span class="trend">↗</span></div><div class="watermark">∿</div></article><article class="metric"><div class="metric-label">PEAK {{forecast.interval | uppercase}} RAINFALL</div><div class="value">{{forecast.summary.maxRainfall | number:'1.1-1'}}<small>mm</small></div><div class="metric-foot">{{forecast.forecast | peakTime}}</div><div class="rain-symbol">◉</div></article><article class="metric"><div class="metric-label">PRECIPITATION RISK</div><div class="risk-value"><span class="risk-dot" [class.high]="forecast.summary.riskLevel === 'High'"></span>{{forecast.summary.riskLevel}}</div><div class="metric-foot">Based on forecast intensity</div><div class="risk-gauge"><span [style.width.%]="forecast.summary.riskLevel === 'High' ? 86 : forecast.summary.riskLevel === 'Moderate' ? 58 : 24"></span></div></article></section>`,
})
export class ForecastSummaryComponent { @Input({ required: true }) forecast!: Forecast; }
