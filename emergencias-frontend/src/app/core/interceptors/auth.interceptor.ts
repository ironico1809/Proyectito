import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // Buscamos el token que guardamos al iniciar sesión
  const token = localStorage.getItem('token');

  // Si hay token, clonamos la petición y le pegamos el header de Autorización
  if (token) {
    const peticionClonada = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    return next(peticionClonada);
  }

  // Si no hay token (ej. al hacer login), la dejamos pasar normal
  return next(req);
};