export type ForecastModel = 'ifs' | 'aifs';
export interface Place { name: string; region: string; lat: number; lon: number }
export interface GeocodingResult { id: number; name: string; latitude: number; longitude: number; country: string; country_code: string; admin1: string; feature_code: string }
export interface LocationSearchState { results: GeocodingResult[]; loading: boolean; error: string | null }
export interface ForecastPoint { time: string; rainfall: number; intensity: string }
export interface Forecast {
  location: { name: string; region: string; latitude: number; longitude: number };
  model: string;
  source: string;
  mode: 'live' | 'demo';
  runTime: string;
  unit: string;
  interval: string;
  forecast: ForecastPoint[];
  summary: { totalRainfall: number; maxRainfall: number; riskLevel: string };
}
export interface ForecastState { forecast: Forecast | null; loading: boolean; error: string | null }
export interface ForecastGrid { model: string; mode: 'live' | 'demo'; unit: string; cells: { lat: number; lon: number; rainfall: number }[] }
