import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../providers/notificacion_provider.dart';
import '../../widgets/bottom_nav.dart';

class NotificacionesScreen extends StatefulWidget {
  const NotificacionesScreen({super.key});

  @override
  State<NotificacionesScreen> createState() => _NotificacionesScreenState();
}

class _NotificacionesScreenState extends State<NotificacionesScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<NotificacionProvider>().loadNotificaciones();
      context.read<NotificacionProvider>().loadUnreadCount();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<NotificacionProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text('Notificaciones', style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: provider.isLoading && provider.notificaciones.isEmpty
            ? const Center(child: CircularProgressIndicator(color: Color(0xFFF59E0B)))
            : RefreshIndicator(
                color: const Color(0xFFF59E0B),
                onRefresh: () async {
                  await provider.loadNotificaciones();
                  await provider.loadUnreadCount();
                },
                child: provider.notificaciones.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.notifications_none_rounded, size: 72, color: Colors.white24),
                            const SizedBox(height: 16),
                            Text('No tienes notificaciones',
                                style: GoogleFonts.inter(fontSize: 16, color: Colors.white54)),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(24),
                        itemCount: provider.notificaciones.length,
                        itemBuilder: (context, index) {
                          final n = provider.notificaciones[index];
                          return GestureDetector(
                            onTap: () {
                              if (!n.leido) {
                                provider.marcarLeida(n.idNotificacion);
                              }
                            },
                            child: Container(
                              margin: const EdgeInsets.only(bottom: 16),
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: n.leido ? const Color(0xFF1E293B) : const Color(0xFF1E293B).withOpacity(0.8),
                                borderRadius: BorderRadius.circular(16),
                                border: n.leido
                                    ? null
                                    : Border.all(color: const Color(0xFFF59E0B).withOpacity(0.3), width: 1.5),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.15),
                                    blurRadius: 10,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    width: 44,
                                    height: 44,
                                    decoration: BoxDecoration(
                                      color: n.leido
                                          ? Colors.white.withOpacity(0.05)
                                          : const Color(0xFFF59E0B).withOpacity(0.15),
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      n.leido ? Icons.notifications_outlined : Icons.notifications_active_rounded,
                                      color: n.leido ? Colors.white54 : const Color(0xFFF59E0B),
                                      size: 22,
                                    ),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Expanded(
                                              child: Text(
                                                n.titulo,
                                                style: GoogleFonts.inter(
                                                  fontSize: 15,
                                                  fontWeight: n.leido ? FontWeight.w600 : FontWeight.w800,
                                                  color: n.leido ? Colors.white.withOpacity(0.9) : Colors.white,
                                                ),
                                              ),
                                            ),
                                            if (!n.leido)
                                              Container(
                                                width: 8,
                                                height: 8,
                                                decoration: const BoxDecoration(
                                                  color: Color(0xFFF59E0B),
                                                  shape: BoxShape.circle,
                                                ),
                                              ),
                                          ],
                                        ),
                                        const SizedBox(height: 6),
                                        Text(
                                          n.mensaje,
                                          style: GoogleFonts.inter(
                                            fontSize: 13,
                                            color: n.leido ? Colors.white54 : Colors.white70,
                                            height: 1.4,
                                          ),
                                        ),
                                        if (n.fechaCreacion != null) ...[
                                          const SizedBox(height: 10),
                                          Text(
                                            _formatDate(n.fechaCreacion!),
                                            style: GoogleFonts.inter(fontSize: 11, color: Colors.white38),
                                          ),
                                        ]
                                      ],
                                    ),
                                  ),
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

  String _formatDate(String isoString) {
    try {
      final dt = DateTime.parse(isoString).toLocal();
      return '${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return isoString;
    }
  }
}
