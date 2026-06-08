import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface TallerOut {
  id_taller: number;
  dueño_id: number;
  nombre_dueno: string;
  email_dueno: string;
  telefono_dueno?: string | null;
  nombre_taller: string;
  direccion?: string | null;
  nit?: string | null;
  latitud_decimal?: string | null;
  longitud_decimal?: string | null;
}

export interface TallerUpdate {
  nombre_taller?: string;
  direccion?: string;
  nit?: string;
  telefono_dueno?: string;
  nombre_dueno?: string;
  email_dueno?: string;
}

export interface TallerUbicacion {
  latitud: string;
  longitud: string;
}

@Injectable({ providedIn: 'root' })
export class TalleresApi {
  constructor(private readonly http: HttpClient) {}

  listar() {
    return this.http.get<TallerOut[]>(apiUrl('/talleres/'));
  }

  obtener(id: number) {
    return this.http.get<TallerOut>(apiUrl(`/talleres/${id}`));
  }

  eliminar(id: number) {
    return this.http.delete<{ message: string }>(apiUrl(`/talleres/${id}`));
  }

  obtenerMiTaller() {
    return this.http.get<TallerOut>(apiUrl('/talleres/mi-taller/perfil'));
  }

  actualizar(id: number, datos: TallerUpdate) {
    return this.http.patch<TallerOut>(apiUrl(`/talleres/${id}`), datos);
  }

  actualizarUbicacion(datos: TallerUbicacion) {
    return this.http.patch<TallerOut>(apiUrl('/talleres/mi-ubicacion/actualizar'), datos);
  }
}
