import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface TecnicoOut {
  id_tecnico: number;
  taller_id: number;
  usuario_id: number;
  nombre: string;
  especialidad?: string | null;
  disponible_boolean: boolean;
}

export interface TecnicoCreate {
  taller_id: number;
  nombre: string;
  email: string;
  password: string;
  telefono?: string;
  especialidad?: string;
  disponible_boolean?: boolean;
}

export interface TecnicoUpdate {
  nombre?: string;
  especialidad?: string;
  disponible_boolean?: boolean;
}

@Injectable({ providedIn: 'root' })
export class TecnicosApi {
  constructor(private readonly http: HttpClient) {}

  listarTodos() {
    return this.http.get<TecnicoOut[]>(apiUrl('/tecnicos/todos'));
  }

  listarPorTaller(tallerId: number) {
    return this.http.get<TecnicoOut[]>(apiUrl(`/tecnicos/taller/${tallerId}`));
  }

  crear(datos: TecnicoCreate) {
    return this.http.post<TecnicoOut>(apiUrl('/tecnicos/'), datos);
  }

  actualizarParcial(id: number, datos: TecnicoUpdate) {
    return this.http.patch<TecnicoOut>(apiUrl(`/tecnicos/${id}`), datos);
  }

  eliminar(id: number) {
    return this.http.delete<{ message: string }>(apiUrl(`/tecnicos/${id}`));
  }
}
