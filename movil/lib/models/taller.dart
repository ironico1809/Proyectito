class Taller {
  final int idTaller;
  final int duenoId;
  final String nombreDueno;
  final String emailDueno;
  final String telefonoDueno;
  final String nombreTaller;
  final String direccion;
  final String nit;
  final double latitudDecimal;
  final double longitudDecimal;

  Taller({
    required this.idTaller,
    required this.duenoId,
    required this.nombreDueno,
    required this.emailDueno,
    required this.telefonoDueno,
    required this.nombreTaller,
    required this.direccion,
    required this.nit,
    required this.latitudDecimal,
    required this.longitudDecimal,
  });

  factory Taller.fromJson(Map<String, dynamic> json) => Taller(
        idTaller: json['id_taller'],
        duenoId: json['dueño_id'],
        nombreDueno: json['nombre_dueno'] ?? '',
        emailDueno: json['email_dueno'] ?? '',
        telefonoDueno: json['telefono_dueno'] ?? '',
        nombreTaller: json['nombre_taller'] ?? '',
        direccion: json['direccion'] ?? '',
        nit: json['nit'] ?? '',
        latitudDecimal: double.tryParse(json['latitud_decimal'].toString()) ?? 0,
        longitudDecimal: double.tryParse(json['longitud_decimal'].toString()) ?? 0,
      );
}
