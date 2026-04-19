import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TecnicoOut, TecnicoCreate, TecnicoPartial } from '../../shared/models/tecnico.model';

@Injectable({
  providedIn: 'root'
})
export class TecnicoService {
  // Asegúrate de que apiUrl tampoco tenga barra al final aquí
  private apiUrl = 'http://localhost:8000/tecnicos'; 

  constructor(private http: HttpClient) {}

  // ⚡ EL GET NO DEBE TENER BARRA AL FINAL
  getTecnicosByTaller(tallerId: number): Observable<TecnicoOut[]> {
    return this.http.get<TecnicoOut[]>(`${this.apiUrl}/taller/${tallerId}`);
  }

  // EL POST SÍ NECESITA LA BARRA (porque en main.py tu router es /tecnicos/)
  crearTecnico(tecnico: TecnicoCreate): Observable<TecnicoOut> {
    return this.http.post<TecnicoOut>(`${this.apiUrl}/`, tecnico);
  }

  updateDisponibilidad(idTecnico: number, data: TecnicoPartial): Observable<TecnicoOut> {
    return this.http.patch<TecnicoOut>(`${this.apiUrl}/${idTecnico}`, data);
  }

  deleteTecnico(idTecnico: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${idTecnico}`);
  }
}