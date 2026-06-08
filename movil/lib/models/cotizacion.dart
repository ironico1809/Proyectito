class Cotizacion {
  final int idCotizacion;
  final int incidenteId;
  final int tallerId;
  final double precioEstimado;
  final int tiempoEstimadoMin;
  final String? descripcion;
  final String estado;
  final String? tallerNombre;

  Cotizacion({
    required this.idCotizacion,
    required this.incidenteId,
    required this.tallerId,
    required this.precioEstimado,
    required this.tiempoEstimadoMin,
    this.descripcion,
    required this.estado,
    this.tallerNombre,
  });

  factory Cotizacion.fromJson(Map<String, dynamic> json) => Cotizacion(
    idCotizacion: json['id_cotizacion'],
    incidenteId: json['incidente_id'],
    tallerId: json['taller_id'],
    precioEstimado: double.tryParse(json['precio_estimado'].toString()) ?? 0,
    tiempoEstimadoMin: json['tiempo_estimado_min'] ?? 0,
    descripcion: json['descripcion'],
    estado: json['estado'] ?? 'pendiente',
    tallerNombre: json['taller_nombre'],
  );
}
