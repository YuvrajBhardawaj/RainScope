import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/dashboard/pages/dashboard.page').then(module => module.DashboardPage) },
  { path: 'map', loadComponent: () => import('./features/map/pages/map.page').then(module => module.MapPage) },
  { path: 'about', loadComponent: () => import('./features/about/pages/about.page').then(module => module.AboutPage) },
  { path: '**', redirectTo: '' },
];
