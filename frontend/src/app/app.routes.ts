import { Routes } from '@angular/router';

import { portalGuard } from './infra/http/portal.guard';
import { guestOnlyGuard } from './infra/http/guest.guard';
import { superadminGuard } from './infra/http/superadmin.guard';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () =>
      import('./areas/access/pages/landing/landing.page').then((m) => m.LandingPage),
  },

  {
    path: 'acceso',
    canActivate: [guestOnlyGuard],
    loadComponent: () =>
      import('./areas/access/pages/login/login.page').then((m) => m.LoginPage),
  },

  {
    path: 'panel',
    canActivate: [portalGuard],
    canActivateChild: [portalGuard],
    loadComponent: () =>
      import('./areas/portal/layouts/portal.layout').then(
        (m) => m.PortalLayout,
      ),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'resumen' },
      {
        path: 'resumen',
        data: { roles: ['admin', 'taller', 'tecnico'] },
        loadComponent: () =>
          import('./areas/portal/pages/overview/overview.page').then(
            (m) => m.OverviewPage,
          ),
      },
      {
        path: 'vehiculos',
        data: { roles: ['admin'] },
        loadComponent: () =>
          import('./areas/portal/pages/vehicles/vehicles.page').then(
            (m) => m.VehiclesPage,
          ),
      },
      {
        path: 'incidentes',
        data: { roles: ['admin', 'taller', 'tecnico'] },
        loadComponent: () =>
          import('./areas/portal/pages/incidents/incidents.page').then(
            (m) => m.IncidentsPage,
          ),
      },
      {
        path: 'pagos',
        data: { roles: ['admin'] },
        loadComponent: () =>
          import('./areas/portal/pages/payments/payments.page').then(
            (m) => m.PaymentsPage,
          ),
      },
      {
        path: 'perfil',
        data: { roles: ['admin', 'taller', 'tecnico'] },
        loadComponent: () =>
          import('./areas/portal/pages/profile/profile.page').then(
            (m) => m.ProfilePage,
          ),
      },
      {
        path: 'clientes',
        data: { roles: ['admin'] },
        loadComponent: () =>
          import('./areas/portal/pages/clients/clients.page').then(
            (m) => m.ClientsPage,
          ),
      },
      {
        path: 'talleres',
        data: { roles: ['admin'] },
        loadComponent: () =>
          import('./areas/portal/pages/workshops/workshops.page').then(
            (m) => m.WorkshopsPage,
          ),
      },
      {
        path: 'tecnicos',
        data: { roles: ['admin', 'taller'] },
        loadComponent: () =>
          import('./areas/portal/pages/technicians/technicians.page').then(
            (m) => m.TechniciansPage,
          ),
      },
      {
        path: 'cotizaciones',
        data: { roles: ['admin', 'taller'] },
        loadComponent: () =>
          import('./areas/portal/pages/quotations/quotations.page').then(
            (m) => m.QuotationsPage,
          ),
      },
      {
        path: 'notificaciones',
        data: { roles: ['admin', 'taller', 'tecnico'] },
        loadComponent: () =>
          import('./areas/portal/pages/notifications/notifications.page').then(
            (m) => m.NotificationsPage,
          ),
      },
      {
        path: 'mi-taller',
        data: { roles: ['taller'] },
        loadComponent: () =>
          import('./areas/portal/pages/my-workshop/my-workshop.page').then(
            (m) => m.MyWorkshopPage,
          ),
      },
      {
        path: 'usuarios',
        data: { roles: ['admin'] },
        loadComponent: () =>
          import('./areas/portal/pages/users-management/users-management.page').then(
            (m) => m.UsersManagementPage,
          ),
      },
      {
        path: 'incidentes/:id',
        data: { roles: ['admin', 'taller', 'tecnico'] },
        loadComponent: () =>
          import('./areas/portal/pages/incident-detail/incident-detail.page').then(
            (m) => m.IncidentDetailPage,
          ),
      },
      {
        path: 'mision',
        data: { roles: ['tecnico'] },
        loadComponent: () =>
          import('./areas/portal/pages/mission/mission.page').then(
            (m) => m.MissionPage,
          ),
      },
      {
        path: 'mision/:id',
        data: { roles: ['tecnico'] },
        loadComponent: () =>
          import('./areas/portal/pages/mission/mission.page').then(
            (m) => m.MissionPage,
          ),
      },
      {
        path: 'ubicacion',
        data: { roles: ['admin', 'taller'] },
        loadComponent: () =>
          import('./areas/portal/pages/location/location.page').then(
            (m) => m.LocationPage,
          ),
      },
      {
        path: 'historial',
        data: { roles: ['admin', 'taller', 'tecnico'] },
        loadComponent: () =>
          import('./areas/portal/pages/history/history.page').then(
            (m) => m.HistoryPage,
          ),
      },
      {
        path: 'comisiones',
        data: { roles: ['admin'] },
        loadComponent: () =>
          import('./areas/portal/pages/commissions/commissions.page').then(
            (m) => m.CommissionsPage,
          ),
      },
      {
        path: 'ingresos',
        data: { roles: ['taller'] },
        loadComponent: () =>
          import('./areas/portal/pages/income/income.page').then(
            (m) => m.IncomePage,
          ),
      },
      {
        path: 'analitica',
        data: { roles: ['admin'] },
        loadComponent: () =>
          import('./areas/portal/pages/kpis/kpis.page').then(
            (m) => m.KpisPage,
          ),
      },
      {
        path: 'monitoreo',
        redirectTo: 'incidentes',
        pathMatch: 'full'
      }
    ],
  },

  {
    path: 'superadmin',
    canActivate: [superadminGuard],
    canActivateChild: [superadminGuard],
    loadComponent: () =>
      import('./areas/superadmin/layouts/superadmin.layout').then(
        (m) => m.SuperadminLayout,
      ),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./areas/superadmin/pages/dashboard/superadmin-dashboard.page').then(
            (m) => m.SuperadminDashboardPage,
          ),
      },
      {
        path: 'tenants',
        loadComponent: () =>
          import('./areas/superadmin/pages/tenants/superadmin-tenants.page').then(
            (m) => m.SuperadminTenantsPage,
          ),
      },
    ],
  },

  { path: '**', redirectTo: 'panel' },
];
