class Notificacion {
  final int idNotificacion;
  final String titulo;
  final String mensaje;
  final bool leido;
  final String? fechaCreacion;

  Notificacion({
    required this.idNotificacion,
    required this.titulo,
    required this.mensaje,
    required this.leido,
    this.fechaCreacion,
  });

  factory Notificacion.fromJson(Map<String, dynamic> json) => Notificacion(
    idNotificacion: json['id_notificacion'],
    titulo: json['titulo'] ?? '',
    mensaje: json['mensaje'] ?? '',
    leido: json['leido_boolean'] ?? false,
    fechaCreacion: json['fecha_creacion_timestamp'],
  );

  Notificacion copyWith({
    int? idNotificacion,
    String? titulo,
    String? mensaje,
    bool? leido,
    String? fechaCreacion,
  }) {
    return Notificacion(
      idNotificacion: idNotificacion ?? this.idNotificacion,
      titulo: titulo ?? this.titulo,
      mensaje: mensaje ?? this.mensaje,
      leido: leido ?? this.leido,
      fechaCreacion: fechaCreacion ?? this.fechaCreacion,
    );
  }
}
