import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface KpiResumen {
  total_incidentes: number;
  incidentes_activos: number;
  incidentes_finalizados: number;
  tasa_exito: number;
  tiempo_promedio_atencion_min: number;
  ingresos_totales: number;
  calificacion_promedio: number;
  tecnicos_disponibles: number;
  tecnicos_total: number;
}

export interface IncidentesPorMes {
  mes: string;
  total: number;
}

export interface DistribucionEstado {
  estado: string;
  total: number;
  porcentaje: number;
}

export interface DistribucionPrioridad {
  prioridad: string;
  total: number;
}

export interface TallerRanking {
  taller_id: number;
  nombre: string;
  servicios_completados: number;
  calificacion_promedio: number;
}

export interface TipoIncidente {
  tipo: string;
  total: number;
}

export interface ZonaIncidente {
  lat: number;
  lng: number;
  total: number;
}

export interface SlaData {
  sla_objetivo_min: number;
  total_finalizados: number;
  dentro_sla: number;
  fuera_sla: number;
  porcentaje_cumplimiento: number;
  tiempo_promedio_min: number;
}

export interface TiempoData {
  avg_minutos: number;
  total_medidos?: number;
}

@Injectable({ providedIn: 'root' })
export class KpisApi {
  constructor(private readonly http: HttpClient) {}

  obtenerResumen() {
    return this.http.get<KpiResumen>(apiUrl('/kpis/resumen'));
  }

  incidentesPorMes() {
    return this.http.get<IncidentesPorMes[]>(apiUrl('/kpis/incidentes-por-mes'));
  }

  porEstado() {
    return this.http.get<DistribucionEstado[]>(apiUrl('/kpis/por-estado'));
  }

  porPrioridad() {
    return this.http.get<DistribucionPrioridad[]>(apiUrl('/kpis/por-prioridad'));
  }

  talleresRanking() {
    return this.http.get<TallerRanking[]>(apiUrl('/kpis/talleres-ranking'));
  }

  tiempoRespuesta() {
    return this.http.get<TiempoData>(apiUrl('/kpis/tiempo-respuesta'));
  }

  tiempoAsignacion() {
    return this.http.get<TiempoData>(apiUrl('/kpis/tiempo-asignacion'));
  }

  tiempoLlegada() {
    return this.http.get<TiempoData>(apiUrl('/kpis/tiempo-llegada'));
  }

  porTipo() {
    return this.http.get<TipoIncidente[]>(apiUrl('/kpis/por-tipo'));
  }

  zonasIncidentes() {
    return this.http.get<ZonaIncidente[]>(apiUrl('/kpis/zonas-incidentes'));
  }

  sla() {
    return this.http.get<SlaData>(apiUrl('/kpis/sla'));
  }
}
