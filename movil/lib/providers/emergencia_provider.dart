import 'package:flutter/foundation.dart';
import '../models/incidente.dart';
import '../models/cotizacion.dart';
import '../services/api_service.dart';
import '../services/offline_service.dart';

class EmergenciaProvider extends ChangeNotifier {
  final ApiService _apiService;
  final OfflineService _offlineService = OfflineService();

  Incidente? _activeIncidente;
  bool _isLoading = false;
  String? _error;
  List<Cotizacion> _cotizaciones = [];
  Map<String, dynamic>? _monitoreo;
  List<Incidente> _historial = [];
  int _pendingOfflineCount = 0;
  bool _disposed = false;

  EmergenciaProvider({required ApiService apiService}) : _apiService = apiService;

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

  int get pendingOfflineCount => _pendingOfflineCount;

  Incidente? get activeIncidente => _activeIncidente;
  bool get isLoading => _isLoading;
  String? get error => _error;
  List<Cotizacion> get cotizaciones => _cotizaciones;
  Map<String, dynamic>? get monitoreo => _monitoreo;
  List<Incidente> get historial => _historial;

  Future<void> loadActiveEmergency() async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final response = await _apiService.get('/incidentes/cliente/activo');
      final data = response.data;
      final idIncidente = data['id_incidente'];
      if (idIncidente != null && idIncidente is int) {
        final detail = await _apiService.get('/incidentes/$idIncidente');
        _activeIncidente = Incidente.fromJson(detail.data);
      } else {
        _activeIncidente = null;
      }
    } catch (e) {
      _activeIncidente = null;
      _error = e.toString();
    } finally {
      _isLoading = false;
      _safeNotify();
    }
  }

  Future<void> loadPendingOfflineCount() async {
    final pending = await _offlineService.getPendingEmergencies();
    _pendingOfflineCount = pending.length;
    _safeNotify();
  }

  Future<void> syncOfflineEmergencies() async {
    final pending = await _offlineService.getPendingEmergencies();
    if (pending.isEmpty) return;

    for (final p in pending) {
      try {
        final List<Map<String, String>> evidencias = [];
        final imgBase64 = p['imagen_base64'] as String?;
        if (imgBase64 != null && imgBase64.isNotEmpty) {
          evidencias.add({'tipo_enum': 'imagen', 'url_recurso': imgBase64});
        }
        final audBase64 = p['audio_base64'] as String?;
        if (audBase64 != null && audBase64.isNotEmpty) {
          evidencias.add({'tipo_enum': 'audio', 'url_recurso': audBase64});
        }

        await _apiService.post('/incidentes/', data: {
          'vehiculo_id': p['vehiculo_id'],
          'descripcion_texto': p['descripcion'],
          'latitud_emergencia': p['latitud'],
          'longitud_emergencia': p['longitud'],
          'uuid_offline': p['uuid'],
          if (evidencias.isNotEmpty) 'evidencias': evidencias,
        });

        await _offlineService.markAsSynced(p['id'] as int);
      } catch (e) {
        debugPrint('Error syncing offline emergency: $e');
      }
    }
    
    await loadPendingOfflineCount();
    // Refresh active emergency just in case one of the synced ones became active
    await loadActiveEmergency();
  }

  Future<bool> createEmergency({
    required int vehiculoId,
    required String descripcion,
    required double lat,
    required double lng,
    String? imagenBase64,
    String? audioBase64,
  }) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final data = {
        'vehiculo_id': vehiculoId,
        'descripcion_texto': descripcion,
        'latitud_emergencia': lat,
        'longitud_emergencia': lng,
        'evidencias': [],
      };
      
      final List<Map<String, dynamic>> evidencias = [];
      if (imagenBase64 != null) {
        evidencias.add({'tipo_enum': 'imagen', 'url_recurso': imagenBase64});
      }
      if (audioBase64 != null) {
        evidencias.add({'tipo_enum': 'audio', 'url_recurso': audioBase64});
      }
      if (evidencias.isNotEmpty) {
        data['evidencias'] = evidencias;
      }
      
      final response = await _apiService.post('/incidentes/', data: data);
      _activeIncidente = Incidente.fromJson(response.data);
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

  Future<String?> transcribeAudio(String audioBase64) async {
    try {
      final response = await _apiService.post('/ia/transcribir', data: {
        'audio_base64': audioBase64,
      });
      if (response.data != null && response.data['texto'] != null) {
        return response.data['texto'] as String;
      }
    } catch (e) {
      debugPrint('Error en la transcripción de audio: $e');
    }
    return null;
  }

  Future<void> loadCotizaciones(int incidenteId) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final response = await _apiService.get('/cotizaciones/$incidenteId');
      final List data = response.data is List ? response.data : response.data['results'] ?? [];
      _cotizaciones = data.map((e) => Cotizacion.fromJson(e)).toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      _safeNotify();
    }
  }

  Future<bool> aceptarCotizacion(int cotizacionId) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      await _apiService.put('/cotizaciones/$cotizacionId/aceptar');
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

  Future<Incidente?> loadIncidenteById(int id) async {
    try {
      final response = await _apiService.get('/incidentes/$id');
      return Incidente.fromJson(response.data);
    } catch (e) {
      return null;
    }
  }

  Future<void> loadMonitoreo(int incidenteId) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final response = await _apiService.get('/incidentes/$incidenteId/monitoreo');
      _monitoreo = Map<String, dynamic>.from(response.data);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      _safeNotify();
    }
  }

  Future<bool> calificarIncidente({
    required int incidenteId,
    required int puntuacion,
    String? comentario,
  }) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      await _apiService.post('/calificaciones/', data: {
        'incidente_id': incidenteId,
        'puntuacion': puntuacion,
        'comentario': comentario,
      });
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

  Future<bool> registrarPago({
    required int incidenteId,
    required int duenoTallerId,
    required double montoTotal,
    required String metodo,
  }) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      await _apiService.post('/pagos/', data: {
        'incidente_id': incidenteId,
        'dueño_taller_id': duenoTallerId,
        'monto_total_decimal': montoTotal,
        'metodo_enum': metodo,
      });
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

  Future<String?> crearStripeIntent(int incidenteId) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      final res = await _apiService.post('/pagos/stripe/crear-intent', data: {
        'incidente_id': incidenteId,
      });
      _isLoading = false;
      _safeNotify();
      return res.data['client_secret'];
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      _safeNotify();
      return null;
    }
  }

  Future<void> loadHistorial() async {
    print("DEBUG_PROVIDER: loadHistorial() called!");
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      print("DEBUG_PROVIDER: Requesting GET /incidentes/historial/cliente");
      final response = await _apiService.get('/incidentes/historial/cliente');
      print("DEBUG_PROVIDER: Response code = ${response.statusCode}");
      
      final List data = response.data is List ? response.data : response.data['results'] ?? [];
      print("DEBUG_PROVIDER: Parsing ${data.length} incidents from JSON list");
      
      final List<Incidente> list = [];
      for (int i = 0; i < data.length; i++) {
        try {
          list.add(Incidente.fromJson(data[i]));
        } catch (parseError, stack) {
          print("DEBUG_PROVIDER: Error parsing incident at index $i: $parseError");
          print("JSON item: ${data[i]}");
          print("StackTrace: $stack");
          // Re-throw or ignore? Let's rethrow to catch it in main try block,
          // or we can allow partial load. Let's re-throw so we know about it.
          rethrow;
        }
      }
      
      _historial = list;
      print("DEBUG_PROVIDER: Historial loaded successfully. Count = ${_historial.length}");
    } catch (e, stack) {
      print("DEBUG_PROVIDER: Exception in loadHistorial: $e");
      print("StackTrace: $stack");
      _error = e.toString();
    } finally {
      _isLoading = false;
      _safeNotify();
    }
  }

  Future<bool> cancelarEmergencia(int incidenteId) async {
    _isLoading = true;
    _error = null;
    _safeNotify();

    try {
      await _apiService.patch('/incidentes/$incidenteId/cancelar');
      _isLoading = false;
      _safeNotify();
      // Refrescar para reflejar la cancelación
      await loadActiveEmergency();
      await loadHistorial();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      _safeNotify();
      return false;
    }
  }

  void clear() {
    _activeIncidente = null;
    _cotizaciones = [];
    _monitoreo = null;
    _historial = [];
    _isLoading = false;
    _error = null;
    _safeNotify();
  }
}
