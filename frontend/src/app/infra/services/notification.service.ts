import { Injectable, PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';
import { environment } from '../../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { apiUrl } from '../api/api-url';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private messaging: any;

  constructor(
    private http: HttpClient,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    if (isPlatformBrowser(this.platformId)) {
      try {
        const app = initializeApp(environment.firebase);
        this.messaging = getMessaging(app);
        this.listenForMessages();
      } catch (e) {
        console.error('Error inicializando Firebase:', e);
      }
    }
  }

  async requestPermissionAndGetToken() {
    if (!isPlatformBrowser(this.platformId)) return;

    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        const token = await getToken(this.messaging, {
          vapidKey: environment.vapidKey
        });
        
        if (token) {
          console.log('FCM Web Token obtenido correctamente');
          this.sendTokenToServer(token);
        } else {
          console.warn('No se pudo obtener el token de FCM.');
        }
      } else {
        console.warn('El usuario bloqueó las notificaciones.');
      }
    } catch (error) {
      console.error('Error al pedir permiso de notificaciones:', error);
    }
  }

  private sendTokenToServer(token: string) {
    this.http.patch(apiUrl('/usuarios/fcm-token'), { fcm_token: token })
      .subscribe({
        next: () => console.log('Token FCM Web registrado en el servidor.'),
        error: (err) => console.error('Error registrando token FCM en el servidor:', err)
      });
  }

  private listenForMessages() {
    if (!isPlatformBrowser(this.platformId)) return;

    onMessage(this.messaging, (payload: any) => {
      console.log('Notificación recibida en primer plano:', payload);
      
      const title = payload.notification?.title || 'Nueva Notificación';
      const body = payload.notification?.body || '';

      if (Notification.permission === 'granted') {
        new Notification(title, {
          body: body,
          icon: '/favicon.ico'
        });
      }
    });
  }
}
