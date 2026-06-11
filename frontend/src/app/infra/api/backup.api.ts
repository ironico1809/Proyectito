// ============================================================
// infra/api/backup.api.ts
// Cliente HTTP para el módulo de Backup
// ============================================================
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';
import { Observable } from 'rxjs';

export interface BackupItem {
  id: number;
  nombre_archivo: string;
  tipo: 'manual' | 'automatico';
  tamanio_bytes: number | null;
  creado_en: string;
}

export interface ConfigBackup {
  hora_automatico: string | null;
  automatico_activo: boolean;
}

@Injectable({ providedIn: 'root' })
export class BackupApi {
  constructor(private http: HttpClient) {}

  historial(): Observable<BackupItem[]> {
    return this.http.get<BackupItem[]>(apiUrl('/backup/historial'));
  }

  generarManual(): Observable<BackupItem> {
    return this.http.post<BackupItem>(apiUrl('/backup/generar'), {});
  }

  obtenerConfig(): Observable<ConfigBackup> {
    return this.http.get<ConfigBackup>(apiUrl('/backup/configuracion'));
  }

  guardarConfig(config: ConfigBackup): Observable<ConfigBackup> {
    return this.http.post<ConfigBackup>(apiUrl('/backup/configuracion'), config);
  }

  eliminar(id: number): Observable<void> {
    return this.http.delete<void>(apiUrl(`/backup/${id}`));
  }

  descargarUrl(id: number): string {
    return apiUrl(`/backup/descargar/${id}`);
  }
}