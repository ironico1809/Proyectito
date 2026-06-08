import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, catchError, of, finalize } from 'rxjs';
import { KpisApi, KpiResumen, IncidentesPorMes, DistribucionEstado, DistribucionPrioridad, TallerRanking, TipoIncidente, SlaData, TiempoData } from '../../../../infra/api/kpis.api';

interface StatusColors {
  [key: string]: string;
}

@Component({
  selector: 'ev-kpis-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './kpis.page.html',
  styleUrl: './kpis.page.css',
})
export class KpisPage implements OnInit {
  private readonly kpisApi = inject(KpisApi);

  isLoading = true;
  error = false;

  resumen: KpiResumen | null = null;
  incidentesPorMes: IncidentesPorMes[] = [];
  porEstado: DistribucionEstado[] = [];
  porPrioridad: DistribucionPrioridad[] = [];
  talleresRanking: TallerRanking[] = [];
  porTipo: TipoIncidente[] = [];
  sla: SlaData | null = null;
  tiempoAsignacion: TiempoData | null = null;
  tiempoLlegada: TiempoData | null = null;
  tiempoRespuesta: TiempoData | null = null;

  maxMes = 0;
  maxTipo = 0;

  readonly statusColors: StatusColors = {
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

  readonly prioridadColors: StatusColors = {
    baja: '#22c55e',
    media: '#f59e0b',
    alta: '#ef4444',
    critica: '#dc2626',
  };

  readonly tipoIcons: StatusColors = {
    batería: 'battery_charging_full',
    battery: 'battery_charging_full',
    llanta: 'tire_repair',
    motor: 'engine',
    choque: 'collision',
    otros: 'help',
  };

  readonly tipoColors: StatusColors = {
    batería: '#f59e0b',
    battery: '#f59e0b',
    llanta: '#3b82f6',
    motor: '#10b981',
    choque: '#ef4444',
    otros: '#8b5cf6',
  };

  ngOnInit() {
    this.cargarDatos();
  }

  cargarDatos() {
    this.isLoading = true;
    this.error = false;

    forkJoin({
      resumen: this.kpisApi.obtenerResumen().pipe(catchError(() => of(null))),
      porMes: this.kpisApi.incidentesPorMes().pipe(catchError(() => of([]))),
      porEstado: this.kpisApi.porEstado().pipe(catchError(() => of([]))),
      porPrioridad: this.kpisApi.porPrioridad().pipe(catchError(() => of([]))),
      talleres: this.kpisApi.talleresRanking().pipe(catchError(() => of([]))),
      porTipo: this.kpisApi.porTipo().pipe(catchError(() => of([]))),
      sla: this.kpisApi.sla().pipe(catchError(() => of(null))),
      tAsignacion: this.kpisApi.tiempoAsignacion().pipe(catchError(() => of(null))),
      tLlegada: this.kpisApi.tiempoLlegada().pipe(catchError(() => of(null))),
      tRespuesta: this.kpisApi.tiempoRespuesta().pipe(catchError(() => of(null))),
    }).pipe(
      finalize(() => this.isLoading = false)
    ).subscribe({
      next: (data) => {
        this.resumen = data.resumen;
        this.incidentesPorMes = data.porMes;
        this.porEstado = data.porEstado;
        this.porPrioridad = data.porPrioridad;
        this.talleresRanking = data.talleres;
        this.porTipo = data.porTipo;
        this.sla = data.sla;
        this.tiempoAsignacion = data.tAsignacion;
        this.tiempoLlegada = data.tLlegada;
        this.tiempoRespuesta = data.tRespuesta;

        this.maxMes = Math.max(...data.porMes.map(m => m.total), 1);
        this.maxTipo = Math.max(...data.porTipo.map(t => t.total), 1);

        if (!data.resumen && !data.sla) {
          this.error = true;
        }
      },
      error: () => {
        this.error = true;
        this.isLoading = false;
      }
    });
  }

  conicGradient(items: { label: string; value: number; color: string }[]): string {
    const total = items.reduce((s, i) => s + i.value, 0) || 1;
    let current = 0;
    return items
      .map((i) => {
        const pct = (i.value / total) * 100;
        const start = current;
        current += pct;
        return `${i.color} ${start}% ${current}%`;
      })
      .join(', ');
  }

  donutData(): { label: string; value: number; color: string }[] {
    if (!this.porEstado.length) return [];
    return this.porEstado.map((e) => ({
      label: this.formatLabel(e.estado),
      value: e.total,
      color: this.statusColors[e.estado] || '#64748b',
    }));
  }

  formatLabel(key: string): string {
    const map: StatusColors = {
      pendiente: 'Pendiente',
      en_proceso: 'En Proceso',
      buscando_taller: 'Buscando Taller',
      taller_asignado: 'Taller Asignado',
      en_camino: 'En Camino',
      en_atencion: 'En Atención',
      atendido: 'Atendido',
      finalizado: 'Finalizado',
      cancelado: 'Cancelado',
      baja: 'Baja',
      media: 'Media',
      alta: 'Alta',
      critica: 'Crítica',
    };
    return map[key] || key;
  }
}
