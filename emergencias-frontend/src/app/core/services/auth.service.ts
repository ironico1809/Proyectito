import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { TokenResponse, TipoRol } from '../../shared/models/usuario.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'https://backend-ixkv.onrender.com/auth';

  constructor(private http: HttpClient) {}

  login(datos: any): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.apiUrl}/login`, datos).pipe(
      tap(res => {
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('rol', res.rol);
        localStorage.setItem('nombre', res.nombre);
        
        const idParaGuardar = res.id_taller ? res.id_taller : res.id_usuario;
        localStorage.setItem('id_entidad', idParaGuardar.toString());
      })
    );
  }

  logout(): void {
    localStorage.clear();
  }
}