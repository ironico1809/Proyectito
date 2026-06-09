import 'package:shared_preferences/shared_preferences.dart';
import '../models/usuario.dart';

class StorageService {
  static const _keyToken = 'token';
  static const _keyUserId = 'user_id';
  static const _keyUserName = 'user_name';
  static const _keyUserRole = 'user_role';
  static const _keyUserEmail = 'user_email';
  static const _keyUserPhone = 'user_phone';
  static const _keyTenantId = 'tenant_id';

  late SharedPreferences _prefs;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  Future<void> saveToken(String token) async {
    await _prefs.setString(_keyToken, token);
  }

  String? getToken() => _prefs.getString(_keyToken);

  Future<void> saveUserData({
    required int id,
    required String nombre,
    required String rol,
    required String email,
    String? telefono,
    int? tenantId,
  }) async {
    await Future.wait([
      _prefs.setInt(_keyUserId, id),
      _prefs.setString(_keyUserName, nombre),
      _prefs.setString(_keyUserRole, rol),
      _prefs.setString(_keyUserEmail, email),
      if (telefono != null)
        _prefs.setString(_keyUserPhone, telefono)
      else
        _prefs.remove(_keyUserPhone),
      if (tenantId != null)
        _prefs.setInt(_keyTenantId, tenantId)
      else
        _prefs.remove(_keyTenantId),
    ]);
  }

  int? getUserId() => _prefs.getInt(_keyUserId);
  String? getUserName() => _prefs.getString(_keyUserName);
  String? getUserRole() => _prefs.getString(_keyUserRole);
  String? getUserEmail() => _prefs.getString(_keyUserEmail);
  String? getUserPhone() => _prefs.getString(_keyUserPhone);
  int? getTenantId() => _prefs.getInt(_keyTenantId);

  Usuario? getUser() {
    final id = getUserId();
    final nombre = getUserName();
    final email = getUserEmail();
    final rol = getUserRole();
    final telefono = getUserPhone();
    final tenantId = getTenantId();
    
    if (id == null || nombre == null || rol == null) return null;
    return Usuario(
      idUsuario: id,
      nombre: nombre,
      email: email ?? '',
      rol: rol,
      telefono: telefono,
      tenantId: tenantId,
    );
  }

  Future<void> clear() async {
    await _prefs.clear();
  }

  bool isLoggedIn() => getToken() != null;
}
