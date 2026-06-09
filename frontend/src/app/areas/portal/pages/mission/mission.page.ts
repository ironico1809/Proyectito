import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule, Router } from '@angular/router';
import { BehaviorSubject, catchError, map, of, Subscription, switchMap } from 'rxjs';
import { IncidentesApi, MonitoreoOut } from '../../../../infra/api/incidentes.api';
import { CotizacionesApi, CotizacionOut } from '../../../../infra/api/cotizaciones.api';
import { WebSocketService } from '../../../../infra/realtime/websocket.service';
import { SessionStore } from '../../../../infra/session/session.store';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { NotificationService } from '../../../../infra/services/notification.service';

@Component({
  selector: 'ev-mission-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './mission.page.html',
  styleUrl: './mission.page.css',
})
export class MissionPage implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly incidentesApi = inject(IncidentesApi);
  private readonly cotizacionesApi = inject(CotizacionesApi);
  private readonly wsService = inject(WebSocketService);
  private readonly sessionStore = inject(SessionStore);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly notifications = inject(NotificationService);

  userRole = this.sessionStore.snapshot()?.role || '';
  mapaUrlSegura: SafeResourceUrl | null = null;
  private wsSub?: Subscription;
  private currentIncidenteId?: number;
  
  isBusy = false;
  trackingActive = false;
  private watchId?: number;

  readonly incidenteId$ = this.route.paramMap.pipe(
    switchMap((p) => {
      const id = p.get('id');
      if (id) {
        return of(Number(id));
      }
      return this.incidentesApi.obtenerTecnicoActivo().pipe(
        map((res) => res.id_incidente)
      );
    })
  );

  private readonly monitoreoRefresh$ = new BehaviorSubject<number>(0);

  readonly monitoreo$ = this.incidenteId$.pipe(
    switchMap((id) => {
      if (!id) return of(null);
      this.currentIncidenteId = id;
      return this.monitoreoRefresh$.pipe(
        switchMap(() => this.incidentesApi.monitoreo(id).pipe(catchError(() => of(null)))),
      );
    }),
  );

  cotizacionAceptada: CotizacionOut | null = null;
  cotizacionesPendientes: CotizacionOut[] = [];

  showExceptionForm = false;
  exceptionForm = { tipo_excepcion: 'cancelacion_tecnico', motivo: '' };

  showQuotationForm = false;
  quotationForm = { precio_estimado: 0, tiempo_estimado_min: 30, descripcion: '' };

  ngOnInit(): void {
    if (this.userRole !== 'tecnico' && this.userRole !== 'admin') {
      this.router.navigateByUrl('/panel/resumen');
      return;
    }

    this.incidenteId$.subscribe((id) => {
      if (id) {
        this.currentIncidenteId = id;
        this.wsService.connectIncidente(id);
        this.cargarCotizaciones(id);
      }
    });

    this.wsSub = this.wsService.messages$.subscribe((msg) => {
      if (msg['tipo'] === 'cambio_estado' || msg['tipo'] === 'cotizacion_aceptada') {
        this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
        if (msg['tipo'] === 'cotizacion_aceptada' && this.currentIncidenteId) {
          this.cargarCotizaciones(this.currentIncidenteId);
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
      this.cotizacionAceptada = data.find(c => c.estado === 'aceptada') || null;
    });
  }

  updateStatus(id: number, nuevoEstado: string) {
    let costo_final: number | undefined;
    let comentario: string | undefined;

    if (nuevoEstado === 'finalizado') {
      const suggest = this.cotizacionAceptada?.precio_estimado || 100;
      const costStr = prompt('Confirmar costo final del servicio (Bs.):', suggest.toString());
      if (costStr === null) return;
      costo_final = parseFloat(costStr) || 0;
      comentario = 'Servicio finalizado por el técnico.';
    }

    this.isBusy = true;
    this.incidentesApi.actualizarEstado(id, nuevoEstado, comentario, costo_final)
      .subscribe({
        next: () => {
          this.isBusy = false;
          this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
          if (nuevoEstado === 'finalizado') {
            this.stopTracking();
            // Notificar al layout para refrescar el menú (podemos usar un evento simple o recargar)
            window.location.reload(); 
          }
        },
        error: () => this.isBusy = false
      });
  }

  toggleTracking(id: number) {
    if (this.trackingActive) {
      this.stopTracking();
    } else {
      this.startTracking(id);
    }
  }

  private startTracking(id: number) {
    if (!('geolocation' in navigator)) {
      alert('Geolocalización no soportada en este navegador.');
      return;
    }

    this.trackingActive = true;
    this.watchId = window.navigator.geolocation.watchPosition(
      (pos) => {
        this.incidentesApi.actualizarUbicacionTecnico(id, pos.coords.latitude, pos.coords.longitude).subscribe();
      },
      (err) => {
        console.error('Error tracking:', err);
        this.stopTracking();
      },
      { enableHighAccuracy: true }
    );
  }

  private stopTracking() {
    if (this.watchId !== undefined) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = undefined;
    }
    this.trackingActive = false;
  }

  abrirNavegacion(lat: string, lng: string) {
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
  }

  // ---- Excepciones ----
  openExceptionForm() {
    this.showExceptionForm = true;
    this.exceptionForm.motivo = '';
  }

  closeExceptionForm() {
    this.showExceptionForm = false;
  }

  reportarExcepcion(id: number) {
    if (!this.exceptionForm.motivo) {
      alert('Debes ingresar un motivo para cancelar la misión.');
      return;
    }
    this.isBusy = true;
    const payload = {
      tipo_excepcion: this.exceptionForm.tipo_excepcion,
      motivo: this.exceptionForm.motivo,
      compensacion_taller: 0.0,
    };
    this.incidentesApi.excepcion(id, payload).subscribe({
      next: () => {
        this.isBusy = false;
        this.closeExceptionForm();
        this.monitoreoRefresh$.next(this.monitoreoRefresh$.value + 1);
        window.location.reload();
      },
      error: () => (this.isBusy = false),
    });
  }

  // ---- Cotizaciones ----
  openQuotationForm() {
    this.showQuotationForm = true;
    this.quotationForm = { precio_estimado: 0, tiempo_estimado_min: 30, descripcion: '' };
  }

  closeQuotationForm() {
    this.showQuotationForm = false;
  }

  suggestAIQuotation(clasificacion_ia: string | undefined | null) {
    let price = 50;
    let desc = 'Servicio general propuesto por IA.';
    if (clasificacion_ia) {
      const lower = clasificacion_ia.toLowerCase();
      if (lower.includes('llanta') || lower.includes('pinchazo')) {
        price = 40;
        desc = 'Gomería express. Solución de llanta en el lugar.';
      } else if (lower.includes('bateria')) {
        price = 50;
        desc = 'Servicio estándar de batería.';
      } else if (lower.includes('motor') || lower.includes('choque')) {
        price = 100;
        desc = 'Evaluación técnica inicial (Motor/Choque).';
      }
    }
    this.quotationForm.precio_estimado = price;
    this.quotationForm.descripcion = desc;
  }

  createQuotation(id_incidente: number) {
    if (!this.quotationForm.precio_estimado || !this.quotationForm.descripcion) {
      alert('Por favor completa el precio y la descripción.');
      return;
    }
    this.isBusy = true;
    const payload = {
      incidente_id: id_incidente,
      precio_estimado: this.quotationForm.precio_estimado,
      tiempo_estimado_min: this.quotationForm.tiempo_estimado_min,
      descripcion: this.quotationForm.descripcion,
    };
    this.cotizacionesApi.crear(payload).subscribe({
      next: () => {
        this.isBusy = false;
        this.closeQuotationForm();
        alert('Cotización enviada al cliente');
      },
      error: () => (this.isBusy = false),
    });
  }

  getEstadoLabel(e: string): string {
    const map: Record<string, string> = {
      pendiente: 'Pendiente',
      en_proceso: 'En Proceso',
      en_camino: 'En Camino (Ruta)',
      en_atencion: 'En Sitio (Atendiendo)',
      finalizado: 'Finalizado',
      cancelado: 'Cancelado',
    };
    return map[e] || e;
  }

  ngOnDestroy(): void {
    this.stopTracking();
    this.wsSub?.unsubscribe();
    this.wsService.disconnect();
  }
}
