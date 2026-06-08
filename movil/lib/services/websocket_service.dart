import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../config/api_config.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  final _controller = StreamController<Map<String, dynamic>>.broadcast();
  final _connectionController = StreamController<bool>.broadcast();
  Timer? _reconnectTimer;
  int _retryCount = 0;
  int? _currentIncidenteId;
  bool _intentionalDisconnect = false;
  bool _isConnected = false;

  static const int _maxRetries = 5;
  static const Duration _retryDelay = Duration(seconds: 3);

  Stream<Map<String, dynamic>> get messages => _controller.stream;
  Stream<bool> get connectionState => _connectionController.stream;
  bool get isConnected => _isConnected;

  void connect(int incidenteId) {
    _currentIncidenteId = incidenteId;
    _intentionalDisconnect = false;
    _retryCount = 0;
    _establishConnection(incidenteId);
  }

  void _establishConnection(int incidenteId) {
    final wsUrl = '${ApiConfig.wsUrl}/ws/incidente/$incidenteId';
    _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

    _isConnected = true;
    _connectionController.add(true);

    _channel!.stream.listen(
      (data) {
        _retryCount = 0;
        if (!_isConnected) {
          _isConnected = true;
          _connectionController.add(true);
        }
        try {
          final decoded = json.decode(data as String);
          if (decoded is Map<String, dynamic>) {
            _controller.add(decoded);
          }
        } catch (_) {}
      },
      onError: (error) {
        _isConnected = false;
        _connectionController.add(false);
        _attemptReconnect();
      },
      onDone: () {
        _isConnected = false;
        _connectionController.add(false);
        if (!_intentionalDisconnect) {
          _attemptReconnect();
        }
      },
    );
  }

  void _attemptReconnect() {
    if (_intentionalDisconnect || _retryCount >= _maxRetries) return;

    _retryCount++;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(_retryDelay, () {
      if (_currentIncidenteId != null) {
        _establishConnection(_currentIncidenteId!);
      }
    });
  }

  void sendMessage(Map<String, dynamic> data) {
    _channel?.sink.add(json.encode(data));
  }

  void disconnect() {
    _intentionalDisconnect = true;
    _isConnected = false;
    _connectionController.add(false);
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    _currentIncidenteId = null;
  }

  void dispose() {
    disconnect();
    _controller.close();
    _connectionController.close();
  }
}
