import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface IncidenteOut {
  id_incidente: number;
  cliente_id: number;
  vehiculo_id: number;
  taller_actual_id?: number | null;
  tecnico_id?: number | null;
  estado_enum: string;
  prioridad_enum: string;
  descripcion_texto?: string | null;
  latitud_emergencia: string;
  longitud_emergencia: string;
  fecha_creacion_timestamp: string;
  cliente_nombre?: string | null;
  vehiculo_placa?: string | null;
  taller_nombre?: string | null;
  tecnico_nombre?: string | null;
}

export interface PaginatedIncidentes {
  items: IncidenteOut[];
  total: number;
  page: number;
  pages: number;
}

export interface MonitoreoOut {
  id_incidente: number;
  cliente_id: number;
  vehiculo_id: number;
  taller_actual_id?: number | null;
  tecnico_id?: number | null;
  estado_enum: string;
  prioridad_enum: string;
  descripcion_texto?: string | null;
  latitud_emergencia: string;
  longitud_emergencia: string;
  fecha_creacion_timestamp: string;
  cliente_nombre?: string;
  vehiculo_placa?: string;
  taller_nombre?: string | null;
  taller_telefono?: string | null;
  tecnico_nombre?: string | null;
  tecnico_especialidad?: string | null;
  tecnico_telefono?: string | null;
  clasificacion_ia?: string | null;
  latitud_tecnico?: number | null;
  longitud_tecnico?: number | null;
  latitud_taller?: number | null;
  longitud_taller?: number | null;
  costo_final_decimal?: number | null;
  evidencias?: { id_evidencia: number; tipo: string; url: string; clasificacion?: string; transcripcion?: string }[];
  historial_estados?: { estado: string; fecha: string; comentario?: string }[];
}

export interface AccionData {
  accion: string;
}

export interface AsignarData {
  tecnico_id: number;
}

export interface EstadoData {
  estado: string;
}

export interface ExcepcionData {
  tipo_excepcion: string;
  motivo: string;
}

@Injectable({ providedIn: 'root' })
export class IncidentesApi {
  constructor(private readonly http: HttpClient) {}

  listarPendientes() {
    return this.http.get<IncidenteOut[]>(apiUrl('/incidentes/pendientes'));
  }

  listarEnProceso() {
    return this.http.get<IncidenteOut[]>(apiUrl('/incidentes/en-proceso'));
  }

  listarTodos(page: number = 1, limit: number = 10, estado?: string, search?: string) {
    let params: any = { page: String(page), limit: String(limit) };
    if (estado) {
      params['estado'] = estado;
    }
    if (search) {
      params['search'] = search;
    }
    return this.http.get<PaginatedIncidentes>(apiUrl('/incidentes/todos'), { params });
  }

  obtenerClienteActivo() {
    return this.http.get<{ id_incidente: number | null }>(
      apiUrl('/incidentes/cliente/activo'),
    );
  }

  obtener(id: number) {
    return this.http.get<IncidenteOut>(apiUrl(`/incidentes/${id}`));
  }

  monitoreo(id: number) {
    return this.http.get<MonitoreoOut>(apiUrl(`/incidentes/${id}/monitoreo_completo`));
  }

  responderAccion(id: number, accion: string) {
    return this.http.post<IncidenteOut>(apiUrl(`/incidentes/${id}/accion`), { accion });
  }

  asignarTecnico(id: number, tecnicoId: number) {
    return this.http.post<IncidenteOut>(apiUrl(`/incidentes/${id}/asignar`), { tecnico_id: tecnicoId });
  }

  actualizarEstado(id: number, estado: string, comentario?: string, costo_final?: number) {
    return this.http.put<IncidenteOut>(apiUrl(`/incidentes/${id}/estado`), {
      estado_enum: estado,
      comentario,
      costo_final
    });
  }

  actualizarUbicacionTecnico(id: number, lat: number, lng: number) {
    return this.http.put<any>(apiUrl(`/incidentes/${id}/ubicacion-tecnico`), {
      latitud: lat,
      longitud: lng
    });
  }

  excepcion(id: number, data: ExcepcionData) {
    return this.http.post<any>(apiUrl(`/incidentes/${id}/excepcion`), data);
  }
}
