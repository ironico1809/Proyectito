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
  
  rolUsuario: string = ''; 

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.rolUsuario = localStorage.getItem('rol') || 'taller';
  }
  
  toggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  cerrarSesion() {
    localStorage.removeItem('token'); 
    this.rolUsuario = localStorage.getItem('rol') || 'taller';
    this.router.navigate(['/login']); 
  }
}