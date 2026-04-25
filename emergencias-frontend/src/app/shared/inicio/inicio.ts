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
  
  rolUsuario: string = ''; 

  constructor() {}

  ngOnInit(): void {
    this.rolUsuario = localStorage.getItem('rol') || 'taller';
  }
}