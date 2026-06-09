import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SaasApi } from '../../../../infra/api/saas.api';
import { shareReplay } from 'rxjs';

@Component({
  selector: 'ev-superadmin-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './superadmin-dashboard.page.html',
  styleUrl: './superadmin-dashboard.page.css',
})
export class SuperadminDashboardPage {
  private readonly saasApi = inject(SaasApi);

  readonly data$ = this.saasApi.obtenerDashboardGlobal().pipe(shareReplay(1));
}
