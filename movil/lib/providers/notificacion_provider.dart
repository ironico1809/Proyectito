import 'package:flutter/foundation.dart';
import '../models/notificacion.dart';
import '../services/api_service.dart';

class NotificacionProvider extends ChangeNotifier {
  final ApiService _apiService;

  List<Notificacion> _notificaciones = [];
  int _unreadCount = 0;
  bool _isLoading = false;
  String? _error;
  bool _disposed = false;

  NotificacionProvider({required ApiService apiService}) : _apiService = apiService;

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }

  void _safeNotify() {
    if (_disposed) return;
    Future.delayed(Duration.zero, () {
      if (!_disposed) {
        notifyListeners();
      }
    });
  }

  List<Notificacion> get notificaciones => _notificaciones;
  int get unreadCount => _unreadCount;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadNotificaciones() async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final response = await _apiService.get('/notificaciones/mis-notificaciones');
      final List data = response.data is List ? response.data : response.data['results'] ?? [];
      _notificaciones = data.map((e) => Notificacion.fromJson(e)).toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      _safeNotify();
    }
  }

  Future<void> loadUnreadCount() async {
    try {
      final response = await _apiService.get('/notificaciones/no-leidas');
      _unreadCount = response.data['no_leidas'] ?? 0;
      _safeNotify();
    } catch (_) {}
  }

  Future<void> marcarLeida(int id) async {
    try {
      await _apiService.patch('/notificaciones/$id/leer');
      final index = _notificaciones.indexWhere((n) => n.idNotificacion == id);
      if (index != -1) {
        _notificaciones[index] = _notificaciones[index].copyWith(leido: true);
      }
      if (_unreadCount > 0) _unreadCount--;
      _safeNotify();
    } catch (e) {
      _error = e.toString();
      _safeNotify();
    }
  }

  void clearError() {
    _error = null;
    _safeNotify();
  }
}
