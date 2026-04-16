import { Routes } from '@angular/router';
import { LoginComponent } from './paquete1-gestion/cu1-autenticacion/login/login.component';
import { Inicio } from './shared/inicio/inicio';
import { ClienteList } from './paquete1-gestion/cu2-gestion-clientes/cliente-list/cliente-list';
import { TallerList } from './paquete1-gestion/cu3-gestion-talleres/taller-list/taller-list'; // Asegúrate que el nombre de la clase sea el correcto

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'inicio', component: Inicio },
  { path: 'clientes', component: ClienteList },
  { path: 'talleres', component: TallerList }, // <--- DEBE ESTAR ANTES DE LOS ASTERISCOS
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: '**', redirectTo: 'login' }          // <--- LOS ASTERISCOS SIEMPRE AL FINAL
];