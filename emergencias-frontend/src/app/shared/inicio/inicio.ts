import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { Sidebar } from '../sidebar/sidebar'; // 👈 agrega esta línea

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [CommonModule, RouterModule, Sidebar],
  templateUrl: './inicio.html',
  styleUrl: './inicio.css'
})
export class Inicio {
  isSidebarOpen = false;

  constructor(private router: Router) {}

  toggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  // Agrega tu lógica de logout aquí si usas AuthService
  cerrarSesion() {
    // 1. Borramos el token para que el backend ya no lo deje pasar
    localStorage.removeItem('token'); 
    
    // 2. Lo enviamos a la ruta de login
    this.router.navigate(['/login']);
  }
}