import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { RUNTIME } from '../runtime/runtime';
import { TokenResponse } from '../api/auth.api';
import { SessionSnapshot } from './session.types';

@Injectable({ providedIn: 'root' })
export class SessionStore {
  private readonly subject = new BehaviorSubject<SessionSnapshot | null>(
    this.loadFromStorage(),
  );
  readonly session$ = this.subject.asObservable();

  snapshot(): SessionSnapshot | null {
    return this.subject.value;
  }

  isAuthenticated(): boolean {
    return !!this.subject.value?.token;
  }

  setFromLogin(response: TokenResponse): void {
    const next: SessionSnapshot = {
      token: response.access_token,
      tokenType: response.token_type,
      role: response.rol,
      displayName: response.nombre,
      userId: response.id_usuario,
      workshopId: response.id_taller ?? null,
    };

    localStorage.setItem(RUNTIME.sessionStorageKey, JSON.stringify(next));
    this.subject.next(next);
  }

  clear(): void {
    localStorage.removeItem(RUNTIME.sessionStorageKey);
    this.subject.next(null);
  }

  private loadFromStorage(): SessionSnapshot | null {
    try {
      const raw = localStorage.getItem(RUNTIME.sessionStorageKey);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as SessionSnapshot;
      if (!parsed?.token) return null;
      return parsed;
    } catch {
      return null;
    }
  }
}
