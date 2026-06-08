import '../models/usuario.dart';
import 'api_service.dart';
import 'storage_service.dart';

class AuthService {
  final ApiService _api;
  final StorageService _storage;

  AuthService(this._api, this._storage);

  Future<Usuario> login(String email, String password) async {
    final response = await _api.post('/auth/login', data: {
      'email': email,
      'password': password,
    });

    final data = response.data;

    await _storage.saveToken(data['access_token']);
    await _storage.saveUserData(
      id: data['id_usuario'],
      nombre: data['nombre'],
      rol: data['rol'],
      email: email,
    );

    // Let's call /usuarios/me to fetch any additional fields like phone number
    try {
      final meResponse = await _api.get('/usuarios/me');
      final meData = meResponse.data;
      await _storage.saveUserData(
        id: meData['id_usuario'],
        nombre: meData['nombre'],
        rol: meData['rol'],
        email: meData['email'] ?? email,
        telefono: meData['telefono'],
      );
      return Usuario.fromJson(meData);
    } catch (_) {
      return Usuario(
        idUsuario: data['id_usuario'],
        nombre: data['nombre'],
        email: email,
        rol: data['rol'],
        idTaller: data['id_taller'],
      );
    }
  }

  Future<Usuario> register({
    required String nombre,
    required String email,
    required String password,
    String? telefono,
  }) async {
    await _api.post('/usuarios/registro', data: {
      'nombre': nombre,
      'email': email,
      'password': password,
      if (telefono != null) 'telefono': telefono,
    });

    return login(email, password);
  }

  Future<Usuario> updateProfile({required String nombre, String? telefono, String? email, String? password}) async {
    final response = await _api.put('/usuarios/me', data: {
      'nombre': nombre,
      if (telefono != null) 'telefono': telefono,
      if (email != null) 'email': email,
      if (password != null && password.isNotEmpty) 'password': password,
    });

    final data = response.data;
    await _storage.saveUserData(
      id: data['id_usuario'],
      nombre: data['nombre'],
      rol: data['rol'],
      email: data['email'] ?? '',
      telefono: data['telefono'],
    );

    return Usuario.fromJson(data);
  }

  Future<void> updateFcmToken(String token) async {
    try {
      await _api.patch('/usuarios/fcm-token', data: {'fcm_token': token});
    } catch (e) {
      print('Error updating FCM token: $e');
    }
  }

  Future<void> logout() async {
    try {
      await _api.post('/auth/logout');
    } catch (_) {}
    await _storage.clear();
  }
}
