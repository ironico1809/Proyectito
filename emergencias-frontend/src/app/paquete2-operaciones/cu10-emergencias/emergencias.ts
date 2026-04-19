import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IncidenteService } from '../../core/services/incidente';
import { TecnicoService } from '../../core/services/tecnico';
import { TecnicoOut } from '../../shared/models/tecnico.model';

@Component({
  selector: 'app-emergencias',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './emergencias.html',
  styleUrls: ['./emergencias.css']
})
export class EmergenciasComponent implements OnInit {
  emergencias: any[] = [];
  cargando: boolean = true;
  tallerId: number = 0;

  // --- VARIABLES PARA EL MODAL (CU11) ---
  mostrarModal: boolean = false;
  incidenteSeleccionado: any = null;
  tecnicosDisponibles: TecnicoOut[] = [];
  tecnicoSeleccionadoId: number | null = null;
  cargandoAsignacion: boolean = false;

  constructor(
    private incidenteService: IncidenteService,
    private tecnicoService: TecnicoService
  ) {}

  ngOnInit(): void {
    // Obtenemos el ID del taller desde el localStorage al iniciar sesión
    this.tallerId = Number(localStorage.getItem('id_taller')) || 1; 
    this.cargarPendientes();
  }

  cargarPendientes(): void {
    this.cargando = true;
    this.incidenteService.getPendientes().subscribe({
      next: (data) => {
        this.emergencias = data;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error cargando emergencias:', err);
        this.cargando = false;
      }
    });
  }

  // CU10: Aceptar o Rechazar
  responder(incidente: any, accion: 'aceptar' | 'rechazar'): void {
    const confirmar = confirm(`¿Estás seguro de ${accion} esta emergencia?`);
    if (!confirmar) return;

    this.incidenteService.responderSolicitud(incidente.id_incidente, accion).subscribe({
      next: () => {
        // Quitamos la emergencia de la lista visual
        this.emergencias = this.emergencias.filter(e => e.id_incidente !== incidente.id_incidente);
        
        if (accion === 'aceptar') {
          // CU11: Si acepta, abrimos el modal para asignar técnico
          this.abrirModalAsignacion(incidente);
        }
      },
      error: (err) => alert('Hubo un error al procesar la solicitud.')
    });
  }

  // --- LÓGICA DEL MODAL CU11 ---
  abrirModalAsignacion(incidente: any): void {
    this.incidenteSeleccionado = incidente;
    this.tecnicoSeleccionadoId = null;
    this.mostrarModal = true;

    // Buscar técnicos del taller
    this.tecnicoService.getTecnicosByTaller(this.tallerId).subscribe({
      next: (data) => {
        // Filtramos para mostrar solo a los que están "Disponibles" (true)
        this.tecnicosDisponibles = data.filter(t => t.disponible_boolean === true);
      },
      error: (err) => console.error('Error cargando técnicos', err)
    });
  }

  cerrarModal(): void {
    this.mostrarModal = false;
    this.incidenteSeleccionado = null;
  }

  confirmarAsignacion(): void {
    if (!this.tecnicoSeleccionadoId) {
      alert('Por favor, selecciona un técnico.');
      return;
    }

    this.cargandoAsignacion = true;
    this.incidenteService.asignarTecnico(this.incidenteSeleccionado.id_incidente, this.tecnicoSeleccionadoId)
      .subscribe({
        next: () => {
          alert('¡Técnico asignado y en ruta exitosamente!');
          this.cargandoAsignacion = false;
          this.cerrarModal();
        },
        error: (err) => {
          alert('Error al asignar el técnico.');
          this.cargandoAsignacion = false;
        }
      });
  }
}