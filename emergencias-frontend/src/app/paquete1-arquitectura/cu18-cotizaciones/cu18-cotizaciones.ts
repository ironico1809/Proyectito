import { Component } from '@angular/core';
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
export class Cu18Cotizaciones {
  incidentesPendientes: any[] = [];
  nuevaCotizacion = { 
    incidente_id: null, 
    precio_estimado: null, 
    tiempo_estimado_min: null, 
    descripcion: '' 
  };

  constructor(
    private cotizacionService: CotizacionService,
    private incidenteService: IncidenteService
  ) {
    this.cargarIncidentes();
  }

  cargarIncidentes() {
    // Aquí usamos el servicio que ya tenían para traer los incidentes pendientes
    this.incidenteService.getPendientes().subscribe(data => {
      this.incidentesPendientes = data;
    });
  }

  enviarCotizacion(incidenteId: number) {
    if (!this.nuevaCotizacion.precio_estimado || !this.nuevaCotizacion.tiempo_estimado_min) {
      alert('Por favor, ingresa un precio y tiempo estimado válidos.');
      return;
    }

    this.nuevaCotizacion.incidente_id = incidenteId as any;
    
    this.cotizacionService.enviarCotizacion(this.nuevaCotizacion).subscribe({
      next: () => {
        alert('Cotización enviada con éxito');
        this.nuevaCotizacion = { incidente_id: null, precio_estimado: null, tiempo_estimado_min: null, descripcion: '' };
        this.cargarIncidentes(); // Recargar la lista para quitar el incidente o actualizar vista
      },
      error: (err) => {
        console.error('Error al enviar la cotización', err);
        alert('Hubo un error al enviar la cotización.');
      }
    });
  }
}