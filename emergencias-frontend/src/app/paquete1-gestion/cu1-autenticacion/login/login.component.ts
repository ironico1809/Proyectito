import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { TallerService } from '../../../core/services/taller'; // <--- Importamos el servicio del CU3

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
    private tallerService: TallerService, // <--- Lo inyectamos aquí
    private router: Router
  ) {
    this.iniciarFormulario();
  }

  iniciarFormulario() {
    if (this.isLoginMode) {
      // Formulario corto para Iniciar Sesión
      this.loginForm = this.fb.group({
        email: ['', [Validators.required, Validators.email]],
        password: ['', [Validators.required, Validators.minLength(6)]]
      });
    } else {
      // Formulario largo para Registrar un Taller (Basado en TallerCreate del backend)
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
    this.iniciarFormulario(); // Reconstruye el formulario con los campos correctos
  }

  onSubmit() {
    if (this.loginForm.invalid) return;

    if (this.isLoginMode) {
      // Lógica de Iniciar Sesión (Se mantiene igual)
      this.authService.login(this.loginForm.value).subscribe({
        next: (res) => {
          alert('¡Hola ' + res.nombre + '!');
          this.router.navigate(['/inicio']);
        },
        error: (err) => alert('Correo o contraseña incorrectos')
      });
    } else {
      // Lógica de Registrar Taller (CU3)
      this.tallerService.crearTaller(this.loginForm.value).subscribe({
        next: (res) => {
          alert('¡Taller registrado exitosamente! Ahora puedes iniciar sesión.');
          this.toggleMode(); // Lo devolvemos a la vista de login
        },
        error: (err) => alert('Error al registrar el taller: ' + err.error?.detail)
      });
    }
  }
}