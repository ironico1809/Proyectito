import 'package:flutter/material.dart';

class StatusBadge extends StatelessWidget {
  final String status;

  const StatusBadge({super.key, required this.status});

  static const _statusLabels = {
    'pendiente': 'Pendiente',
    'en_proceso': 'En Proceso',
    'finalizado': 'Finalizado',
    'cancelado': 'Cancelado',
    'en_camino': 'En Camino',
    'en_atencion': 'En Atención',
    'taller_asignado': 'Taller Asignado',
    'buscando_taller': 'Buscando Taller',
    'atendido': 'Atendido',
  };

  Color _colorForStatus() {
    switch (status) {
      case 'pendiente':
        return Colors.yellow;
      case 'en_proceso':
      case 'en_camino':
      case 'en_atencion':
        return Colors.blue;
      case 'finalizado':
      case 'atendido':
        return Colors.green;
      case 'cancelado':
        return Colors.red;
      case 'buscando_taller':
      case 'taller_asignado':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _colorForStatus();
    final label = _statusLabels[status] ?? status;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
