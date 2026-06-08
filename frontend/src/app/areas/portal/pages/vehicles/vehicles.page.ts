import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject, catchError, combineLatest, of, switchMap } from 'rxjs';
import { VehiculosApi, VehiculoOut } from '../../../../infra/api/vehiculos.api';
import { SessionStore } from '../../../../infra/session/session.store';

@Component({
  selector: 'ev-vehicles-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './vehicles.page.html',
  styleUrl: './vehicles.page.css',
})
export class VehiclesPage {
  private readonly api = inject(VehiculosApi);
  readonly session = inject(SessionStore);

  readonly refresh$ = new BehaviorSubject<void>(undefined);

  readonly vehicles$ = combineLatest([this.session.session$, this.refresh$]).pipe(
    switchMap(() => this.api.listarMisVehiculos().pipe(catchError(() => of([] as VehiculoOut[]))))
  );

  showForm = false;
  formData = { placa: '', marca: '', modelo: '', color: '', usuario_id: 0 };

  editingId: number | null = null;
  editData = { placa: '', marca: '', modelo: '', color: '' };

  openForm(uid: number) {
    this.showForm = true;
    this.formData = { placa: '', marca: '', modelo: '', color: '', usuario_id: uid };
  }

  closeForm() {
    this.showForm = false;
  }

  createVehicle() {
    if (!this.formData.placa) return;
    this.api.crear(this.formData).subscribe(() => {
      this.showForm = false;
      this.refresh$.next();
    });
  }

  startEdit(v: VehiculoOut) {
    this.editingId = v.id_vehiculo;
    this.editData = { placa: v.placa, marca: v.marca || '', modelo: v.modelo || '', color: v.color || '' };
  }

  cancelEdit() {
    this.editingId = null;
  }

  saveEdit(id: number) {
    const data: Record<string, string> = {};
    if (this.editData.placa) data['placa'] = this.editData.placa;
    if (this.editData.marca) data['marca'] = this.editData.marca;
    if (this.editData.modelo) data['modelo'] = this.editData.modelo;
    if (this.editData.color) data['color'] = this.editData.color;
    this.api.actualizar(id, data).subscribe(() => {
      this.editingId = null;
      this.refresh$.next();
    });
  }

  deleteVehicle(id: number, placa: string) {
    if (confirm(`¿Eliminar vehículo "${placa}"?`)) {
      this.api.eliminar(id).subscribe(() => {
        this.refresh$.next();
      });
    }
  }
}
