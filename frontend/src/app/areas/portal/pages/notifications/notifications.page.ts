import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { catchError, of } from 'rxjs';
import { NotificacionesApi, NotificacionOut } from '../../../../infra/api/notificaciones.api';

@Component({
  selector: 'ev-notifications-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notifications.page.html',
  styleUrl: './notifications.page.css',
})
export class NotificationsPage {
  private readonly api = inject(NotificacionesApi);

  readonly notifications$ = this.api.misNotificaciones().pipe(catchError(() => of([] as NotificacionOut[])));

  marcarLeida(n: NotificacionOut) {
    if (n.leido_boolean) return;
    this.api.marcarLeida(n.id_notificacion).subscribe(() => {
      n.leido_boolean = true;
    });
  }

  marcarTodasLeidas() {
    this.notifications$.subscribe((items) => {
      items.filter((n) => !n.leido_boolean).forEach((n) => {
        this.api.marcarLeida(n.id_notificacion).subscribe(() => {
          n.leido_boolean = true;
        });
      });
    });
  }
}
