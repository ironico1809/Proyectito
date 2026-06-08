import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface UsuarioOut {
  id_usuario: number;
  nombre: string;
  email: string;
  telefono?: string | null;
  rol: string;
}

export interface UsuarioUpdate {
  nombre?: string;
  email?: string;
  password?: string;
  telefono?: string;
  rol?: string;
}

export interface UsuarioCreate {
  nombre: string;
  email: string;
  password: string;
  telefono?: string;
  rol?: string;
}

@Injectable({ providedIn: 'root' })
export class UsuariosApi {
  constructor(private readonly http: HttpClient) {}

  listar() {
    return this.http.get<UsuarioOut[]>(apiUrl('/usuarios/'));
  }

  obtener(id: number) {
    return this.http.get<UsuarioOut>(apiUrl(`/usuarios/${id}`));
  }

  crear(datos: UsuarioCreate) {
    return this.http.post<UsuarioOut>(apiUrl('/usuarios/registro'), datos);
  }

  actualizarParcial(id: number, datos: UsuarioUpdate) {
    return this.http.patch<UsuarioOut>(apiUrl(`/usuarios/${id}`), datos);
  }

  eliminar(id: number) {
    return this.http.delete<{ message: string }>(apiUrl(`/usuarios/${id}`));
  }
}
