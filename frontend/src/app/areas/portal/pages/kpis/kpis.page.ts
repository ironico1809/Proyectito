import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, catchError, of, finalize } from 'rxjs';
import { KpisApi, KpiResumen, IncidentesPorMes, DistribucionEstado, DistribucionPrioridad, TallerRanking, TipoIncidente, SlaData, TiempoData } from '../../../../infra/api/kpis.api';
import { ReportesIaApi, ReporteResponse } from '../../../../infra/api/reportes-ia.api';

// Declaración para el API de reconocimiento de voz del navegador
declare var webkitSpeechRecognition: any;

interface StatusColors {
  [key: string]: string;
}

@Component({
  selector: 'ev-kpis-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './kpis.page.html',
  styleUrl: './kpis.page.css',
})
export class KpisPage implements OnInit {
  private readonly kpisApi: KpisApi = inject(KpisApi);
  private readonly reportesApi: ReportesIaApi = inject(ReportesIaApi);

  isLoading = true;
  error = false;

  // Estados de Voz
  isRecording = false;
  transcript = '';
  recognition: any;
  isGeneratingReport = false;
  reporteGenerado: ReporteResponse | null = null;

  readonly reportesRapidos = [
    { label: 'Resumen Mensual', prompt: 'Dame un resumen ejecutivo de los incidentes de los últimos 30 días, destacando la tasa de éxito y los ingresos.' },
    { label: 'Análisis de Fallas', prompt: 'Analiza los tipos de incidentes más comunes y sugiere medidas preventivas basadas en los datos.' },
    { label: 'Ranking de Talleres', prompt: 'Explica por qué los mejores talleres tienen ese rendimiento y qué diferencia hay con el promedio.' },
    { label: 'Cumplimiento SLA', prompt: 'Evalúa el cumplimiento de los tiempos de respuesta (SLA) e identifica cuellos de botella en la operación.' }
  ];

  resumen: KpiResumen | null = null;
  incidentesPorMes: IncidentesPorMes[] = [];
  porEstado: DistribucionEstado[] = [];
  porPrioridad: DistribucionPrioridad[] = [];
  talleresRanking: TallerRanking[] = [];
  porTipo: TipoIncidente[] = [];
  sla: SlaData | null = null;
  tiempoAsignacion: TiempoData | null = null;
  tiempoLlegada: TiempoData | null = null;
  tiempoRespuesta: TiempoData | null = null;

  maxMes = 0;
  maxTipo = 0;

  readonly statusColors: StatusColors = {
    pendiente: '#f59e0b',
    en_proceso: '#3b82f6',
    buscando_taller: '#8b5cf6',
    taller_asignado: '#06b6d4',
    en_camino: '#10b981',
    en_atencion: '#f97316',
    atendido: '#22c55e',
    finalizado: '#14b8a6',
    cancelado: '#ef4444',
  };

  readonly prioridadColors: StatusColors = {
    baja: '#22c55e',
    media: '#f59e0b',
    alta: '#ef4444',
    critica: '#dc2626',
  };

  readonly tipoIcons: StatusColors = {
    batería: 'battery_charging_full',
    battery: 'battery_charging_full',
    llanta: 'tire_repair',
    motor: 'engine',
    choque: 'collision',
    otros: 'help',
  };

  readonly tipoColors: StatusColors = {
    batería: '#f59e0b',
    battery: '#f59e0b',
    llanta: '#3b82f6',
    motor: '#10b981',
    choque: '#ef4444',
    otros: '#8b5cf6',
  };

  ngOnInit() {
    this.cargarDatos();
  }

  cargarDatos() {
    this.isLoading = true;
    this.error = false;

    this.kpisApi.obtenerTodo().pipe(
      finalize(() => this.isLoading = false)
    ).subscribe({
      next: (data) => {
        this.resumen = data.resumen;
        this.incidentesPorMes = data.porMes || [];
        this.porEstado = data.porEstado || [];
        this.porPrioridad = data.porPrioridad || [];
        this.talleresRanking = data.talleres || [];
        this.porTipo = data.porTipo || [];
        this.sla = data.sla;
        this.tiempoAsignacion = data.tAsignacion;
        this.tiempoLlegada = data.tLlegada;
        this.tiempoRespuesta = data.tRespuesta;

        this.maxMes = Math.max(...(data.porMes || []).map((m: any) => m.total), 1);
        this.maxTipo = Math.max(...(data.porTipo || []).map((t: any) => t.total), 1);

        if (!data.resumen && !data.sla) {
          this.error = true;
        }
      },
      error: () => {
        this.error = true;
        this.isLoading = false;
      }
    });
  }

  conicGradient(items: { label: string; value: number; color: string }[]): string {
    const total = items.reduce((s, i) => s + i.value, 0) || 1;
    let current = 0;
    return items
      .map((i) => {
        const pct = (i.value / total) * 100;
        const start = current;
        current += pct;
        return `${i.color} ${start}% ${current}%`;
      })
      .join(', ');
  }

  donutData(): { label: string; value: number; color: string }[] {
    if (!this.porEstado.length) return [];
    return this.porEstado.map((e) => ({
      label: this.formatLabel(e.estado),
      value: e.total,
      color: this.statusColors[e.estado] || '#64748b',
    }));
  }

  formatLabel(key: string): string {
    const map: StatusColors = {
      pendiente: 'Pendiente',
      en_proceso: 'En Proceso',
      buscando_taller: 'Buscando Taller',
      taller_asignado: 'Taller Asignado',
      en_camino: 'En Camino',
      en_atencion: 'En Atención',
      atendido: 'Atendido',
      finalizado: 'Finalizado',
      cancelado: 'Cancelado',
      baja: 'Baja',
      media: 'Media',
      alta: 'Alta',
      critica: 'Crítica',
    };
    return map[key] || key;
  }

  // ---- CONTROL DE VOZ Y REPORTES IA ----
  
  initVoice() {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Tu navegador no soporta reconocimiento de voz.');
      return;
    }

    this.recognition = new webkitSpeechRecognition();
    this.recognition.lang = 'es-ES';
    this.recognition.continuous = true;
    this.recognition.interimResults = true;

    this.recognition.onresult = (event: any) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        this.transcript = finalTranscript;
      }
    };

    this.recognition.onend = () => {
      if (this.isRecording) {
        this.stopVoice();
      }
    };
  }

  toggleVoice() {
    if (this.isRecording) {
      this.stopVoice();
    } else {
      this.startVoice();
    }
  }

  startVoice() {
    if (!this.recognition) this.initVoice();
    this.transcript = '';
    this.reporteGenerado = null;
    this.recognition.start();
    this.isRecording = true;
  }

  stopVoice() {
    this.recognition.stop();
    this.isRecording = false;
    
    // Procesar automáticamente al detener
    if (this.transcript.trim()) {
      this.generarReporteIA();
    }
  }

  generarReporteRapido(prompt: string) {
    this.transcript = prompt;
    this.generarReporteIA();
  }

  generarReporteIA() {
    if (!this.transcript.trim()) return;

    this.isGeneratingReport = true;
    this.reportesApi.generarPorTexto(this.transcript, 30).pipe(
      finalize(() => this.isGeneratingReport = false)
    ).subscribe({
      next: (res: ReporteResponse) => {
        this.reporteGenerado = res;
      },
      error: () => alert('Error al generar el reporte con IA.')
    });
  }

  exportarPDF() {
    if (!this.reporteGenerado) return;
    this.reportesApi.exportarPdf(this.transcript || 'Reporte de KPIs', 30).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Reporte_Analitica_${new Date().getTime()}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => alert('Error al generar el PDF profesional.')
    });
  }

  exportarExcel() {
    if (!this.reporteGenerado) return;
    this.reportesApi.exportarExcel(this.transcript || 'Reporte de KPIs', 30).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Reporte_Operativo_${new Date().getTime()}.xlsx`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => alert('Error al generar el archivo Excel.')
    });
  }
}
