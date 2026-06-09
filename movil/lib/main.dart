import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'config/app_theme.dart';
import 'services/storage_service.dart';
import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'providers/auth_provider.dart';
import 'providers/emergencia_provider.dart';
import 'providers/vehiculo_provider.dart';
import 'providers/notificacion_provider.dart';
import 'providers/taller_provider.dart';

// Screens
import 'screens/auth/login_screen.dart';
import 'screens/auth/register_screen.dart';
import 'screens/main_screen.dart';
import 'screens/emergencia/nueva_emergencia_screen.dart';
import 'screens/emergencia/tracking_screen.dart';
import 'screens/pagos/mis_pagos_screen.dart';
import 'screens/pagos/pago_screen.dart';
import 'screens/calificacion/calificacion_screen.dart';
import 'screens/vehiculos/vehiculos_screen.dart';
import 'screens/vehiculos/vehiculo_form_screen.dart';
import 'screens/notificaciones/notificaciones_screen.dart';
import 'screens/perfil/perfil_screen.dart';
import 'screens/emergencia/historial_screen.dart';

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint("Handling a background message: ${message.messageId}");
}

final GlobalKey<ScaffoldMessengerState> scaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();

final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();

const AndroidNotificationChannel channel = AndroidNotificationChannel(
  'high_importance_channel', // id
  'Notificaciones Importantes', // name
  description: 'Este canal es usado para notificaciones importantes.', // description
  importance: Importance.max,
);

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await Firebase.initializeApp();
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  // Solicitar permisos para notificaciones
  await FirebaseMessaging.instance.requestPermission();
  
  // Opciones para iOS en primer plano
  await FirebaseMessaging.instance.setForegroundNotificationPresentationOptions(
    alert: true,
    badge: true,
    sound: true,
  );

  // Inicializar flutter_local_notifications
  const AndroidInitializationSettings initializationSettingsAndroid = AndroidInitializationSettings('@mipmap/ic_launcher');
  const InitializationSettings initializationSettings = InitializationSettings(android: initializationSettingsAndroid);
  await flutterLocalNotificationsPlugin.initialize(settings: initializationSettings);

  await flutterLocalNotificationsPlugin
      .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
      ?.createNotificationChannel(channel);

  // Escuchar notificaciones mientras la app está ABIERTA (Foreground)
  FirebaseMessaging.onMessage.listen((RemoteMessage message) {
    RemoteNotification? notification = message.notification;

    if (notification != null) {
      // Mostrar notificación nativa tipo "Heads-Up" (baja desde arriba)
      flutterLocalNotificationsPlugin.show(
        id: notification.hashCode,
        title: notification.title,
        body: notification.body,
        notificationDetails: NotificationDetails(
          android: AndroidNotificationDetails(
            channel.id,
            channel.name,
            channelDescription: channel.description,
            icon: '@mipmap/ic_launcher',
            importance: Importance.max,
            priority: Priority.high,
          ),
        ),
      );

      // Mostrar el SnackBar dentro de la app como respaldo opcional
      scaffoldMessengerKey.currentState?.showSnackBar(
        SnackBar(
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                notification.title ?? 'Notificación',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              Text(notification.body ?? ''),
            ],
          ),
          duration: const Duration(seconds: 5),
          backgroundColor: Colors.blue.shade800,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          margin: const EdgeInsets.all(16),
        ),
      );
    }
  });

  // Stripe configuration
  Stripe.publishableKey = 'pk_test_51SST3pGRwb0l2ATkKgCn2co5sjWSlDKebdCqjK52h6JtRvmpY4Pa9GZATmZOU9HdDzM1aJ5FcVEjAv8Q0HFB7YZx00YakU9BhM';
  await Stripe.instance.applySettings();
  
  final storage = StorageService();
  await storage.init();
  
  final api = ApiService(storage);
  final authService = AuthService(api, storage);
  
  final authProvider = AuthProvider(authService: authService, storageService: storage);
  await authProvider.init();

  api.onUnauthorized = () {
    authProvider.logout();
  };

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: authProvider),
        ChangeNotifierProvider(create: (_) => EmergenciaProvider(apiService: api)),
        ChangeNotifierProvider(create: (_) => VehiculoProvider(apiService: api)),
        ChangeNotifierProvider(create: (_) => NotificacionProvider(apiService: api)),
        ChangeNotifierProvider(create: (_) => TallerProvider(apiService: api)),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    
    return MaterialApp(
      scaffoldMessengerKey: scaffoldMessengerKey,
      title: 'TallerPro',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: auth.isLoggedIn ? const MainScreen() : const LoginScreen(),
      routes: {
        '/login': (_) => const LoginScreen(),
        '/register': (_) => const RegisterScreen(),
        '/home': (_) => const MainScreen(),
        '/nueva-emergencia': (_) => const NuevaEmergenciaScreen(),
        '/tracking': (_) => const TrackingScreen(),
        '/pago': (_) => const PagoScreen(),
        '/mis_pagos': (_) => const MisPagosScreen(),
        '/calificacion': (_) => const CalificacionScreen(),
        '/vehiculos': (_) => const VehiculosScreen(),
        '/vehiculo-form': (_) => const VehiculoFormScreen(),
        '/notificaciones': (_) => const NotificacionesScreen(),
        '/perfil': (_) => const PerfilScreen(),
        '/historial': (_) => const HistorialScreen(),
      },
    );
  }
}
