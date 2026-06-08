import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject, catchError, combineLatest, of, switchMap } from 'rxjs';
import { UsuariosApi, UsuarioOut } from '../../../../infra/api/usuarios.api';
import { SessionStore } from '../../../../infra/session/session.store';

@Component({
  selector: 'ev-users-management-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './users-management.page.html',
  styleUrl: './users-management.page.css',
})
export class UsersManagementPage {
  private readonly api = inject(UsuariosApi);
  readonly session = inject(SessionStore);

  readonly refresh$ = new BehaviorSubject<void>(undefined);

  readonly usuarios$ = combineLatest([this.session.session$, this.refresh$]).pipe(
    switchMap(() => this.api.listar().pipe(catchError(() => of([] as UsuarioOut[]))))
  );

  showForm = false;
  isEditing = false;
  formData = { nombre: '', email: '', password: '', telefono: '', rol: 'cliente' };

  editingId: number | null = null;

  getRolColor(rol: string): string {
    const map: Record<string, string> = {
      admin: 'var(--danger)',
      taller: 'var(--orange-500)',
      tecnico: 'var(--info)',
      cliente: 'var(--success)',
    };
    return map[rol] || 'var(--text-muted)';
  }

  openForm() {
    this.showForm = true;
    this.isEditing = false;
    this.formData = { nombre: '', email: '', password: '', telefono: '', rol: 'cliente' };
  }

  closeForm() {
    this.showForm = false;
  }

  saveForm() {
    if (this.isEditing && this.editingId !== null) {
      const updateData: any = {
        nombre: this.formData.nombre,
        email: this.formData.email,
        telefono: this.formData.telefono,
        rol: this.formData.rol
      };
      if (this.formData.password && this.formData.password.trim() !== '') {
        updateData.password = this.formData.password;
      }
      this.api.actualizarParcial(this.editingId, updateData).subscribe(() => {
        this.showForm = false;
        this.refresh$.next();
      });
    } else {
      if (!this.formData.nombre || !this.formData.email || !this.formData.password) return;
      this.api.crear(this.formData).subscribe(() => {
        this.showForm = false;
        this.refresh$.next();
      });
    }
  }

  startEdit(u: UsuarioOut) {
    this.editingId = u.id_usuario;
    this.isEditing = true;
    this.formData = { nombre: u.nombre, email: u.email, password: '', telefono: u.telefono || '', rol: u.rol };
    this.showForm = true;
  }

  deleteUser(id: number, name: string) {
    if (confirm(`¿Eliminar a "${name}"? Esta acción no se puede deshacer.`)) {
      this.api.eliminar(id).subscribe(() => {
        this.refresh$.next();
      });
    }
  }
}
