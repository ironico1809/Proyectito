import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';
import { Observable } from 'rxjs';

export interface SuperadminDashboardData {
  total_tenants: number;
  total_talleres: number;
  total_usuarios: number;
  total_incidentes: number;
  total_ingresos: number;
}

export interface TenantStatItem {
  id_tenant: number;
  nombre: string;
  descripcion?: string | null;
  estado: string; // "activo" | "suspendido"
  talleres_count: number;
  usuarios_count: number;
}

@Injectable({ providedIn: 'root' })
export class SaasApi {
  constructor(private readonly http: HttpClient) {}

  obtenerDashboardGlobal(): Observable<SuperadminDashboardData> {
    return this.http.get<SuperadminDashboardData>(apiUrl('/saas/dashboard'));
  }

  listarTenants(): Observable<TenantStatItem[]> {
    return this.http.get<TenantStatItem[]>(apiUrl('/saas/tenants'));
  }

  actualizarEstadoTenant(idTenant: number, estado: string): Observable<any> {
    return this.http.patch<any>(apiUrl(`/saas/tenants/${idTenant}/estado`), { estado });
  }
}
