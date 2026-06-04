import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CotizacionService } from '../../core/services/cotizacion.service';
import { IncidenteService } from '../../core/services/incidente';

@Component({
  selector: 'app-cu18-cotizaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cu18-cotizaciones.html',
  styleUrls: ['./cu18-cotizaciones.css'] 
})
export class Cu18Cotizaciones implements OnInit {
  incidentesPendientes: any[] = [];
  cargando = false;

  // Un formulario independiente por incidente
  formularios: { [incidenteId: number]: any } = {};

  constructor(
    private cotizacionService: CotizacionService,
    private incidenteService: IncidenteService
  ) {}

  ngOnInit() { this.cargarIncidentes(); }

  cargarIncidentes() {
    this.cargando = true;
    this.incidenteService.getPendientes().subscribe({
      next: (data) => {
        this.incidentesPendientes = data;
        // Inicializar formulario vacío para cada incidente
        data.forEach((inc: any) => {
          if (!this.formularios[inc.id_incidente]) {
            this.formularios[inc.id_incidente] = {
              precio_estimado: null,
              tiempo_estimado_min: null,
              descripcion: ''
            };
          }
        });
        this.cargando = false;
      },
      error: () => this.cargando = false
    });
  }

  enviarCotizacion(incidenteId: number) {
    const form = this.formularios[incidenteId];
    if (!form?.precio_estimado || !form?.tiempo_estimado_min) {
      alert('Ingresá un precio y tiempo estimado válidos.');
      return;
    }
    const payload = {
      incidente_id:         incidenteId,
      precio_estimado:      form.precio_estimado,
      tiempo_estimado_min:  form.tiempo_estimado_min,
      descripcion:          form.descripcion
    };
    this.cotizacionService.enviarCotizacion(payload).subscribe({
      next: () => {
        alert('✅ Cotización enviada con éxito.');
        this.formularios[incidenteId] = {
          precio_estimado: null, tiempo_estimado_min: null, descripcion: ''
        };
        // Ocultar el incidente de la lista — ya tiene cotización de este taller
        this.incidentesPendientes = this.incidentesPendientes
          .filter(i => i.id_incidente !== incidenteId);
      },
      error: () => alert('Error al enviar la cotización.')
    });
  }
}
