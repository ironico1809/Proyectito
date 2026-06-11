// ============================================================
// infra/api/bitacora.api.ts
// Cliente HTTP para el historial de trazabilidad (bitácora)
// ============================================================
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { apiUrl } from './api-url';

export interface BitacoraItem {
  id_bitacora: number;
  incidente_id: number;
  evento: string;
  descripcion: string;
  usuario_id: number | null;
  usuario_nombre: string | null;
  timestamp: string;
}

@Injectable({ providedIn: 'root' })
export class BitacoraApi {
  private http = inject(HttpClient);

  obtenerBitacora(incidenteId: number): Observable<BitacoraItem[]> {
    return this.http.get<BitacoraItem[]>(apiUrl(`/bitacora/${incidenteId}`));
  }
}