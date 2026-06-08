import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface VehiculoOut {
  id_vehiculo: number;
  usuario_id: number;
  placa: string;
  marca?: string | null;
  modelo?: string | null;
  color?: string | null;
}

export interface VehiculoCreate {
  usuario_id: number;
  placa: string;
  marca?: string;
  modelo?: string;
  color?: string;
}

export interface VehiculoUpdate {
  placa?: string;
  marca?: string;
  modelo?: string;
  color?: string;
}

@Injectable({ providedIn: 'root' })
export class VehiculosApi {
  constructor(private readonly http: HttpClient) {}

  listarMisVehiculos() {
    return this.http.get<VehiculoOut[]>(apiUrl('/vehiculos/'));
  }

  crear(datos: VehiculoCreate) {
    return this.http.post<VehiculoOut>(apiUrl('/vehiculos/'), datos);
  }

  actualizar(id: number, datos: VehiculoUpdate) {
    return this.http.patch<VehiculoOut>(apiUrl(`/vehiculos/${id}`), datos);
  }

  eliminar(id: number) {
    return this.http.delete<{ message: string }>(apiUrl(`/vehiculos/${id}`));
  }
}
