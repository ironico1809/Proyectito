import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../providers/emergencia_provider.dart';
import '../../models/incidente.dart';
import '../../widgets/status_badge.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../config/api_config.dart';

class HistorialScreen extends StatefulWidget {
  const HistorialScreen({super.key});

  @override
  State<HistorialScreen> createState() => _HistorialScreenState();
}

class _HistorialScreenState extends State<HistorialScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<EmergenciaProvider>().loadHistorial();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<EmergenciaProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text('Historial de Solicitudes', style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: provider.isLoading && provider.historial.isEmpty
            ? const Center(child: CircularProgressIndicator(color: Color(0xFFF59E0B)))
            : RefreshIndicator(
                color: const Color(0xFFF59E0B),
                onRefresh: () => provider.loadHistorial(),
                child: provider.error != null
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.error_outline, size: 64, color: Colors.redAccent),
                              const SizedBox(height: 16),
                              Text('Error de conexión:', style: GoogleFonts.inter(fontSize: 16, color: Colors.white, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 8),
                              Text(provider.error!, textAlign: TextAlign.center, style: GoogleFonts.inter(fontSize: 14, color: Colors.white70)),
                            ],
                          ),
                        ),
                      )
                    : provider.historial.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.history_rounded, size: 72, color: Colors.white24),
                                const SizedBox(height: 16),
                                Text('No tienes solicitudes previas',
                                    style: GoogleFonts.inter(fontSize: 16, color: Colors.white54)),
                              ],
                            ),
                          )
                        : ListView.builder(
                        padding: const EdgeInsets.all(24),
                        itemCount: provider.historial.length,
                        itemBuilder: (context, index) {
                          final inc = provider.historial[index];
                          final isActivo = inc.estadoEnum != 'cancelado' &&
                              inc.estadoEnum != 'finalizado' &&
                              inc.estadoEnum != 'atendido';

                          return GestureDetector(
                            onTap: () {
                              if (isActivo) {
                                Navigator.pushNamed(context, '/tracking', arguments: inc);
                              } else if (inc.estadoEnum == 'finalizado' || inc.estadoEnum == 'atendido') {
                                // If finished but has no payment, offer to pay
                                _showDetailDialog(inc);
                              } else {
                                _showDetailDialog(inc);
                              }
                            },
                            child: Container(
                              margin: const EdgeInsets.only(bottom: 16),
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: const Color(0xFF1E293B),
                                borderRadius: BorderRadius.circular(16),
                                border: isActivo
                                    ? Border.all(color: const Color(0xFFF59E0B).withOpacity(0.3), width: 1.5)
                                    : null,
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.15),
                                    blurRadius: 10,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      StatusBadge(status: inc.estadoEnum ?? 'pendiente'),
                                      const Spacer(),
                                      if (inc.fechaCreacion != null)
                                        Text(
                                          _formatDate(inc.fechaCreacion!),
                                          style: GoogleFonts.inter(fontSize: 12, color: Colors.white38),
                                        ),
                                    ],
                                  ),
                                  const SizedBox(height: 14),
                                  Text(
                                    inc.descripcionTexto ?? 'Sin descripción.',
                                    style: GoogleFonts.inter(fontSize: 14, color: Colors.white70, height: 1.4),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  const SizedBox(height: 14),
                                  const Divider(color: Colors.white10, height: 1),
                                  const SizedBox(height: 14),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text('Taller Asignado',
                                              style: GoogleFonts.inter(fontSize: 11, color: Colors.white38)),
                                          const SizedBox(height: 4),
                                          Text(
                                            inc.tallerNombre ?? 'Buscando taller...',
                                            style: GoogleFonts.inter(
                                              fontSize: 13,
                                              color: inc.tallerNombre != null ? const Color(0xFFF59E0B) : Colors.white54,
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                        ],
                                      ),
                                      if (inc.costoFinalDecimal != null && inc.costoFinalDecimal! > 0)
                                        Column(
                                          crossAxisAlignment: CrossAxisAlignment.end,
                                          children: [
                                            Text('Costo Final',
                                                style: GoogleFonts.inter(fontSize: 11, color: Colors.white38)),
                                            const SizedBox(height: 4),
                                            Text(
                                              'Bs. ${inc.costoFinalDecimal!.toStringAsFixed(2)}',
                                              style: GoogleFonts.inter(
                                                fontSize: 14,
                                                color: Colors.greenAccent,
                                                fontWeight: FontWeight.w700,
                                              ),
                                            ),
                                          ],
                                        )
                                      else
                                        const SizedBox.shrink(),
                                    ],
                                  ),
                                  if (isActivo) ...[
                                    const SizedBox(height: 12),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.end,
                                      children: [
                                        Text(
                                          'Seguimiento en vivo →',
                                          style: GoogleFonts.inter(
                                            fontSize: 12,
                                            color: const Color(0xFFF59E0B),
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ],
                                    )
                                  ]
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
      ),
    );
  }

  void _showDetailDialog(Incidente inc) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(
          'Detalle de Solicitud',
          style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _detailRow('ID Incidente', '#${inc.idIncidente ?? "N/A"}'),
              _detailRow('Estado', inc.estadoEnum?.toUpperCase() ?? 'PENDIENTE'),
              _detailRow('Prioridad', inc.prioridadEnum?.toUpperCase() ?? 'MEDIA'),
              _detailRow('Taller', inc.tallerNombre ?? 'Ninguno'),
              _detailRow('Clasificación IA', inc.clasificacionIa ?? 'Sin procesar'),
              _detailRow('Descripción', inc.descripcionTexto ?? 'Sin descripción'),
              if (inc.costoFinalDecimal != null)
                _detailRow('Costo Final', 'Bs. ${inc.costoFinalDecimal!.toStringAsFixed(2)}'),
              if (inc.fechaCreacion != null)
                _detailRow('Fecha Registro', _formatDate(inc.fechaCreacion!)),
            ],
          ),
        ),
        actions: [
          if (inc.costoFinalDecimal != null && inc.costoFinalDecimal! > 0 && (inc.estadoEnum == 'finalizado' || inc.estadoEnum == 'atendido'))
            TextButton(
              onPressed: () async {
                final prefs = await SharedPreferences.getInstance();
                final token = prefs.getString('token') ?? '';
                final url = Uri.parse('${ApiConfig.baseUrl}/pagos/incidente/${inc.idIncidente}/factura?token=$token');
                if (await canLaunchUrl(url)) {
                  await launchUrl(url, mode: LaunchMode.externalApplication);
                } else {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('No se pudo abrir el comprobante.')),
                    );
                  }
                }
              },
              child: Text('Descargar Factura', style: GoogleFonts.inter(color: Colors.lightBlueAccent, fontWeight: FontWeight.bold)),
            ),
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text('Cerrar', style: GoogleFonts.inter(color: const Color(0xFFF59E0B))),
          ),
        ],
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: GoogleFonts.inter(fontSize: 11, color: Colors.white38)),
          const SizedBox(height: 4),
          Text(value, style: GoogleFonts.inter(fontSize: 14, color: Colors.white70, height: 1.3)),
        ],
      ),
    );
  }

  String _formatDate(String isoString) {
    try {
      final dt = DateTime.parse(isoString).toLocal();
      return '${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return isoString;
    }
  }
}
