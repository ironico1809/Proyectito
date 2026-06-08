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
    // DESACTIVADO EN EL PORTAL WEB: Para optimizar rendimiento y dejar el WebSocket exclusivo para el móvil.
    console.log('WebSocket de la web omitido/desactivado:', url);
    return;
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

  ngOnDestroy(): void {
    this.disconnect();
    this.messageSubject.complete();
  }
}
