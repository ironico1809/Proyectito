import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http'; // <--- Añadir withInterceptors

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor'; // <--- Importar el interceptor

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    // Así le decimos a Angular que use nuestro interceptor
    provideHttpClient(withInterceptors([authInterceptor])) 
  ]
};