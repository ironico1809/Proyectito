import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cu4-perfil.html',
  styleUrls: ['./cu4-perfil.css']
})
export class Cu4Perfil implements OnInit {
  // Datos reales del usuario
  usuario = { 
    nombre: localStorage.getItem('nombre') || '', 
    email: '', 
    telefono: '', 
    rol: localStorage.getItem('rol') || '' 
  };
  
  cargando = false;
  mensaje = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.obtenerDatosCompletos();
  }

  obtenerDatosCompletos() {
    // Usamos el endpoint /me que ya configuramos en FastAPI
    this.http.get<any>('http://localhost:8000/usuarios/me').subscribe({
      next: (res) => this.usuario = res,
      error: (err) => console.error("Error al traer perfil", err)
    });
  }

  actualizar() {
    this.cargando = true;
    this.http.put('http://localhost:8000/usuarios/me', this.usuario).subscribe({
      next: () => {
        this.cargando = false;
        this.mensaje = "¡Perfil actualizado! ✅";
        localStorage.setItem('nombre', this.usuario.nombre); // Actualizamos el nombre en el navegador
        setTimeout(() => this.mensaje = '', 3000);
      },
      error: () => {
        this.cargando = false;
        alert("Error al actualizar datos.");
      }
    });
  }
}