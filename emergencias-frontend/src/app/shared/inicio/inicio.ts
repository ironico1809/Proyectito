// src/app/shared/inicio/inicio.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './inicio.html',
  styleUrls: ['./inicio.css']
})
export class Inicio implements OnInit {
  
  // La variable inicia vacía
  rolUsuario: string = ''; 

  constructor() {}

  ngOnInit(): void {
    // ⚡ AQUÍ ESTÁ LA MAGIA: Leemos el rol real.
    // Angular mostrará automáticamente las tarjetas de Admin o Taller según lo que encuentre aquí.
    this.rolUsuario = localStorage.getItem('rol') || 'taller';
  }
}