import { Component, Input } from '@angular/core';
import { Forecast } from '../../../core/models/forecast.model';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-forecast-insights', standalone: true, imports: [DecimalPipe],
  template: `<article class="panel insights"><div class="panel-kicker">AT A GLANCE</div><h3>Forecast insights</h3><div class="insight-main"><div class="cloud">☂</div><div><strong>{{forecast.summary.riskLevel}} rainfall risk</strong><p>For {{forecast.location.name}} over the next 24 hours</p></div></div><div class="insight-row"><span>Highest rainfall</span><b>{{forecast.summary.maxRainfall | number:'1.1-1'}} mm</b></div><div class="insight-row"><span>Forecast intervals</span><b>{{forecast.forecast.length}} periods</b></div><div class="insight-row"><span>Data source</span><b>{{forecast.source}}</b></div><div class="source-note"><span>ⓘ</span> {{forecast.mode === 'demo' ? 'Illustrative demo values. No live forecast data is connected yet.' : 'Forecast values are processed by RainScope.'}}</div></article>`,
})
export class ForecastInsightsComponent { @Input({ required: true }) forecast!: Forecast; }
