import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { catchError, of, switchMap } from 'rxjs';
import { IncidentesApi } from '../../../../infra/api/incidentes.api';
import { CotizacionesApi, CotizacionOut } from '../../../../infra/api/cotizaciones.api';
import { TalleresApi } from '../../../../infra/api/talleres.api';

@Component({
  selector: 'ev-quotations-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './quotations.page.html',
  styleUrl: './quotations.page.css',
})
export class QuotationsPage {
  private readonly incidentesApi = inject(IncidentesApi);
  private readonly cotizacionesApi = inject(CotizacionesApi);
  private readonly talleresApi = inject(TalleresApi);

  readonly pendientes$ = this.incidentesApi.listarPendientes().pipe(catchError(() => of([])));
  readonly taller$ = this.talleresApi.obtenerMiTaller().pipe(catchError(() => of(null)));

  selectedIncidenteId: number | null = null;
  cotizaciones: CotizacionOut[] = [];

  showQuotationForm = false;
  quotationForm = { precio_estimado: 0, tiempo_estimado_min: 60, descripcion: '' };
  tallerId = 0;

  verCotizaciones(incidenteId: number) {
    this.selectedIncidenteId = incidenteId;
    this.cotizacionesApi.listarPorIncidente(incidenteId).subscribe((data) => {
      this.cotizaciones = data;
    });
  }

  volver() {
    this.selectedIncidenteId = null;
    this.cotizaciones = [];
  }

  getEstadoColor(estado: string): string {
    const map: Record<string, string> = {
      pendiente: 'var(--amber-500)',
      aceptada: 'var(--success)',
      rechazada: 'var(--danger)',
      expirada: 'var(--text-muted)',
    };
    return map[estado] || 'var(--text-muted)';
  }

  openQuotationForm(tallerId: number) {
    this.tallerId = tallerId;
    this.showQuotationForm = true;
    this.quotationForm = { precio_estimado: 0, tiempo_estimado_min: 60, descripcion: '' };
  }

  closeQuotationForm() {
    this.showQuotationForm = false;
  }

  createQuotation() {
    if (!this.selectedIncidenteId || !this.quotationForm.precio_estimado || !this.quotationForm.descripcion) return;
    this.cotizacionesApi.crear({
      incidente_id: this.selectedIncidenteId,
      precio_estimado: this.quotationForm.precio_estimado,
      tiempo_estimado_min: this.quotationForm.tiempo_estimado_min,
      descripcion: this.quotationForm.descripcion,
    }).subscribe(() => {
      this.showQuotationForm = false;
      if (this.selectedIncidenteId) {
        this.cotizacionesApi.listarPorIncidente(this.selectedIncidenteId).subscribe((data) => {
          this.cotizaciones = data;
        });
      }
    });
  }
}
