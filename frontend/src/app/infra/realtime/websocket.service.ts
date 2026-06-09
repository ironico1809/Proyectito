import { Injectable, OnDestroy } from '@angular/core';
import { Subject, Observable } from 'rxjs';
import { RUNTIME } from '../runtime/runtime';

export interface WsMessage {
  tipo: string;
  [key: string]: any;
}

@Injectable({ providedIn: 'root' })
export class WebSocketService implements OnDestroy {
  private socket: WebSocket | null = null;
  private messageSubject = new Subject<WsMessage>();
  private reconnectTimer: any = null;
  private pingTimer: any = null;
  private retryCount = 0;
  private maxRetries = 10;
  private currentUrl = '';
  private intentionalClose = false;

  readonly messages$: Observable<WsMessage> = this.messageSubject.asObservable();

  private get wsBaseUrl(): string {
    const apiUrl: string = RUNTIME.apiBaseUrl || 'http://127.0.0.1:8000';
    return apiUrl.replace(/^http/, 'ws');
  }

  connectGlobal(): void {
    this.connect(`${this.wsBaseUrl}/ws/sala-general`);
  }

  connectIncidente(id: number): void {
    this.connect(`${this.wsBaseUrl}/ws/incidente/${id}`);
  }

  private connect(url: string): void {
    this.intentionalClose = false;
    this.currentUrl = url;
    this.disconnect();
    this.intentionalClose = false;
    this._open(url);
  }

  private _open(url: string): void {
    try {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        this.retryCount = 0;
        this._startPing();
      };

      this.socket.onmessage = (event) => {
        try {
          const data: WsMessage = JSON.parse(event.data);
          this.messageSubject.next(data);
          this.showNativeNotification(data);
        } catch { /* ignore parse errors */ }
      };

      this.socket.onclose = () => {
        this._stopPing();
        if (!this.intentionalClose) {
          this._scheduleReconnect();
        }
      };

      this.socket.onerror = () => {
        this.socket?.close();
      };
    } catch { /* ignore connection errors */ }
  }

  send(data: object): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  private _scheduleReconnect(): void {
    if (this.retryCount >= this.maxRetries) return;
    this.retryCount++;
    const delay = Math.min(1000 * Math.pow(2, this.retryCount - 1), 30000);
    this.reconnectTimer = setTimeout(() => {
      if (!this.intentionalClose) {
        this._open(this.currentUrl);
      }
    }, delay);
  }

  private _startPing(): void {
    this._stopPing();
    this.pingTimer = setInterval(() => {
      this.send({ tipo: 'ping' });
    }, 25000);
  }

  private _stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  disconnect(): void {
    this.intentionalClose = true;
    this._stopPing();
    clearTimeout(this.reconnectTimer);
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  private showNativeNotification(data: WsMessage): void {
    if (typeof window === 'undefined' || !('Notification' in window)) return;

    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    if (Notification.permission !== 'granted') return;

    let title = '';
    let body = '';
    let isHighPriority = false;

    // Obtener rol del usuario desde localStorage si es posible, o asumimos que podría ser técnico
    let userRole = 'desconocido';
    try {
      const session = localStorage.getItem('session');
      if (session) {
        userRole = JSON.parse(session).role;
      }
    } catch (e) {}

    if (data.tipo === 'nuevo_incidente') {
      title = `🚨 Nueva Emergencia #${data['id_incidente']}`;
      body = `Prioridad: ${data['prioridad'] || 'pendiente'}\n${data['descripcion'] || 'Sin descripción'}`;
      isHighPriority = true; // Solo alertas fuertes para incidentes nuevos
    } else if (data.tipo === 'cambio_estado') {
      // Filtrar notificaciones de cambio de estado para técnicos, a menos que el mensaje diga específicamente que fue asignado.
      if (userRole === 'tecnico' && data['estado'] !== 'en_proceso') {
          // El técnico está cambiando sus propios estados, no necesita notificación nativa para esto
          return; 
      }
      
      title = `⚙️ Estado de Auxilio: ${data['estado']?.toUpperCase()}`;
      body = data['mensaje'] || `El incidente #${data['id_incidente'] || ''} cambió a estado: ${data['estado']}`;
    } else if (data.tipo === 'nueva_cotizacion') {
      title = `💰 Nueva Cotización Recibida`;
      body = `El taller ${data['taller_nombre']} envió cotización de Bs. ${data['precio']}.`;
    }

    if (title) {
      try {
        new Notification(title, {
          body: body,
          icon: '/favicon.ico'
        });
        
        if (isHighPriority) {
          this.playNotificationSound();
        }
      } catch (e) {
        console.error('Error mostrando notificación HTML5:', e);
      }
    }
  }

  private playNotificationSound(): void {
    try {
      // Soft chime sound
      const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/911/911-84.wav');
      audio.volume = 0.4;
      audio.play();
    } catch { /* ignore audio errors */ }
  }

  ngOnDestroy(): void {
    this.disconnect();
    this.messageSubject.complete();
  }
}
