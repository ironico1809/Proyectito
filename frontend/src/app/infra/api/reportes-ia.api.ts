import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { apiUrl } from './api-url';
import { Observable } from 'rxjs';

export interface ReporteResponse {
  reporte_markdown: string;
  prompt_procesado: string;
  datos_periodo: {
    total_incidentes: number;
    ingresos_totales_bs: number;
    tasa_exito: number;
    calificacion_promedio: number;
    [key: string]: any;
  };
}

@Injectable({ providedIn: 'root' })
export class ReportesIaApi {
  private readonly http = inject(HttpClient);

  generarPorTexto(prompt: string, periodo_dias: number = 30): Observable<ReporteResponse> {
    return this.http.post<ReporteResponse>(apiUrl('/reportes-ia/generar'), {
      prompt,
      periodo_dias
    });
  }

  generarPorVoz(audioBase64: string, periodo_dias: number = 30): Observable<ReporteResponse> {
    return this.http.post<ReporteResponse>(apiUrl('/reportes-ia/voz'), {
      audio_base64: audioBase64,
      periodo_dias
    });
  }

  exportarExcel(prompt: string, periodo_dias: number = 30): Observable<Blob> {
    return this.http.post(apiUrl('/reportes-ia/exportar/excel'), {
      prompt,
      periodo_dias
    }, { responseType: 'blob' });
  }

  exportarPdf(prompt: string, periodo_dias: number = 30): Observable<Blob> {
    return this.http.post(apiUrl('/reportes-ia/exportar/pdf'), {
      prompt,
      periodo_dias
    }, { responseType: 'blob' });
  }
}
