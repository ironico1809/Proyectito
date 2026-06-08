import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BehaviorSubject, catchError, combineLatest, of, switchMap } from 'rxjs';
import { TalleresApi, TallerOut } from '../../../../infra/api/talleres.api';

@Component({
  selector: 'ev-workshops-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './workshops.page.html',
  styleUrl: './workshops.page.css',
})
export class WorkshopsPage {
  private readonly api = inject(TalleresApi);

  readonly refresh$ = new BehaviorSubject<void>(undefined);

  readonly talleres$ = this.refresh$.pipe(
    switchMap(() => this.api.listar().pipe(catchError(() => of([] as TallerOut[]))))
  );

  deleteWorkshop(id: number, name: string) {
    if (confirm(`¿Eliminar el taller "${name}"? Se eliminará también el usuario dueño.`)) {
      this.api.eliminar(id).subscribe(() => {
        this.refresh$.next();
      });
    }
  }

  hasCoords(t: TallerOut): boolean {
    return !!(t.latitud_decimal && t.longitud_decimal);
  }
}
