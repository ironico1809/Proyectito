import { CanActivateFn, Router, ActivatedRouteSnapshot } from '@angular/router';
import { inject } from '@angular/core';
import { SessionStore } from '../session/session.store';

export const portalGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const store = inject(SessionStore);
  const snapshot = store.snapshot();
  
  if (store.isAuthenticated()) {
    if (snapshot?.role === 'superadmin') {
      return inject(Router).parseUrl('/superadmin');
    }
    
    // Check if route has role constraints
    const allowedRoles = route.data?.['roles'] as string[];
    if (allowedRoles && snapshot?.role) {
      if (!allowedRoles.includes(snapshot.role)) {
        // Redirect to panel home if unauthorized
        return inject(Router).parseUrl('/panel/resumen');
      }
    }
    
    return true;
  }

  return inject(Router).parseUrl('/acceso');
};
