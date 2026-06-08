import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { SessionStore } from '../../../../infra/session/session.store';
import { RUNTIME } from '../../../../infra/runtime/runtime';

@Component({
  selector: 'ev-profile-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './profile.page.html',
  styleUrl: './profile.page.css',
})
export class ProfilePage {
  private readonly http = inject(HttpClient);
  private readonly session = inject(SessionStore);

  readonly session$ = this.session.session$;

  usuario = {
    nombre: localStorage.getItem('nombre') || '',
    telefono: '',
  };

  cargando = false;
  mensaje = '';
  mostrarMensaje = false;

  actualizar(): void {
    this.cargando = true;
    this.mostrarMensaje = false;

    const token = this.session.snapshot()?.token;
    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    });

    this.http
      .put(`${RUNTIME.apiBaseUrl}/usuarios/me`, this.usuario, { headers })
      .subscribe({
        next: () => {
          this.cargando = false;
          this.mensaje = 'Perfil actualizado correctamente';
          this.mostrarMensaje = true;
          localStorage.setItem('nombre', this.usuario.nombre);
          setTimeout(() => (this.mostrarMensaje = false), 3000);
        },
        error: () => {
          this.cargando = false;
          this.mensaje = 'Error al actualizar perfil';
          this.mostrarMensaje = true;
          setTimeout(() => (this.mostrarMensaje = false), 3000);
        },
      });
  }

  getUserInitial(name: string): string {
    return name?.charAt(0)?.toUpperCase() || 'U';
  }
}
