import { Component, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router } from '@angular/router';
import { Sidebar } from './shared/sidebar/sidebar'; 
import { NavbarComponent } from './shared/navbar/navbar'; 

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, Sidebar, NavbarComponent],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App { 
  // Si la pantalla es menor a 768px (móvil), inicia oculto (true)
  sidebarColapsado = window.innerWidth <= 768; 

  constructor(public router: Router) {}

  toggleSidebar() {
    this.sidebarColapsado = !this.sidebarColapsado;
  }

  // Escucha si el usuario redimensiona la ventana
  @HostListener('window:resize')
  onResize() {
    this.sidebarColapsado = window.innerWidth <= 768;
  }
}