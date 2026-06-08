import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { catchError, forkJoin, map, of, shareReplay, switchMap, Subscription, BehaviorSubject, combineLatest } from 'rxjs';
import { SessionStore } from '../../../../infra/session/session.store';
import { VehiculosApi } from '../../../../infra/api/vehiculos.api';
import { IncidentesApi } from '../../../../infra/api/incidentes.api';
import { PagosApi } from '../../../../infra/api/pagos.api';
import { KpisApi } from '../../../../infra/api/kpis.api';
import { WebSocketService } from '../../../../infra/realtime/websocket.service';

@Component({
  selector: 'ev-overview-page',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './overview.page.html',
  styleUrl: './overview.page.css',
})
export class OverviewPage implements OnInit, OnDestroy {
  private readonly session = inject(SessionStore);
  private readonly vehiculosApi = inject(VehiculosApi);
  private readonly incidentesApi = inject(IncidentesApi);
  private readonly pagosApi = inject(PagosApi);
  private readonly kpisApi = inject(KpisApi);
  private readonly wsService = inject(WebSocketService);

  private wsSub?: Subscription;
  readonly refreshTrigger$ = new BehaviorSubject<number>(0);

  hasNewAlert = false;
  newAlertMessage = '';

  readonly session$ = this.session.session$;

  sections = {
    stats: true,
    acceso: true,
    incidentes: true,
    estados: true,
  };

  toggleSection(section: string) {
    (this.sections as any)[section] = !(this.sections as any)[section];
  }

  readonly data$ = combineLatest([this.session.session$, this.refreshTrigger$]).pipe(
    switchMap(([s, _]) => {
      const role = s?.role ?? 'anon';

      return forkJoin({
        resumen: this.kpisApi.obtenerResumen().pipe(catchError(() => of(null))),
        vehiculos: this.vehiculosApi.listarMisVehiculos().pipe(catchError(() => of([]))),
        pendientes: this.incidentesApi.listarPendientes().pipe(catchError(() => of([]))),
        activo: this.incidentesApi.obtenerClienteActivo().pipe(catchError(() => of({ id_incidente: null }))),
        pagos: this.pagosApi.listarTodos().pipe(
          catchError(() => of([]))
        ),
        porEstado: this.kpisApi.porEstado().pipe(catchError(() => of([]))),
        incidentesMes: this.kpisApi.incidentesPorMes().pipe(catchError(() => of([]))),
        tecnicos: this.kpisApi.obtenerResumen().pipe(
          map(r => ({ disponibles: r?.tecnicos_disponibles ?? 0, total: r?.tecnicos_total ?? 0 })),
          catchError(() => of({ disponibles: 0, total: 0 }))
        ),
      });
    }),
    shareReplay(1),
  );

  max(items: { total: number }[]): number {
    return Math.max(...items.map((i) => i.total), 1);
  }

  statusColor(estado: string): string {
    const map: Record<string, string> = {
      pendiente: '#f59e0b',
      en_proceso: '#3b82f6',
      buscando_taller: '#8b5cf6',
      taller_asignado: '#06b6d4',
      en_camino: '#10b981',
      en_atencion: '#f97316',
      atendido: '#22c55e',
      finalizado: '#14b8a6',
      cancelado: '#ef4444',
    };
    return map[estado] || '#64748b';
  }

  formatLabel(key: string): string {
    const map: Record<string, string> = {
      pendiente: 'Pendiente',
      en_proceso: 'En Proceso',
      buscando_taller: 'Buscando Taller',
      taller_asignado: 'Taller Asignado',
      en_camino: 'En Camino',
      en_atencion: 'En Atención',
      atendido: 'Atendido',
      finalizado: 'Finalizado',
      cancelado: 'Cancelado',
    };
    return map[key] || key;
  }

  ngOnInit(): void {
    this.wsService.connectGlobal();
    this.wsSub = this.wsService.messages$.subscribe((msg) => {
      if (msg['tipo'] === 'nuevo_incidente') {
        this.hasNewAlert = true;
        this.newAlertMessage = `🚨 Nueva emergencia registrada! Incidente #${msg['id_incidente']}`;
        this.refreshData();
        // Auto-hide alert after 8 seconds
        setTimeout(() => { this.hasNewAlert = false; }, 8000);
      }
    });
  }

  refreshData(): void {
    this.refreshTrigger$.next(this.refreshTrigger$.value + 1);
  }

  ngOnDestroy(): void {
    this.wsSub?.unsubscribe();
    this.wsService.disconnect();
  }
}
