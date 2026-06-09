import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthApi } from '../../../../infra/api/auth.api';
import { SessionStore } from '../../../../infra/session/session.store';
import { NotificationService } from '../../../../infra/services/notification.service';

@Component({
  selector: 'ev-login-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './login.page.html',
  styleUrl: './login.page.css',
})
export class LoginPage {
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApi);
  private readonly session = inject(SessionStore);
  private readonly router = inject(Router);
  private readonly notificationService = inject(NotificationService);

  isBusy = false;
  errorText: string | null = null;

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  submit(): void {
    this.errorText = null;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isBusy = true;
    const { email, password } = this.form.getRawValue();

    this.authApi
      .login({ email, password })
      .pipe(finalize(() => (this.isBusy = false)))
      .subscribe({
        next: (token) => {
          this.session.setFromLogin(token);
          this.notificationService.requestPermissionAndGetToken();
          if (token.rol === 'superadmin') {
            this.router.navigateByUrl('/superadmin');
          } else {
            this.router.navigateByUrl('/panel');
          }
        },
        error: (err) => {
          const detail = err?.error?.detail;
          this.errorText =
            typeof detail === 'string' ? detail : 'Credenciales incorrectas';
        },
      });
  }
}
