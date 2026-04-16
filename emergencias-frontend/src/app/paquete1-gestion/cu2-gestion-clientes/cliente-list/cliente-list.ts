import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms'; // <--- 1. Importante importar esto
import { UsuarioService } from '../../../core/services/usuario';
import { Usuario } from '../../../shared/models/usuario.model';
import { Sidebar } from '../../../shared/sidebar/sidebar';

@Component({
  selector: 'app-cliente-list',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, Sidebar],
  templateUrl: './cliente-list.html',
  styleUrl: './cliente-list.css' // <--- FÍJATE QUE ES styleUrl EN SINGULAR
})
export class ClienteList implements OnInit {
  usuarios: Usuario[] = [];
  cargando: boolean = true;
  error: string | null = null;
  
  // Variable para guardar los datos del usuario que estamos editando en ese momento
  usuarioEditando: any = null; 

  constructor(private usuarioService: UsuarioService) {}

  ngOnInit(): void {
    this.cargarUsuarios();
  }

  cargarUsuarios() {
    this.usuarioService.getUsuarios().subscribe({
      next: (datos) => {
        this.usuarios = datos;
        this.cargando = false;
      },
      error: (err) => {
        this.error = "Error al cargar usuarios.";
        this.cargando = false;
      }
    });
  }

  // --- NUEVAS FUNCIONES ---

  eliminarUsuario(id: number, nombre: string) {
    // Alerta nativa para confirmar antes de borrar
    if (confirm(`¿Estás súper seguro de eliminar a ${nombre}?`)) {
      this.usuarioService.deleteUsuario(id).subscribe({
        next: () => {
          alert('Usuario eliminado correctamente');
          this.cargarUsuarios(); // Recarga la tabla automáticamente
        },
        error: (err) => alert('Error al eliminar: ' + err.error?.detail)
      });
    }
  }

  abrirEditar(user: Usuario) {
    // Hacemos una copia del usuario para no modificar la tabla en vivo hasta que demos "Guardar"
    this.usuarioEditando = { ...user };
  }

  guardarEdicion() {
    const id = this.usuarioEditando.id_usuario;
    
    // Empaquetamos solo los datos que queremos permitir editar
    const datosUpdate = {
      nombre: this.usuarioEditando.nombre,
      telefono: this.usuarioEditando.telefono,
      rol: this.usuarioEditando.rol
    };

    this.usuarioService.updateUsuario(id, datosUpdate).subscribe({
      next: () => {
        alert('Datos actualizados con éxito');
        this.usuarioEditando = null; // Cierra el formulario
        this.cargarUsuarios(); // Recarga la tabla
      },
      error: (err) => alert('Error al actualizar: ' + err.error?.detail)
    });
  }

  cancelarEdicion() {
    this.usuarioEditando = null; // Cierra el formulario sin guardar nada
  }
}