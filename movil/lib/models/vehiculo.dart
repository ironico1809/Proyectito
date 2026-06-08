class Vehiculo {
  final int? idVehiculo;
  final String placa;
  final String marca;
  final String modelo;
  final String color;

  Vehiculo({
    this.idVehiculo,
    required this.placa,
    required this.marca,
    required this.modelo,
    required this.color,
  });

  factory Vehiculo.fromJson(Map<String, dynamic> json) => Vehiculo(
    idVehiculo: json['id_vehiculo'],
    placa: json['placa'] ?? '',
    marca: json['marca'] ?? '',
    modelo: json['modelo'] ?? '',
    color: json['color'] ?? '',
  );

  Map<String, dynamic> toJson() => {
    'placa': placa,
    'marca': marca,
    'modelo': modelo,
    'color': color,
  };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Vehiculo &&
          runtimeType == other.runtimeType &&
          idVehiculo == other.idVehiculo;

  @override
  int get hashCode => idVehiculo.hashCode;
}
