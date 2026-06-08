import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { IncidentesApi } from '../../../../infra/api/incidentes.api';
import { SessionStore } from '../../../../infra/session/session.store';

@Component({
  selector: 'ev-location-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './location.page.html',
  styleUrl: './location.page.css',
})
export class LocationPage implements OnInit, OnDestroy {
  private readonly sanitizer = inject(DomSanitizer);
  private readonly incidentesApi = inject(IncidentesApi);
  private readonly sessionStore = inject(SessionStore);

  isTracking = false;
  isSharing = false;
  lastUpdated: string | null = null;
  coordinates = { lat: -17.7831, lng: -63.1821 }; // SCZ
  mapaUrlSegura: SafeResourceUrl | null = null;

  incidentes: any[] = [];
  selectedIncidentId: number | null = null;
  private sharingTimer: any = null;

  ngOnInit() {
    this.lastUpdated = new Date().toLocaleTimeString();
    this.generarMapa(this.coordinates.lat, this.coordinates.lng);
    this.cargarIncidentes();
  }

  ngOnDestroy() {
    this.stopSharing();
  }

  cargarIncidentes() {
    const session = this.sessionStore.snapshot();
    this.incidentesApi.listarEnProceso().subscribe({
      next: (list) => {
        if (session?.role === 'tecnico') {
          // Filtrar incidentes asignados a este técnico
          this.incidentes = list.filter((i) => i.tecnico_id === session.userId);
        } else {
          // Admin/Taller ven todos los en proceso
          this.incidentes = list;
        }
        if (this.incidentes.length > 0) {
          this.selectedIncidentId = this.incidentes[0].id_incidente;
        } else {
          this.selectedIncidentId = null;
        }
      },
      error: () => {}
    });
  }

  generarMapa(lat: number, lng: number) {
    const urlBruta = `https://maps.google.com/maps?q=${lat},${lng}&z=15&output=embed`;
    this.mapaUrlSegura = this.sanitizer.bypassSecurityTrustResourceUrl(urlBruta);
  }

  updateLocation() {
    this.isTracking = true;

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.coordinates.lat = position.coords.latitude;
          this.coordinates.lng = position.coords.longitude;
          this.lastUpdated = new Date().toLocaleTimeString();
          
          this.generarMapa(this.coordinates.lat, this.coordinates.lng);
          this.isTracking = false;

          // Si está transmitiendo activamente, enviar al backend
          if (this.isSharing && this.selectedIncidentId) {
            this.enviarUbicacionAlServidor(this.selectedIncidentId, this.coordinates.lat, this.coordinates.lng);
          }
        },
        (error) => {
          alert('No se pudo obtener la ubicación. Asegúrate de darle permisos al navegador.');
          this.isTracking = false;
          this.stopSharing();
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    } else {
      alert('Tu navegador no soporta geolocalización.');
      this.isTracking = false;
      this.stopSharing();
    }
  }

  toggleSharing() {
    if (this.isSharing) {
      this.stopSharing();
    } else {
      if (!this.selectedIncidentId) {
        alert('Debes seleccionar un incidente activo primero.');
        return;
      }
      this.startSharing();
    }
  }

  startSharing() {
    this.isSharing = true;
    this.updateLocation(); // Primera actualización inmediata
    // Transmitir cada 10 segundos
    this.sharingTimer = setInterval(() => {
      this.updateLocation();
    }, 10000);
  }

  stopSharing() {
    this.isSharing = false;
    if (this.sharingTimer) {
      clearInterval(this.sharingTimer);
      this.sharingTimer = null;
    }
  }

  private enviarUbicacionAlServidor(incidentId: number, lat: number, lng: number) {
    this.incidentesApi.actualizarUbicacionTecnico(incidentId, lat, lng).subscribe({
      next: () => {
        console.log('Ubicación enviada al servidor');
      },
      error: (err) => {
        console.error('Error al enviar ubicación:', err);
      }
    });
  }
}
