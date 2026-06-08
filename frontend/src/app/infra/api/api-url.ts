import { RUNTIME } from '../runtime/runtime';

export function apiUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${RUNTIME.apiBaseUrl}${normalized}`;
}
