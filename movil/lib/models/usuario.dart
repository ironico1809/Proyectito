class Usuario {
  final int idUsuario;
  final String nombre;
  final String email;
  final String? telefono;
  final String rol;
  final int? idTaller;
  final int? tenantId;

  Usuario({
    required this.idUsuario,
    required this.nombre,
    required this.email,
    this.telefono,
    required this.rol,
    this.idTaller,
    this.tenantId,
  });

  factory Usuario.fromJson(Map<String, dynamic> json) => Usuario(
    idUsuario: json['id_usuario'],
    nombre: json['nombre'],
    email: json['email'] ?? '',
    telefono: json['telefono'],
    rol: json['rol'] ?? 'cliente',
    idTaller: json['id_taller'],
    tenantId: json['tenant_id'],
  );
}
