import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject, catchError, combineLatest, of, switchMap } from 'rxjs';
import { PagosApi } from '../../../../infra/api/pagos.api';
import { SessionStore } from '../../../../infra/session/session.store';

@Component({
  selector: 'ev-payments-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './payments.page.html',
  styleUrl: './payments.page.css',
})
export class PaymentsPage {
  private readonly api = inject(PagosApi);
  private readonly session = inject(SessionStore);

  readonly refresh$ = new BehaviorSubject<void>(undefined);

  readonly pagos$ = combineLatest([this.session.session$, this.refresh$]).pipe(
    switchMap(() => this.api.listarTodos()),
    catchError(() => of([])),
  );

  showForm = false;
  formData = { incidente_id: 0, monto_total_decimal: 0, comision_plataforma_decimal: 0, metodo_enum: 'qr' };

  openForm() {
    this.showForm = true;
    this.formData = { incidente_id: 0, monto_total_decimal: 0, comision_plataforma_decimal: 0, metodo_enum: 'qr' };
  }

  closeForm() {
    this.showForm = false;
  }

  createPayment() {
    if (!this.formData.incidente_id || !this.formData.monto_total_decimal) return;
    this.api.crear({
      incidente_id: this.formData.incidente_id,
      monto_total_decimal: this.formData.monto_total_decimal,
      comision_plataforma_decimal: this.formData.comision_plataforma_decimal,
      metodo_enum: this.formData.metodo_enum,
    }).subscribe(() => {
      this.showForm = false;
      this.refresh$.next();
    });
  }
}
