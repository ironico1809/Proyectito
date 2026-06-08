import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface NotificacionOut {
  id_notificacion: number;
  usuario_id: number;
  titulo: string;
  mensaje: string;
  leido_boolean: boolean;
  fecha_creacion_timestamp: string;
}

@Injectable({ providedIn: 'root' })
export class NotificacionesApi {
  constructor(private readonly http: HttpClient) {}

  misNotificaciones() {
    return this.http.get<NotificacionOut[]>(apiUrl('/notificaciones/mis-notificaciones'));
  }

  noLeidas() {
    return this.http.get<{ total_no_leidas: number }>(apiUrl('/notificaciones/no-leidas'));
  }

  marcarLeida(id: number) {
    return this.http.patch<NotificacionOut>(apiUrl(`/notificaciones/${id}/leer`), {});
  }
}
