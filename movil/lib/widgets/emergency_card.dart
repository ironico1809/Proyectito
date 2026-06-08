import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/incidente.dart';
import 'status_badge.dart';

class EmergencyCard extends StatelessWidget {
  final Incidente incidente;
  final VoidCallback? onTap;

  const EmergencyCard({
    super.key,
    required this.incidente,
    this.onTap,
  });

  static const _slate800 = Color(0xFF1E293B);
  static const _slate600 = Color(0xFF475569);
  static const _amber = Color(0xFFF59E0B);

  String _formatDate(String? dateString) {
    if (dateString == null) return '';
    try {
      final date = DateTime.parse(dateString).toLocal();
      return DateFormat('dd/MM/yyyy HH:mm').format(date);
    } catch (_) {
      return dateString;
    }
  }

  String _priorityLabel(String? priority) {
    switch (priority) {
      case 'alta':
        return '🔴 Alta';
      case 'media':
        return '🟡 Media';
      case 'baja':
        return '🟢 Baja';
      default:
        return priority ?? '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: _slate800,
          borderRadius: BorderRadius.circular(14),
          border: const Border(
            left: BorderSide(color: _amber, width: 3),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  StatusBadge(status: incidente.estadoEnum ?? 'pendiente'),
                  Text(
                    _formatDate(incidente.fechaCreacion),
                    style: TextStyle(color: _slate600, fontSize: 12),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                incidente.descripcionTexto != null && incidente.descripcionTexto!.length > 80
                    ? '${incidente.descripcionTexto!.substring(0, 80)}...'
                    : incidente.descripcionTexto ?? 'Sin descripción',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  if (incidente.prioridadEnum != null) ...[
                    Text(
                      _priorityLabel(incidente.prioridadEnum),
                      style: const TextStyle(fontSize: 12, color: Colors.white70),
                    ),
                    const Spacer(),
                  ],
                  if (incidente.tallerNombre != null)
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.build_outlined, size: 14, color: _amber),
                        const SizedBox(width: 4),
                        Text(
                          incidente.tallerNombre!,
                          style: TextStyle(
                            color: _amber,
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
