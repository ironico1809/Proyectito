import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser'; // 👈 IMPORTANTE

@Component({
  selector: 'app-cu9-monitoreo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cu9-monitoreo.html',
  styleUrls: ['./cu9-monitoreo.css']
})
export class Cu9Monitoreo implements OnInit {
  serviciosActivos: any[] = [];
  cargando = true;

  constructor(
    private http: HttpClient,
    private sanitizer: DomSanitizer // 👈 Inyectamos el Sanitizer
  ) {}

  ngOnInit() {
    this.cargarSeguimiento();
    // Opcional: Refrescar automáticamente cada 30 seg para ver movimiento real
    setInterval(() => this.cargarSeguimiento(), 30000);
  }

  // ⚡ FUNCIÓN MÁGICA PARA EL MAPA REAL
  getMapaUrl(lat: number, lng: number): SafeResourceUrl {
    // Usamos el modo 'embed' de Google Maps. No requiere API Key para uso básico.
    const url = `https://maps.google.com/maps?q=${lat},${lng}&z=15&output=embed`;
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  cargarSeguimiento() {
    this.cargando = true;
    this.http.get<any[]>('http://localhost:8000/incidentes/en-proceso').subscribe({
      next: (data) => {
        this.serviciosActivos = data;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error cargando monitoreo:', err);
        this.cargando = false;
      }
    });
  }

  finalizarServicio(id: number) {
    if (!confirm('¿Confirmas que el servicio ha sido finalizado con éxito?')) return;

    this.http.put(`http://localhost:8000/incidentes/${id}/estado`, {
      estado_enum: 'atendido',
      comentario: 'Servicio cerrado desde panel web.'
    }).subscribe(() => {
      alert('Servicio finalizado. El técnico ahora está disponible.');
      this.cargarSeguimiento();
    });
  }
}