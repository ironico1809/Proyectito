import { Component, OnInit, HostListener, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificacionService } from '../../core/services/notificacion';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.html',
  styleUrls: ['./navbar.css']
})
export class NavbarComponent implements OnInit {
  notificaciones: any[] = [];
  cantidadNoLeidas: number = 0;
  mostrarDropdown: boolean = false;
  nombreUsuario: string = ''; 
  rolUsuario: string = '';

  @Output() onToggle = new EventEmitter<void>();

  constructor(private notifService: NotificacionService) {}

  ngOnInit(): void {
    this.nombreUsuario = localStorage.getItem('nombre') || 'Usuario';
    const rol = localStorage.getItem('rol') || 'taller';
    this.rolUsuario = rol.charAt(0).toUpperCase() + rol.slice(1);

    // ⚡ CARGA REAL INICIAL
    this.actualizarContador();
  }

  actualizarContador() {
    this.notifService.getNoLeidas().subscribe(res => {
      this.cantidadNoLeidas = res.total_no_leidas;
    });
  }

  toggleDropdown(event: Event): void {
    event.stopPropagation();
    this.mostrarDropdown = !this.mostrarDropdown;
    
    // Si abre el dropdown, cargamos la lista real
    if (this.mostrarDropdown) {
      this.notifService.getMisNotificaciones().subscribe(data => {
        this.notificaciones = data;
      });
    }
  }

  marcarLeida(notif: any, event: Event): void {
    event.stopPropagation();
    if (notif.leido_boolean) return;

    this.notifService.marcarComoLeida(notif.id_notificacion).subscribe(() => {
      notif.leido_boolean = true;
      this.actualizarContador();
    });
  }

  notificarToggle() { this.onToggle.emit(); }

  @HostListener('document:click')
  onDocumentClick() { this.mostrarDropdown = false; }
}