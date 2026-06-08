import { Component, HostListener, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { SessionStore } from '../../../infra/session/session.store';

interface PackageSection {
  id: string;
  label: string;
  icon: string;
  expanded: boolean;
  links: { path: string; label: string; icon: string }[];
}

@Component({
  selector: 'ev-portal-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './portal.layout.html',
  styleUrl: './portal.layout.css',
})
export class PortalLayout implements OnInit {
  readonly session$ = inject(SessionStore).session$;

  private readonly store = inject(SessionStore);
  private readonly router = inject(Router);

  sidebarOpen = window.innerWidth > 1024;
  isMobile = window.innerWidth <= 1024;

  packages: PackageSection[] = [
    {
      id: 'principal',
      label: 'Principal',
      icon: 'home',
      expanded: true,
      links: [
        { path: '/panel/resumen', label: 'Vista General', icon: 'dashboard' },
        { path: '/panel/analitica', label: 'Analítica y KPIs', icon: 'monitoring' },
        { path: '/panel/perfil', label: 'Mi Perfil', icon: 'person' },
        { path: '/panel/notificaciones', label: 'Notificaciones', icon: 'notifications' },
      ],
    },
    {
      id: 'paquete1',
      label: 'Paquete 1: Gestión',
      icon: 'inventory_2',
      expanded: false,
      links: [
        { path: '/panel/clientes', label: 'Clientes', icon: 'groups' },
        { path: '/panel/talleres', label: 'Talleres', icon: 'handyman' },
        { path: '/panel/usuarios', label: 'Admin Usuarios', icon: 'manage_accounts' },
        { path: '/panel/vehiculos', label: 'Vehículos', icon: 'directions_car' },
      ],
    },
    {
      id: 'paquete2',
      label: 'Paquete 2: Operaciones',
      icon: 'settings',
      expanded: false,
      links: [
        { path: '/panel/tecnicos', label: 'Staff Técnico', icon: 'engineering' },
        { path: '/panel/ubicacion', label: 'Radar de Asistencia', icon: 'radar' },
        { path: '/panel/incidentes', label: 'Emergencias Entrantes', icon: 'emergency' },
        { path: '/panel/cotizaciones', label: 'Cotizaciones', icon: 'request_quote' },
      ],
    },
    {
      id: 'paquete5',
      label: 'Paquete 5: Finanzas',
      icon: 'account_balance',
      expanded: false,
      links: [
        { path: '/panel/comisiones', label: 'Comisiones', icon: 'bar_chart' },
        { path: '/panel/ingresos', label: 'Mis Ingresos', icon: 'account_balance_wallet' },
        { path: '/panel/pagos', label: 'Pagos Generales', icon: 'payments' },
      ],
    },
    {
      id: 'mi-trabajo',
      label: 'Mi Trabajo',
      icon: 'work',
      expanded: false,
      links: [
        { path: '/panel/historial', label: 'Historial de Auxilios', icon: 'history' },
        { path: '/panel/mi-taller', label: 'Mi Taller', icon: 'storefront' },
      ],
    },
  ];

  ngOnInit() {
    // Auto-expand only the package that matches current route
    this.packages.forEach(pkg => {
      pkg.expanded = this.isPackageActive(pkg.id);
    });
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

  togglePackage(id: string) {
    this.packages.forEach(pkg => {
      if (pkg.id === id) {
        pkg.expanded = !pkg.expanded;
      } else {
        pkg.expanded = false; // Close all other packages
      }
    });
  }

  isPackageActive(id: string): boolean {
    const pkg = this.packages.find((p) => p.id === id);
    if (!pkg) return false;
    const currentUrl = this.router.url;
    return pkg.links.some((l) => currentUrl.startsWith(l.path));
  }

  logout(): void {
    this.store.clear();
    this.router.navigateByUrl('/acceso');
  }

  getUserInitial(name: string): string {
    return name?.charAt(0)?.toUpperCase() || 'U';
  }
}
