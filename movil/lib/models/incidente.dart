class Incidente {
  final int? idIncidente;
  final int? clienteId;
  final int? vehiculoId;
  final int? tallerActualId;
  final int? tecnicoId;
  final String? estadoEnum;
  final String? prioridadEnum;
  final String? descripcionTexto;
  final double? costoFinalDecimal;
  final double? latitudEmergencia;
  final double? longitudEmergencia;
  final double? latitudTecnico;
  final double? longitudTecnico;
  final String? fechaCreacion;
  final String? uuidOffline;
  final String? clienteNombre;
  final String? vehiculoPlaca;
  final String? tallerNombre;
  final String? tallerTelefono;
  final String? tecnicoNombre;
  final String? tecnicoTelefono;
  final String? tecnicoEspecialidad;
  final String? clasificacionIa;
  final double? latitudTaller;
  final double? longitudTaller;

  Incidente({
    this.idIncidente,
    this.clienteId,
    this.vehiculoId,
    this.tallerActualId,
    this.tecnicoId,
    this.estadoEnum,
    this.prioridadEnum,
    this.descripcionTexto,
    this.costoFinalDecimal,
    this.latitudEmergencia,
    this.longitudEmergencia,
    this.latitudTecnico,
    this.longitudTecnico,
    this.fechaCreacion,
    this.uuidOffline,
    this.clienteNombre,
    this.vehiculoPlaca,
    this.tallerNombre,
    this.tallerTelefono,
    this.tecnicoNombre,
    this.tecnicoTelefono,
    this.tecnicoEspecialidad,
    this.clasificacionIa,
    this.latitudTaller,
    this.longitudTaller,
  });

  factory Incidente.fromJson(Map<String, dynamic> json) => Incidente(
    idIncidente: json['id_incidente'],
    clienteId: json['cliente_id'],
    vehiculoId: json['vehiculo_id'],
    tallerActualId: json['taller_actual_id'],
    tecnicoId: json['tecnico_id'],
    estadoEnum: json['estado_enum'],
    prioridadEnum: json['prioridad_enum'],
    descripcionTexto: json['descripcion_texto'],
    costoFinalDecimal: json['costo_final_decimal'] != null
        ? double.tryParse(json['costo_final_decimal'].toString())
        : null,
    latitudEmergencia: json['latitud_emergencia'] != null
        ? double.tryParse(json['latitud_emergencia'].toString())
        : null,
    longitudEmergencia: json['longitud_emergencia'] != null
        ? double.tryParse(json['longitud_emergencia'].toString())
        : null,
    latitudTecnico: json['latitud_tecnico'] != null
        ? double.tryParse(json['latitud_tecnico'].toString())
        : null,
    longitudTecnico: json['longitud_tecnico'] != null
        ? double.tryParse(json['longitud_tecnico'].toString())
        : null,
    fechaCreacion: json['fecha_creacion_timestamp'],
    uuidOffline: json['uuid_offline'],
    clienteNombre: json['cliente_nombre'],
    vehiculoPlaca: json['vehiculo_placa'],
    tallerNombre: json['taller_nombre'],
    tallerTelefono: json['taller_telefono'],
    tecnicoNombre: json['tecnico_nombre'],
    tecnicoTelefono: json['tecnico_telefono'],
    tecnicoEspecialidad: json['tecnico_especialidad'],
    clasificacionIa: json['clasificacion_ia'],
    latitudTaller: json['latitud_taller'] != null
        ? double.tryParse(json['latitud_taller'].toString())
        : null,
    longitudTaller: json['longitud_taller'] != null
        ? double.tryParse(json['longitud_taller'].toString())
        : null,
  );

  Map<String, dynamic> toJsonForCreate() => {
    'vehiculo_id': vehiculoId,
    'descripcion_texto': descripcionTexto,
    'latitud_emergencia': latitudEmergencia,
    'longitud_emergencia': longitudEmergencia,
    if (uuidOffline != null) 'uuid_offline': uuidOffline,
  };
}
