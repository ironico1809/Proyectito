import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { BehaviorSubject, catchError, map, of, Subscription, switchMap } from 'rxjs';
import { IncidentesApi, MonitoreoOut } from '../../../../infra/api/incidentes.api';
import { CotizacionesApi, CotizacionOut } from '../../../../infra/api/cotizaciones.api';
import { TecnicosApi, TecnicoOut } from '../../../../infra/api/tecnicos.api';
import { TalleresApi } from '../../../../infra/api/talleres.api';
import { WebSocketService } from '../../../../infra/realtime/websocket.service';
import { BitacoraApi, BitacoraItem } from '../../../../infra/api/bitacora.api';
import { SessionStore } from '../../../../infra/session/session.store';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'ev-incident-detail-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './incident-detail.page.html',
  styleUrl: './incident-detail.page.css',
})
export class IncidentDetailPage implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly incidentesApi = inject(IncidentesApi);
  private readonly cotizacionesApi = inject(CotizacionesApi);
  private readonly tecnicosApi = inject(TecnicosApi);
  private readonly talleresApi = inject(TalleresApi);
  private readonly wsService = inject(WebSocketService);
  private readonly sessionStore = inject(SessionStore);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly bitacoraApi = inject(BitacoraApi);

  userRole = this.sessionStore.snapshot()?.role || '';
  mapaUrlSegura: SafeResourceUrl | null = null;
  private wsSub?: Subscription;
  private currentIncidenteId?: number;
  wsConnected = false;
  currentEstado = '';
  bitacora: BitacoraItem[] = [];

  readonly incidenteId$ = this.route.paramMap.pipe(map((p) => Number(p.get('id'))));

  private readonly monitoreoRefresh$ = new BehaviorSubject<number>(0);

  readonly monitoreo$ = this.incidenteId$.pipe(
    switchMap((id) => {
      this.currentIncidenteId = id;
      return this.monitoreoRefresh$.pipe(
        switchMap(() => this.incidentesApi.monitoreo(id).pipe(catchError(() => of(null)))),
      );
    }),
  );

  readonly tecnicos$ = this.talleresApi.obtenerMiTaller().pipe(
    switchMap((taller) =>
      this.tecnicosApi.listarPorTaller(taller.id_taller).pipe(catchError(() => of([] as TecnicoOut[])))),
    catchError(() => of([] as TecnicoOut[])),
  );

  cotizaciones: CotizacionOut[] = [];

  ngOnInit(): void {
    this.incidenteId$.subscribe((id) => {
      if (id) {
        this.currentIncidenteId = id;
        this.wsService.connectIncidente(id);
        this.wsConnected = true;
        this.cargarCotizaciones(id);
        this.cargarBitacora(id);
      }
    });

    this.wsSub = this.wsService.messages$.subscribe((msg) => {
      if (msg['tipo'] === 'nueva_cotizacion') {
        if (this.currentIncidenteId) {
          this.cargarCotizaciones(this.currentIncidenteId);
          this.cargarBitacora(this.currentIncidenteId);
        }
      } else if (msg['tipo'] === 'cambio_estado') {
        this.currentEstado = msg['estado'];
        this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
      } else if (msg['tipo'] === 'cotizacion_aceptada') {
        if (this.currentIncidenteId) {
          this.cargarCotizaciones(this.currentIncidenteId);
          this.cargarBitacora(this.currentIncidenteId);
          this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
        }
      }
    });

    this.monitoreo$.subscribe((m) => {
      if (m && m.latitud_emergencia && m.longitud_emergencia) {
        const urlBruta = `https://maps.google.com/maps?q=${m.latitud_emergencia},${m.longitud_emergencia}&z=15&output=embed`;
        this.mapaUrlSegura = this.sanitizer.bypassSecurityTrustResourceUrl(urlBruta);
      }
    });
  }

  cargarCotizaciones(incidenteId: number) {
    this.cotizacionesApi.listarPorIncidente(incidenteId).subscribe((data) => {
      this.cotizaciones = data;
    });
  }

  showQuotationForm = false;
  quotationForm = { precio_estimado: 0, tiempo_estimado_min: 60, descripcion: '' };
  tallerId = 0;

  openQuotationForm(tallerId: number) {
    this.tallerId = tallerId;
    this.showQuotationForm = true;
    this.quotationForm = { precio_estimado: 0, tiempo_estimado_min: 60, descripcion: '' };
  }

  closeQuotationForm() {
    this.showQuotationForm = false;
  }

  createQuotation(incidenteId: number) {
    if (!this.quotationForm.precio_estimado || !this.quotationForm.descripcion) return;
    this.cotizacionesApi.crear({
      incidente_id: incidenteId,
      precio_estimado: this.quotationForm.precio_estimado,
      tiempo_estimado_min: this.quotationForm.tiempo_estimado_min,
      descripcion: this.quotationForm.descripcion,
    }).subscribe(() => {
      this.showQuotationForm = false;
      this.cargarCotizaciones(incidenteId);
      this.cargarBitacora(incidenteId);
    });
  }

  aceptarCotizacion(id: number, incidenteId: number) {
    this.cotizacionesApi.aceptar(id).subscribe(() => {
      this.cargarCotizaciones(incidenteId);
    });
  }

  rechazarCotizacion(id: number, incidenteId: number) {
    this.cotizacionesApi.rechazar(id).subscribe(() => {
      this.cargarCotizaciones(incidenteId);
    });
  }

  responderIncidente(id: number, accion: string) {
    this.incidentesApi.responderAccion(id, accion).subscribe(() => {
      this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
    });
  }

  asignarTecnico(id: number, event: Event) {
    const select = event.target as HTMLSelectElement;
    const tecnicoId = Number(select.value);
    if (!tecnicoId) return;
    this.incidentesApi.asignarTecnico(id, tecnicoId).subscribe(() => {
      this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
    });
  }

  actualizarEstado(id: number, event: Event) {
    const select = event.target as HTMLSelectElement;
    const estado = select.value;
    if (!estado) return;

    let comentario: string | null = null;
    let costo_final: number | null = null;

    if (estado === 'finalizado') {
      const costStr = prompt('Ingrese el costo final del servicio (Bs.):', '100');
      if (costStr === null) {
        select.value = ''; // Cancelado
        return;
      }
      costo_final = parseFloat(costStr) || 0;
      comentario = prompt('Ingrese un comentario final (opcional):', 'Servicio completado exitosamente.');
    } else {
      comentario = prompt('Ingrese un comentario sobre el cambio de estado (opcional):');
    }

    this.incidentesApi.actualizarEstado(id, estado, comentario || undefined, costo_final || undefined).subscribe(() => {
      this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
      this.cargarBitacora(id);
    });
  }

  showExceptionForm = false;
  exceptionForm = { tipo_excepcion: 'cancelacion_cliente', motivo: '' };

  openExceptionForm() { this.showExceptionForm = true; }
  closeExceptionForm() { this.showExceptionForm = false; }

  reportarExcepcion(id: number) {
    if (!this.exceptionForm.motivo) return;
    this.incidentesApi.excepcion(id, {
      tipo_excepcion: this.exceptionForm.tipo_excepcion,
      motivo: this.exceptionForm.motivo,
    }).subscribe(() => {
      this.showExceptionForm = false;
      this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
      this.cargarBitacora(id);
    });
  }

  getEstadoColor(e: string): string {
    const map: Record<string, string> = {
      pendiente: 'var(--amber-500)',
      aceptada: 'var(--success)',
      rechazada: 'var(--danger)',
      expirada: 'var(--text-muted)',
    };
    return map[e] || 'var(--text-muted)';
  }

  getEstadoLabel(e: string): string {
    const map: Record<string, string> = {
      pendiente: 'Pendiente',
      en_proceso: 'En Proceso',
      finalizado: 'Finalizado',
      cancelado: 'Cancelado',
      en_camino: 'En Camino',
      en_atencion: 'En Atención',
      taller_asignado: 'Taller Asignado',
      buscando_taller: 'Buscando Taller',
      atendido: 'Atendido',
    };
    return map[e] || e;
  }

  getEstadoStyle(e: string): any {
    const colors: Record<string, { bg: string, text: string }> = {
      pendiente: { bg: 'color-mix(in srgb, var(--amber-500) 12%, transparent)', text: 'var(--amber-500)' },
      en_proceso: { bg: 'color-mix(in srgb, #3b82f6 12%, transparent)', text: '#3b82f6' },
      en_camino: { bg: 'color-mix(in srgb, #3b82f6 12%, transparent)', text: '#3b82f6' },
      en_atencion: { bg: 'color-mix(in srgb, #3b82f6 12%, transparent)', text: '#3b82f6' },
      finalizado: { bg: 'color-mix(in srgb, var(--success) 12%, transparent)', text: 'var(--success)' },
      atendido: { bg: 'color-mix(in srgb, var(--success) 12%, transparent)', text: 'var(--success)' },
      cancelado: { bg: 'color-mix(in srgb, var(--danger) 12%, transparent)', text: 'var(--danger)' },
      taller_asignado: { bg: 'color-mix(in srgb, #f97316 12%, transparent)', text: '#f97316' },
      buscando_taller: { bg: 'color-mix(in srgb, #f97316 12%, transparent)', text: '#f97316' },
    };
    const c = colors[e] || { bg: 'var(--slate-800)', text: 'var(--text-muted)' };
    return {
      background: c.bg,
      color: c.text,
      padding: '4px 12px',
      'border-radius': '100px',
      'font-size': '0.75rem',
      'font-weight': '700',
      'text-transform': 'uppercase',
      'display': 'inline-block'
    };
  }

    cargarBitacora(incidentId: number) {
    this.bitacoraApi.obtenerBitacora(incidentId).subscribe((data) => {
      this.bitacora = data;
    });
  }

  ngOnDestroy(): void {
    this.wsSub?.unsubscribe();
    this.wsService.disconnect();
  }
}
