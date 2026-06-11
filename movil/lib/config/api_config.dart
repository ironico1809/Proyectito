class ApiConfig {
  // Para producción Railway:
  static const String baseUrl = 'https://proyectito-production.up.railway.app';
  static const String wsUrl = 'wss://proyectito-production.up.railway.app';

  // Para Emulador Android (Local):
  // static const String baseUrl = 'http://10.0.2.2:8000';
  // static const String wsUrl = 'ws://10.0.2.2:8000';

  // Para dispositivo físico real (debes colocar la IP local de tu PC, ej: 192.168.1.15):
  // static const String baseUrl = 'http://192.168.0.144:8000';
  // static const String wsUrl = 'ws://192.168.0.144:8000';

  static const Duration timeout = Duration(seconds: 60);
}
