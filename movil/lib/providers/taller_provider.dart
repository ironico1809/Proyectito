import 'package:flutter/foundation.dart';
import '../models/taller.dart';
import '../services/api_service.dart';

class TallerProvider extends ChangeNotifier {
  final ApiService _apiService;

  List<Taller> _talleresCercanos = [];
  bool _isLoading = false;
  String? _error;
  bool _disposed = false;

  TallerProvider({required ApiService apiService}) : _apiService = apiService;

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

  List<Taller> get talleresCercanos => _talleresCercanos;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadTalleresCercanos() async {
    try {
      _isLoading = true;
      _error = null;
      _safeNotify();

      final response = await _apiService.get('/talleres/cercanos');
      
      if (response.statusCode == 200) {
        _talleresCercanos = (response.data as List)
            .map((t) => Taller.fromJson(t))
            .toList();
      } else {
        _error = 'Error al cargar talleres';
      }
    } catch (e) {
      _error = 'Error de conexión: $e';
    } finally {
      _isLoading = false;
      _safeNotify();
    }
  }
}
