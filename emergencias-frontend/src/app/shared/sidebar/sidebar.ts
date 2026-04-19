// src/app/shared/sidebar/sidebar.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css']
})
export class Sidebar implements OnInit {
  isSidebarOpen = false;
  
  // La variable inicia vacía
  rolUsuario: string = ''; 

  constructor(private router: Router) {}

  ngOnInit(): void {
    // ⚡ AQUÍ ESTÁ LA MAGIA: Leemos el rol real guardado en el navegador.
    // (Ponemos 'taller' como valor por defecto por si acaso entra directo sin login por ahora)
    this.rolUsuario = localStorage.getItem('rol') || 'taller';
  }
  
  toggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  cerrarSesion() {
    // Es vital borrar TODO al salir para que no se quede pegada la vista anterior
    localStorage.removeItem('token'); 
    this.rolUsuario = localStorage.getItem('rol') || 'taller';
    this.router.navigate(['/login']); 
  }
}