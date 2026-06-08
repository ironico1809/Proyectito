import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface PagoOut {
  id_pago: number;
  incidente_id: number;
  dueño_taller_id: number;
  monto_total_decimal: string;
  comision_plataforma_decimal: string;
  metodo_enum: string;
  estado_pago_enum: string;
  fecha_pago_timestamp: string;
}

export interface PagoCreate {
  incidente_id: number;
  monto_total_decimal: number;
  comision_plataforma_decimal: number;
  metodo_enum: string;
}

@Injectable({ providedIn: 'root' })
export class PagosApi {
  constructor(private readonly http: HttpClient) {}

  listarTodos() {
    return this.http.get<PagoOut[]>(apiUrl('/pagos/'));
  }

  listarMisIngresos() {
    return this.http.get<PagoOut[]>(apiUrl('/pagos/mis-ingresos'));
  }

  crear(datos: PagoCreate) {
    return this.http.post<PagoOut>(apiUrl('/pagos/'), datos);
  }
}
