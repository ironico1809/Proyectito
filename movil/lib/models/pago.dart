class Pago {
  final int? idPago;
  final int incidenteId;
  final int duenoTallerId;
  final double montoTotal;
  final String metodo;

  Pago({
    this.idPago,
    required this.incidenteId,
    required this.duenoTallerId,
    required this.montoTotal,
    required this.metodo,
  });

  factory Pago.fromJson(Map<String, dynamic> json) => Pago(
    idPago: json['id_pago'],
    incidenteId: json['incidente_id'],
    duenoTallerId: json['dueño_taller_id'] ?? json['dueno_taller_id'] ?? 0,
    montoTotal: double.tryParse(json['monto_total_decimal'].toString()) ?? 0,
    metodo: json['metodo_enum'] ?? 'qr',
  );

  Map<String, dynamic> toJson() => {
    'incidente_id': incidenteId,
    'dueño_taller_id': duenoTallerId,
    'monto_total_decimal': montoTotal,
    'metodo_enum': metodo,
  };
}
