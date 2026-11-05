import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-sidebar', standalone: true, imports: [RouterLink, RouterLinkActive],
  template: `<aside class="rail">
    <a class="brand-mark" routerLink="/" aria-label="RainScope overview"><span class="brand-glyph">R<span>.</span></span><span class="brand-copy">RainScope<small>PRECIPITATION INTELLIGENCE</small></span></a>
    <div class="nav-caption">WORKSPACE</div>
    <nav class="rail-nav" aria-label="Main navigation">
      <a class="rail-icon" routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{exact:true}" [ariaCurrentWhenActive]="'page'"><span class="nav-symbol">◉</span><span class="nav-label">Overview</span><span class="nav-chevron">›</span></a>
      <a class="rail-icon" routerLink="/map" routerLinkActive="active" [ariaCurrentWhenActive]="'page'"><span class="nav-symbol">⌖</span><span class="nav-label">Precipitation map</span><span class="nav-chevron">›</span></a>
      <a class="rail-icon" routerLink="/about" routerLinkActive="active" [ariaCurrentWhenActive]="'page'"><span class="nav-symbol">ⓘ</span><span class="nav-label">About RainScope</span><span class="nav-chevron">›</span></a>
    </nav>
    <div class="sidebar-bottom"><span class="sidebar-signal"></span><span>ECMWF forecast workspace</span></div>
  </aside>`,
  styleUrl: './app-sidebar.component.css',
})
export class AppSidebarComponent {}
