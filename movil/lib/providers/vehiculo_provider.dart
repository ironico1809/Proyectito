import 'package:flutter/foundation.dart';
import '../models/vehiculo.dart';
import '../services/api_service.dart';

class VehiculoProvider extends ChangeNotifier {
  final ApiService _apiService;

  List<Vehiculo> _vehiculos = [];
  bool _isLoading = false;
  String? _error;
  bool _disposed = false;

  VehiculoProvider({required ApiService apiService}) : _apiService = apiService;

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

  List<Vehiculo> get vehiculos => _vehiculos;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadVehiculos() async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final response = await _apiService.get('/vehiculos/');
      final List data = response.data is List ? response.data : response.data['results'] ?? [];
      _vehiculos = data.map((e) => Vehiculo.fromJson(e)).toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      _safeNotify();
    }
  }

  Future<bool> addVehiculo(Vehiculo vehiculo) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final response = await _apiService.post('/vehiculos/', data: vehiculo.toJson());
      final nuevo = Vehiculo.fromJson(response.data);
      _vehiculos.add(nuevo);
      _isLoading = false;
      _safeNotify();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      _safeNotify();
      return false;
    }
  }

  Future<bool> updateVehiculo(int id, Vehiculo vehiculo) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final response = await _apiService.patch('/vehiculos/$id', data: vehiculo.toJson());
      final updated = Vehiculo.fromJson(response.data);
      final index = _vehiculos.indexWhere((v) => v.idVehiculo == id);
      if (index != -1) {
        _vehiculos[index] = updated;
      }
      _isLoading = false;
      _safeNotify();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      _safeNotify();
      return false;
    }
  }

  Future<bool> deleteVehiculo(int id) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      await _apiService.delete('/vehiculos/$id');
      _vehiculos.removeWhere((v) => v.idVehiculo == id);
      _isLoading = false;
      _safeNotify();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      _safeNotify();
      return false;
    }
  }

  void clearError() {
    _error = null;
    _safeNotify();
  }
}
