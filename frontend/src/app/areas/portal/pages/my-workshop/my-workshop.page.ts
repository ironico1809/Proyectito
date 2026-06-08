import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject, catchError, combineLatest, of, switchMap } from 'rxjs';
import { TalleresApi, TallerOut } from '../../../../infra/api/talleres.api';
import { SessionStore } from '../../../../infra/session/session.store';

@Component({
  selector: 'ev-my-workshop-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './my-workshop.page.html',
  styleUrl: './my-workshop.page.css',
})
export class MyWorkshopPage {
  private readonly api = inject(TalleresApi);
  readonly session = inject(SessionStore);

  readonly refresh$ = new BehaviorSubject<void>(undefined);

  readonly taller$ = combineLatest([this.session.session$, this.refresh$]).pipe(
    switchMap(([session]) => {
      if (!session) return of(null);
      return this.api.obtenerMiTaller().pipe(catchError(() => of(null)));
    })
  );

  editing = false;
  formData = { nombre_taller: '', direccion: '', nit: '', telefono_dueno: '', nombre_dueno: '' };
  ubicacion = { latitud: '', longitud: '' };
  saving = false;
  saved = false;

  startEdit(t: TallerOut) {
    this.editing = true;
    this.formData = {
      nombre_taller: t.nombre_taller,
      direccion: t.direccion || '',
      nit: t.nit || '',
      telefono_dueno: t.telefono_dueno || '',
      nombre_dueno: t.nombre_dueno,
    };
    this.ubicacion = {
      latitud: t.latitud_decimal || '',
      longitud: t.longitud_decimal || '',
    };
  }

  cancelEdit() {
    this.editing = false;
  }

  saveEdit(t: TallerOut) {
    this.saving = true;
    this.saved = false;
    this.api.actualizar(t.id_taller, this.formData).subscribe(() => {
      if (this.ubicacion.latitud && this.ubicacion.longitud) {
        this.api.actualizarUbicacion({
          latitud: this.ubicacion.latitud,
          longitud: this.ubicacion.longitud,
        }).subscribe(() => {
          this.saving = false;
          this.saved = true;
          this.editing = false;
          setTimeout(() => { this.saved = false; this.refresh$.next(); }, 1500);
        });
      } else {
        this.saving = false;
        this.saved = true;
        this.editing = false;
        setTimeout(() => { this.saved = false; this.refresh$.next(); }, 1500);
      }
    });
  }
}
