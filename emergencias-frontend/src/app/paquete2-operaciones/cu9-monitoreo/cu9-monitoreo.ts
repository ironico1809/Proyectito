import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

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
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit() {
    this.cargarSeguimiento();
    setInterval(() => this.cargarSeguimiento(), 10000);
  }
  getMapaUrl(incidente: any): SafeResourceUrl {
    let url = '';
    const latCli = incidente.latitud_emergencia;
    const lngCli = incidente.longitud_emergencia;
    const latTec = incidente.latitud_tecnico;
    const lngTec = incidente.longitud_tecnico;

    if (latTec && lngTec) {
      url = `https://maps.google.com/maps?saddr=${latTec},${lngTec}&daddr=${latCli},${lngCli}&output=embed`;
    } else {
      url = `https://maps.google.com/maps?q=${latCli},${lngCli}&z=15&output=embed`;
    }
    
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  cargarSeguimiento() {
    this.http.get<any[]>('https://backend-ixkv.onrender.com/incidentes/en-proceso').subscribe({
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

    this.http.put(`https://backend-ixkv.onrender.com/incidentes/${id}/estado`, {
      estado_enum: 'atendido',
      comentario: 'Servicio cerrado desde panel web.'
    }).subscribe(() => {
      alert('Servicio finalizado. El técnico ahora está disponible.');
      this.cargarSeguimiento();
    });
  }
}