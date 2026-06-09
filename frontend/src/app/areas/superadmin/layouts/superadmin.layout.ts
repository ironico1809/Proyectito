import { Component, HostListener, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { SessionStore } from '../../../infra/session/session.store';

@Component({
  selector: 'ev-superadmin-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './superadmin.layout.html',
  styleUrl: './superadmin.layout.css',
})
export class SuperadminLayout implements OnInit {
  readonly session$ = inject(SessionStore).session$;

  private readonly store = inject(SessionStore);
  private readonly router = inject(Router);

  sidebarOpen = window.innerWidth > 1024;
  isMobile = window.innerWidth <= 1024;

  ngOnInit() {
    // Check if the user is indeed a superadmin, otherwise redirect
    const snapshot = this.store.snapshot();
    if (snapshot?.role !== 'superadmin') {
      this.router.navigateByUrl('/acceso');
    }
  }

  @HostListener('window:resize')
  onResize() {
    this.isMobile = window.innerWidth <= 1024;
    if (this.isMobile) this.sidebarOpen = false;
    else this.sidebarOpen = true;
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  closeSidebar() {
    if (this.isMobile) this.sidebarOpen = false;
  }

  logout(): void {
    this.store.clear();
    this.router.navigateByUrl('/acceso');
  }

  getUserInitial(name: string): string {
    return name?.charAt(0)?.toUpperCase() || 'S';
  }
}
