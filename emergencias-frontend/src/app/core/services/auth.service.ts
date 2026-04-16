import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { TokenResponse, TipoRol } from '../../shared/models/usuario.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // La dirección donde corre tu backend
  private apiUrl = 'http://127.0.0.1:8000/auth';

  constructor(private http: HttpClient) {}

  // Función para iniciar sesión
  login(datos: any): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.apiUrl}/login`, datos).pipe(
      tap(res => {
        // Guardamos los datos en el navegador para no perder la sesión
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('rol', res.rol);
        localStorage.setItem('nombre', res.nombre);
      })
    );
  }

  // Función para cerrar sesión
  logout(): void {
    localStorage.clear();
  }
}