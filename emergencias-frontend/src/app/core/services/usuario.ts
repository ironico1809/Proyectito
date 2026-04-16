import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Usuario } from '../../shared/models/usuario.model';

@Injectable({
  providedIn: 'root'
})
export class UsuarioService {
  private apiUrl = 'http://127.0.0.1:8000/usuarios/';

  constructor(private http: HttpClient) {}

  getUsuarios(): Observable<Usuario[]> {
    return this.http.get<Usuario[]>(this.apiUrl);
  }

  // NUEVO: Petición DELETE
  deleteUsuario(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}${id}`);
  }

  // NUEVO: Petición PATCH para editar parcialmente
  updateUsuario(id: number, datos: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}${id}`, datos);
  }
}