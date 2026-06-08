import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { SessionStore } from '../session/session.store';

export const authGuard: CanActivateFn = () => {
  const store = inject(SessionStore);
  if (store.isAuthenticated()) return true;

  return inject(Router).parseUrl('/acceso');
};
