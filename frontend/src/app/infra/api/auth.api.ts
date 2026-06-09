import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { apiUrl } from './api-url';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  rol: string;
  nombre: string;
  id_usuario: number;
  id_taller?: number | null;
  tenant_id?: number;
}


@Injectable({ providedIn: 'root' })
export class AuthApi {
  constructor(private readonly http: HttpClient) {}

  login(payload: LoginPayload) {
    return this.http.post<TokenResponse>(apiUrl('/auth/login'), payload);
  }

  registroSaaS(payload: any) {
    return this.http.post<TokenResponse>(apiUrl('/saas/registro-saas'), payload);
  }

  logout() {
    return this.http.post<{ message: string }>(apiUrl('/auth/logout'), {});
  }
}
