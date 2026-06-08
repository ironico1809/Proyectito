import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject, combineLatest, catchError, of, switchMap } from 'rxjs';
import { TecnicosApi, TecnicoOut } from '../../../../infra/api/tecnicos.api';
import { TalleresApi } from '../../../../infra/api/talleres.api';
import { SessionStore } from '../../../../infra/session/session.store';

@Component({
  selector: 'ev-technicians-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './technicians.page.html',
  styleUrl: './technicians.page.css',
})
export class TechniciansPage {
  private readonly tecnicosApi = inject(TecnicosApi);
  private readonly talleresApi = inject(TalleresApi);
  private readonly session = inject(SessionStore);

  readonly session$ = this.session.session$;

  tallerId: number | null = null;
  isAdmin = false;
  talleresDisponibles: any[] = [];

  readonly refresh$ = new BehaviorSubject<void>(undefined);

  readonly tecnicos$ = combineLatest([this.session$, this.refresh$]).pipe(
    switchMap(([session]) => {
      if (!session) return of([] as TecnicoOut[]);
      this.isAdmin = true; // Forzamos true temporalmente para habilitar creación
      this.talleresApi.listar().subscribe(t => this.talleresDisponibles = t);
      return this.tecnicosApi.listarTodos().pipe(catchError(() => of([] as TecnicoOut[])));
    }),
    catchError(() => of([] as TecnicoOut[]))
  );

  showForm = false;
  isEditing = false;
  editingId: number | null = null;
  formData = { nombre: '', email: '', password: '', telefono: '', especialidad: '', taller_id: '' };

  openForm(tecnico?: TecnicoOut) {
    this.showForm = true;
    if (tecnico) {
      this.isEditing = true;
      this.editingId = tecnico.id_tecnico;
      this.formData = {
        nombre: tecnico.nombre,
        email: '',
        password: '',
        telefono: '',
        especialidad: tecnico.especialidad || '',
        taller_id: tecnico.taller_id.toString()
      };
    } else {
      this.isEditing = false;
      this.editingId = null;
      this.formData = { nombre: '', email: '', password: '', telefono: '', especialidad: '', taller_id: '' };
    }
  }

  closeForm() {
    this.showForm = false;
  }

  saveTechnician() {
    if (this.isEditing && this.editingId) {
      if (!this.formData.nombre) return;
      this.tecnicosApi.actualizarParcial(this.editingId, {
        nombre: this.formData.nombre,
        especialidad: this.formData.especialidad || undefined,
      }).subscribe(() => {
        this.showForm = false;
        this.refresh$.next();
      });
    } else {
      const finalTallerId = this.isAdmin ? this.formData.taller_id : this.tallerId;
      if (!finalTallerId || !this.formData.nombre || !this.formData.email || !this.formData.password) return;
      this.tecnicosApi.crear({
        taller_id: Number(finalTallerId),
        nombre: this.formData.nombre,
        email: this.formData.email,
        password: this.formData.password,
        telefono: this.formData.telefono || undefined,
        especialidad: this.formData.especialidad || undefined,
        disponible_boolean: true,
      }).subscribe(() => {
        this.showForm = false;
        this.refresh$.next();
      });
    }
  }

  toggleDisponibilidad(t: TecnicoOut) {
    this.tecnicosApi.actualizarParcial(t.id_tecnico, {
      disponible_boolean: !t.disponible_boolean,
    }).subscribe(() => {
      this.refresh$.next();
    });
  }

  deleteTechnician(t: TecnicoOut) {
    if (confirm(`¿Eliminar al técnico "${t.nombre}"?`)) {
      this.tecnicosApi.eliminar(t.id_tecnico).subscribe(() => {
        this.refresh$.next();
      });
    }
  }
}
