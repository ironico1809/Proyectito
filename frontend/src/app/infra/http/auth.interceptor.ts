import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { SessionStore } from '../session/session.store';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const session = inject(SessionStore).snapshot();
  if (!session?.token) return next(req);

  return next(
    req.clone({
      setHeaders: {
        Authorization: `Bearer ${session.token}`,
      },
    }),
  );
};
