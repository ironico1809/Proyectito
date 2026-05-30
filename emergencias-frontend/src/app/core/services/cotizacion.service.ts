import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class CotizacionService {
  private apiUrl = 'http://localhost:8000/cotizaciones';

  constructor(private http: HttpClient) {}

  enviarCotizacion(datos: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/`, datos);
  }
}