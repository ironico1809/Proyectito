import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface CotizacionOut {
  id_cotizacion: number;
  incidente_id: number;
  taller_id: number;
  taller_nombre?: string;
  precio_estimado: string;
  tiempo_estimado_min: number;
  descripcion?: string | null;
  estado: string;
  fecha_envio: string;
}

export interface CotizacionCreate {
  incidente_id: number;
  precio_estimado: number;
  tiempo_estimado_min: number;
  descripcion: string;
}

@Injectable({ providedIn: 'root' })
export class CotizacionesApi {
  constructor(private readonly http: HttpClient) {}

  listarPorIncidente(incidenteId: number) {
    return this.http.get<CotizacionOut[]>(apiUrl(`/cotizaciones/${incidenteId}`));
  }

  crear(data: CotizacionCreate) {
    return this.http.post<CotizacionOut>(apiUrl('/cotizaciones/'), data);
  }

  aceptar(id: number) {
    return this.http.put<CotizacionOut>(apiUrl(`/cotizaciones/${id}/aceptar`), {});
  }

  rechazar(id: number) {
    return this.http.put<CotizacionOut>(apiUrl(`/cotizaciones/${id}/rechazar`), {});
  }
}
