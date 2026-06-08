import 'package:flutter/foundation.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import '../models/usuario.dart';
import '../services/auth_service.dart';
import '../services/storage_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService;
  final StorageService _storageService;

  Usuario? _currentUser;
  bool _isLoading = false;
  String? _error;
  bool _isLoggedIn = false;

  AuthProvider({
    required AuthService authService,
    required StorageService storageService,
  })  : _authService = authService,
        _storageService = storageService;

  Usuario? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn => _isLoggedIn;

  Future<void> init() async {
    _isLoading = true;
    notifyListeners();

    try {
      final token = await _storageService.getToken();
      if (token != null && token.isNotEmpty) {
        _isLoggedIn = true;
        _currentUser = await _storageService.getUser();
        _syncFcmToken();
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final user = await _authService.login(email, password);
      _currentUser = user;
      _isLoggedIn = true;
      _isLoading = false;
      notifyListeners();
      _syncFcmToken();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> register(String nombre, String email, String password, String telefono) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final user = await _authService.register(
        nombre: nombre,
        email: email,
        password: password,
        telefono: telefono.isEmpty ? null : telefono,
      );
      _currentUser = user;
      _isLoggedIn = true;
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _authService.logout();
    } catch (_) {}

    _currentUser = null;
    _isLoggedIn = false;
    _isLoading = false;
    _error = null;
    notifyListeners();
  }

  Future<bool> updateProfile(String nombre, String? telefono, String? email, String? password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final updatedUser = await _authService.updateProfile(
        nombre: nombre,
        telefono: telefono,
        email: email,
        password: password,
      );
      _currentUser = updatedUser;
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> _syncFcmToken() async {
    try {
      String? token = await FirebaseMessaging.instance.getToken();
      if (token != null) {
        await _authService.updateFcmToken(token);
      }
    } catch (e) {
      debugPrint("Error syncing FCM token: $e");
    }
  }
}
