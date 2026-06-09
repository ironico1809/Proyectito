import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SaasApi, TenantStatItem } from '../../../../infra/api/saas.api';
import { BehaviorSubject, switchMap, shareReplay } from 'rxjs';

@Component({
  selector: 'ev-superadmin-tenants',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './superadmin-tenants.page.html',
  styleUrl: './superadmin-tenants.page.css',
})
export class SuperadminTenantsPage {
  private readonly saasApi = inject(SaasApi);

  readonly refreshTrigger$ = new BehaviorSubject<number>(0);
  isUpdatingId: number | null = null;

  readonly tenants$ = this.refreshTrigger$.pipe(
    switchMap(() => this.saasApi.listarTenants()),
    shareReplay(1)
  );

  toggleStatus(idTenant: number, currentEstado: string): void {
    const nextEstado = currentEstado === 'activo' ? 'suspendido' : 'activo';
    
    this.isUpdatingId = idTenant;
    this.saasApi.actualizarEstadoTenant(idTenant, nextEstado).subscribe({
      next: () => {
        this.isUpdatingId = null;
        this.refreshTrigger$.next(this.refreshTrigger$.value + 1);
      },
      error: (err) => {
        this.isUpdatingId = null;
        console.error('Error updating tenant status:', err);
      }
    });
  }
}
