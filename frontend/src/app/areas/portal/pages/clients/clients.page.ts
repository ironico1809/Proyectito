import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject, catchError, combineLatest, of, switchMap } from 'rxjs';
import { UsuariosApi, UsuarioOut } from '../../../../infra/api/usuarios.api';
import { SessionStore } from '../../../../infra/session/session.store';

@Component({
  selector: 'ev-clients-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './clients.page.html',
  styleUrl: './clients.page.css',
})
export class ClientsPage {
  private readonly api = inject(UsuariosApi);
  readonly session = inject(SessionStore);

  readonly refresh$ = new BehaviorSubject<void>(undefined);

  readonly usuarios$ = combineLatest([this.session.session$, this.refresh$]).pipe(
    switchMap(() => this.api.listar().pipe(catchError(() => of([] as UsuarioOut[]))))
  );

  editingId: number | null = null;
  editData: { nombre: string; telefono: string; rol: string } = { nombre: '', telefono: '', rol: '' };

  startEdit(u: UsuarioOut) {
    this.editingId = u.id_usuario;
    this.editData = { nombre: u.nombre, telefono: u.telefono || '', rol: u.rol };
  }

  cancelEdit() {
    this.editingId = null;
  }

  saveEdit(id: number) {
    this.api.actualizarParcial(id, this.editData).subscribe(() => {
      this.editingId = null;
      this.refresh$.next();
    });
  }

  deleteUser(id: number, name: string) {
    if (confirm(`¿Eliminar a "${name}"? Esta acción no se puede deshacer.`)) {
      this.api.eliminar(id).subscribe(() => {
        this.refresh$.next();
      });
    }
  }

  getRolColor(rol: string): string {
    const map: Record<string, string> = {
      admin: 'var(--danger)',
      taller: 'var(--orange-500)',
      tecnico: 'var(--info)',
      cliente: 'var(--success)',
    };
    return map[rol] || 'var(--text-muted)';
  }
}
