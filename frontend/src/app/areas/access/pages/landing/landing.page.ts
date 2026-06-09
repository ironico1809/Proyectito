import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthApi } from '../../../../infra/api/auth.api';
import { SessionStore } from '../../../../infra/session/session.store';
import { NotificationService } from '../../../../infra/services/notification.service';

@Component({
  selector: 'ev-landing-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './landing.page.html',
  styleUrl: './landing.page.css',
})
export class LandingPage {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApi);
  private readonly session = inject(SessionStore);
  private readonly router = inject(Router);
  private readonly notificationService = inject(NotificationService);

  showModal = false;
  currentStep = 1;
  selectedPlan = '';
  selectedPrice = 0;
  isBusy = false;
  errorText: string | null = null;

  readonly form = this.fb.group({
    nombre_empresa: ['', Validators.required],
    descripcion_empresa: [''],
    admin_nombre: ['', Validators.required],
    admin_email: ['', [Validators.required, Validators.email]],
    admin_password: ['', [Validators.required, Validators.minLength(6)]],
    admin_telefono: [''],
  });

  openCheckout(planName: string, price: number): void {
    this.selectedPlan = planName;
    this.selectedPrice = price;
    this.showModal = true;
    this.currentStep = 1;
    this.errorText = null;
    this.form.reset();
  }

  closeCheckout(): void {
    if (!this.isBusy) {
      this.showModal = false;
    }
  }

  nextStep(): void {
    if (this.currentStep === 1 && this.form.get('nombre_empresa')?.invalid) {
      return;
    }
    if (this.currentStep === 2 && (
      this.form.get('admin_nombre')?.invalid ||
      this.form.get('admin_email')?.invalid ||
      this.form.get('admin_password')?.invalid
    )) {
      return;
    }
    this.currentStep++;
  }

  prevStep(): void {
    this.currentStep--;
  }

  submit(): void {
    if (this.form.invalid) return;

    this.isBusy = true;
    this.errorText = null;

    const raw = this.form.getRawValue();
    const payload = {
      nombre_empresa: raw.nombre_empresa ?? '',
      descripcion_empresa: raw.descripcion_empresa ?? '',
      admin_nombre: raw.admin_nombre ?? '',
      admin_email: raw.admin_email ?? '',
      admin_password: raw.admin_password ?? '',
      admin_telefono: raw.admin_telefono ?? '',
    };

    // Call saas.py registration endpoint
    this.authApi
      .registroSaaS(payload)
      .pipe(finalize(() => (this.isBusy = false)))
      .subscribe({
        next: (res) => {
          this.session.setFromLogin(res);
          this.notificationService.requestPermissionAndGetToken();
          this.showModal = false;
          this.router.navigateByUrl('/panel');
        },
        error: (err) => {
          const detail = err?.error?.detail;
          this.errorText =
            typeof detail === 'string' ? detail : 'Error al registrar la empresa. Intente nuevamente.';
        },
      });
  }
}
