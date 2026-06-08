import { Routes } from '@angular/router';

import { authGuard } from './infra/http/auth.guard';
import { guestOnlyGuard } from './infra/http/guest.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'panel' },

  {
    path: 'acceso',
    canActivate: [guestOnlyGuard],
    loadComponent: () =>
      import('./areas/access/pages/login/login.page').then((m) => m.LoginPage),
  },

  {
    path: 'panel',
    canActivate: [authGuard],
    canActivateChild: [authGuard],
    loadComponent: () =>
      import('./areas/portal/layouts/portal.layout').then(
        (m) => m.PortalLayout,
      ),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'resumen' },
      {
        path: 'resumen',
        loadComponent: () =>
          import('./areas/portal/pages/overview/overview.page').then(
            (m) => m.OverviewPage,
          ),
      },
      {
        path: 'vehiculos',
        loadComponent: () =>
          import('./areas/portal/pages/vehicles/vehicles.page').then(
            (m) => m.VehiclesPage,
          ),
      },
      {
        path: 'incidentes',
        loadComponent: () =>
          import('./areas/portal/pages/incidents/incidents.page').then(
            (m) => m.IncidentsPage,
          ),
      },
      {
        path: 'pagos',
        loadComponent: () =>
          import('./areas/portal/pages/payments/payments.page').then(
            (m) => m.PaymentsPage,
          ),
      },
      {
        path: 'perfil',
        loadComponent: () =>
          import('./areas/portal/pages/profile/profile.page').then(
            (m) => m.ProfilePage,
          ),
      },
      {
        path: 'clientes',
        loadComponent: () =>
          import('./areas/portal/pages/clients/clients.page').then(
            (m) => m.ClientsPage,
          ),
      },
      {
        path: 'talleres',
        loadComponent: () =>
          import('./areas/portal/pages/workshops/workshops.page').then(
            (m) => m.WorkshopsPage,
          ),
      },
      {
        path: 'tecnicos',
        loadComponent: () =>
          import('./areas/portal/pages/technicians/technicians.page').then(
            (m) => m.TechniciansPage,
          ),
      },
      {
        path: 'cotizaciones',
        loadComponent: () =>
          import('./areas/portal/pages/quotations/quotations.page').then(
            (m) => m.QuotationsPage,
          ),
      },
      {
        path: 'notificaciones',
        loadComponent: () =>
          import('./areas/portal/pages/notifications/notifications.page').then(
            (m) => m.NotificationsPage,
          ),
      },
      {
        path: 'mi-taller',
        loadComponent: () =>
          import('./areas/portal/pages/my-workshop/my-workshop.page').then(
            (m) => m.MyWorkshopPage,
          ),
      },
      {
        path: 'usuarios',
        loadComponent: () =>
          import('./areas/portal/pages/users-management/users-management.page').then(
            (m) => m.UsersManagementPage,
          ),
      },
      {
        path: 'incidentes/:id',
        loadComponent: () =>
          import('./areas/portal/pages/incident-detail/incident-detail.page').then(
            (m) => m.IncidentDetailPage,
          ),
      },
      {
        path: 'ubicacion',
        loadComponent: () =>
          import('./areas/portal/pages/location/location.page').then(
            (m) => m.LocationPage,
          ),
      },
      {
        path: 'historial',
        loadComponent: () =>
          import('./areas/portal/pages/history/history.page').then(
            (m) => m.HistoryPage,
          ),
      },
      {
        path: 'comisiones',
        loadComponent: () =>
          import('./areas/portal/pages/commissions/commissions.page').then(
            (m) => m.CommissionsPage,
          ),
      },
      {
        path: 'ingresos',
        loadComponent: () =>
          import('./areas/portal/pages/income/income.page').then(
            (m) => m.IncomePage,
          ),
      },
      {
        path: 'analitica',
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

  { path: '**', redirectTo: 'panel' },
];
