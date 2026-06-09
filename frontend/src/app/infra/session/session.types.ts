export type UserRole = 'cliente' | 'taller' | 'tecnico' | 'admin' | string;

export interface SessionSnapshot {
  token: string;
  tokenType: string;
  role: UserRole;
  displayName: string;
  userId: number;
  workshopId: number | null;
  tenantId: number | null;
}
