import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PagoService {
  private apiUrl = 'http://localhost:8000/pagos';

  constructor(private http: HttpClient) {}

  // CU14: Obtener todos los pagos y comisiones para el Admin
  obtenerPagos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/`);
  }
  // Para el Taller: Ver solo sus ingresos
  obtenerPagosPorTaller(tallerId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/taller/${tallerId}`);
  }
}