import { Component, HostListener, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { SessionStore } from '../../../infra/session/session.store';
import { IncidentesApi } from '../../../infra/api/incidentes.api';
import { WebSocketService } from '../../../infra/realtime/websocket.service';
import { Subscription } from 'rxjs';

interface LinkItem {
  path: string;
  label: string;
  icon: string;
}

interface PackageSection {
  id: string;
  label: string;
  icon: string;
  expanded: boolean;
  links: LinkItem[];
}

@Component({
  selector: 'ev-portal-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './portal.layout.html',
  styleUrl: './portal.layout.css',
})
export class PortalLayout implements OnInit, OnDestroy {
  readonly session$ = inject(SessionStore).session$;

  private readonly store = inject(SessionStore);
  private readonly router = inject(Router);
  private readonly incidentesApi = inject(IncidentesApi);
  private readonly wsService = inject(WebSocketService);
  private sub?: Subscription;
  private wsSub?: Subscription;

  sidebarOpen = window.innerWidth > 1024;
  isMobile = window.innerWidth <= 1024;

  activeMissionId: number | null = null;

  packages: PackageSection[] = [
    {
      id: 'operacion',
      label: 'Operación',
      icon: 'electric_car',
      expanded: true,
      links: [],
    },
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

  filteredPackages: PackageSection[] = [];

  ngOnInit() {
    this.sub = this.session$.subscribe(session => {
      const role = session?.role || '';
      this.rebuildMenu(role);
    });
  }

  private rebuildMenu(role: string) {
    this.filteredPackages = this.packages.map(pkg => {
      let links = [...pkg.links];

      // Add static active mission link for technicians
      if (pkg.id === 'operacion' && role === 'tecnico') {
        links = [
          { path: `/panel/mision`, label: 'Misión Activa', icon: 'my_location' },
          ...links
        ];
      }

      const filteredLinks = links.filter(link => {
        let allowedRoles: string[] = [];
        
        if (link.path.startsWith('/panel/mision')) allowedRoles = ['tecnico'];
        else if (link.path === '/panel/resumen') allowedRoles = ['admin', 'taller', 'tecnico'];
          else if (link.path === '/panel/analitica') allowedRoles = ['admin'];
          else if (link.path === '/panel/perfil') allowedRoles = ['admin', 'taller', 'tecnico'];
          else if (link.path === '/panel/notificaciones') allowedRoles = ['admin', 'taller', 'tecnico'];
          
          else if (link.path === '/panel/clientes') allowedRoles = ['admin'];
          else if (link.path === '/panel/talleres') allowedRoles = ['admin'];
          else if (link.path === '/panel/usuarios') allowedRoles = ['admin'];
          else if (link.path === '/panel/vehiculos') allowedRoles = ['admin'];
          
          else if (link.path === '/panel/tecnicos') allowedRoles = ['admin', 'taller'];
          else if (link.path === '/panel/ubicacion') allowedRoles = ['admin', 'taller'];
          else if (link.path === '/panel/incidentes') allowedRoles = ['admin', 'taller', 'tecnico'];
          else if (link.path === '/panel/cotizaciones') allowedRoles = ['admin', 'taller'];
          
          else if (link.path === '/panel/comisiones') allowedRoles = ['admin'];
          else if (link.path === '/panel/ingresos') allowedRoles = ['taller'];
          else if (link.path === '/panel/pagos') allowedRoles = ['admin'];
          
          else if (link.path === '/panel/historial') allowedRoles = ['admin', 'taller', 'tecnico'];
          else if (link.path === '/panel/mi-taller') allowedRoles = ['taller'];
          
          return allowedRoles.includes(role);
        });

        return {
          ...pkg,
          links: filteredLinks
        };
      }).filter(pkg => pkg.links.length > 0);

      this.filteredPackages.forEach(pkg => {
        pkg.expanded = this.isPackageActive(pkg.id);
      });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
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
    this.filteredPackages.forEach(pkg => {
      if (pkg.id === id) {
        pkg.expanded = !pkg.expanded;
      } else {
        pkg.expanded = false;
      }
    });
  }

  isPackageActive(id: string): boolean {
    const pkg = this.filteredPackages.find((p) => p.id === id);
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

