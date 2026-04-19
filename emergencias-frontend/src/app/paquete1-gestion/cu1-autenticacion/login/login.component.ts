import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { TallerService } from '../../../core/services/taller';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  loginForm!: FormGroup;
  isLoginMode = true;

  constructor(
    private fb: FormBuilder, 
    private authService: AuthService,
    private tallerService: TallerService,
    private router: Router
  ) {
    this.iniciarFormulario();
  }

  iniciarFormulario() {
    if (this.isLoginMode) {
      this.loginForm = this.fb.group({
        email: ['', [Validators.required, Validators.email]],
        password: ['', [Validators.required, Validators.minLength(6)]]
      });
    } else {
      this.loginForm = this.fb.group({
        nombre_dueno: ['', Validators.required],
        email: ['', [Validators.required, Validators.email]],
        password: ['', [Validators.required, Validators.minLength(6)]],
        telefono: [''],
        nombre_taller: ['', Validators.required],
        direccion: [''],
        nit: ['']
      });
    }
  }

  toggleMode() {
    this.isLoginMode = !this.isLoginMode;
    this.iniciarFormulario();
  }

  onSubmit() {
    if (this.loginForm.invalid) return;

    if (this.isLoginMode) {
      // ========================================================
      // ⚡ LÓGICA DE LOGIN (AQUÍ GUARDAMOS EL ROL) ⚡
      // ========================================================
      this.authService.login(this.loginForm.value).subscribe({
        next: (res: any) => {
          // 1. Guardamos el token (Soporta si tu backend manda access_token o token)
          localStorage.setItem('token', res.access_token || res.token);
          
          // 2. Guardamos el rol para que el Sidebar y Dashboard se adapten
          // Nota: Si tu backend devuelve el rol bajo otro nombre como 'rol_enum', 
          // cambiaselo aquí abajo a res.rol_enum
          localStorage.setItem('rolUsuario', res.rol);
          
          // 3. Nos vamos al Dashboard
          this.router.navigate(['/inicio']);
        },
        error: (err) => alert('Correo o contraseña incorrectos')
      });
    } else {
      // ========================================================
      // ⚡ LÓGICA DE REGISTRO DE TALLER (CU3) ⚡
      // ========================================================
      this.tallerService.crearTaller(this.loginForm.value).subscribe({
        next: (res) => {
          alert('¡Taller registrado exitosamente! Ahora puedes iniciar sesión.');
          this.toggleMode(); 
        },
        error: (err) => alert('Error al registrar: ' + (err.error?.detail || 'Verifique sus datos'))
      });
    }
  }
}