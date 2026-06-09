import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { SessionStore } from '../session/session.store';

export const superadminGuard: CanActivateFn = () => {
  const store = inject(SessionStore);
  const snapshot = store.snapshot();
  
  if (store.isAuthenticated() && snapshot?.role === 'superadmin') {
    return true;
  }

  // Redirect to login if not authorized
  return inject(Router).parseUrl('/acceso');
};
