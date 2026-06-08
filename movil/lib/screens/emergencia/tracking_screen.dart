import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:latlong2/latlong.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:provider/provider.dart';
import '../../models/incidente.dart';
import '../../models/cotizacion.dart';
import '../../providers/emergencia_provider.dart';
import '../../services/websocket_service.dart';
import '../../widgets/status_badge.dart';

class TrackingScreen extends StatefulWidget {
  const TrackingScreen({super.key});

  @override
  State<TrackingScreen> createState() => _TrackingScreenState();
}

class _TrackingScreenState extends State<TrackingScreen> {
  final WebSocketService _ws = WebSocketService();
  final MapController _mapCtrl = MapController();
  StreamSubscription? _wsSub;
  StreamSubscription<bool>? _wsConnSub;
  bool _isWsConnected = false;

  Incidente? _incidente;
  LatLng? _tecnicoPos;
  String _estado = 'pendiente';
  List<Cotizacion> _cotizaciones = [];
  bool _loadingIncident = false;

  double _calculateDistance(LatLng p1, LatLng p2) {
    const double r = 6371.0; // Earth's radius in km
    final double lat1 = p1.latitude * math.pi / 180;
    final double lon1 = p1.longitude * math.pi / 180;
    final double lat2 = p2.latitude * math.pi / 180;
    final double lon2 = p2.longitude * math.pi / 180;

    final double dlat = lat2 - lat1;
    final double dlon = lon2 - lon1;

    final double a = math.sin(dlat / 2) * math.sin(dlat / 2) +
        math.cos(lat1) * math.cos(lat2) *
        math.sin(dlon / 2) * math.sin(dlon / 2);
    final double c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));

    return r * c; // Distance in km
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_incidente == null && !_loadingIncident) {
      final arg = ModalRoute.of(context)?.settings.arguments;
      if (arg is Incidente) {
        _incidente = arg;
        _estado = arg.estadoEnum ?? 'pendiente';
        if (arg.latitudTecnico != null && arg.longitudTecnico != null) {
          _tecnicoPos = LatLng(arg.latitudTecnico!, arg.longitudTecnico!);
          _adjustMapBounds();
        }
        _connectWebSocket();
        _loadCotizaciones();
        // If incident arrived with only an ID, fetch full details
        if (arg.estadoEnum == null && arg.idIncidente != null) {
          _loadFullIncident(arg.idIncidente!);
        }
      }
    }
  }

  Future<void> _loadFullIncident(int id) async {
    _loadingIncident = true;
    try {
      final api = context.read<EmergenciaProvider>();
      final full = await api.loadIncidenteById(id);
      if (full != null && mounted) {
        setState(() {
          _incidente = full;
          _estado = full.estadoEnum ?? _estado;
          if (full.latitudTecnico != null && full.longitudTecnico != null) {
            _tecnicoPos = LatLng(full.latitudTecnico!, full.longitudTecnico!);
            _adjustMapBounds();
          }
        });
      }
    } catch (_) {}
    _loadingIncident = false;
  }

  void _connectWebSocket() {
    if (_incidente == null) return;
    _ws.connect(_incidente!.idIncidente!);
    
    _isWsConnected = _ws.isConnected;
    _wsConnSub = _ws.connectionState.listen((connected) {
      if (mounted) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) {
            setState(() => _isWsConnected = connected);
          }
        });
      }
    });

    _wsSub = _ws.messages.listen((data) {
      final tipo = data['tipo'] ?? data['type'];
      if (tipo == 'conexion') {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(data['mensaje'] ?? 'Conectado al seguimiento en vivo'),
              backgroundColor: Colors.blueGrey.shade800,
              duration: const Duration(seconds: 2),
            ),
          );
        }
      } else if (tipo == 'ubicacion_tecnico') {
        final lat = double.tryParse(data['latitud']?.toString() ?? '');
        final lng = double.tryParse(data['longitud']?.toString() ?? '');
        if (lat != null && lng != null) {
          if (mounted) {
            setState(() {
              _tecnicoPos = LatLng(lat, lng);
            });
            _adjustMapBounds();
          }
        }
      } else if (tipo == 'cambio_estado') {
        final nuevoEstado = data['estado'] ?? _estado;
        if (mounted) {
          setState(() => _estado = nuevoEstado);
        }
        if (_incidente?.idIncidente != null) {
          _loadFullIncident(_incidente!.idIncidente!);
        }
        if (nuevoEstado == 'finalizado' || nuevoEstado == 'atendido') {
          _showFinalizadoDialog();
        }
      } else if (tipo == 'nueva_cotizacion') {
        _loadCotizaciones();
      }
    });
  }

  void _adjustMapBounds() {
    if (_tecnicoPos == null || _incidente == null) return;
    final latEmergencia = _incidente!.latitudEmergencia;
    final lonEmergencia = _incidente!.longitudEmergencia;
    if (latEmergencia == null || lonEmergencia == null) return;

    final clientPos = LatLng(latEmergencia, lonEmergencia);
    final latDiff = (clientPos.latitude - _tecnicoPos!.latitude).abs();
    final lngDiff = (clientPos.longitude - _tecnicoPos!.longitude).abs();

    if (latDiff < 0.0001 && lngDiff < 0.0001) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        try {
          _mapCtrl.move(clientPos, 15.0);
        } catch (e) {
          debugPrint('Error centering map: $e');
        }
      });
      return;
    }

    final bounds = LatLngBounds(clientPos, _tecnicoPos!);
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      try {
        _mapCtrl.fitCamera(
          CameraFit.bounds(
            bounds: bounds,
            padding: const EdgeInsets.all(70.0),
          ),
        );
      } catch (e) {
        debugPrint('Error fitting map bounds: $e');
      }
    });
  }

  Future<void> _loadCotizaciones() async {
    if (_incidente == null) return;
    final prov = context.read<EmergenciaProvider>();
    await prov.loadCotizaciones(_incidente!.idIncidente!);
    if (mounted) {
      setState(() => _cotizaciones = prov.cotizaciones);
    }
  }

  void _showFinalizadoDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(children: [
          const Icon(Icons.check_circle_rounded, color: Colors.greenAccent, size: 28),
          const SizedBox(width: 10),
          Text('¡Servicio Finalizado!', style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w700)),
        ]),
        content: Text('Tu vehículo ha sido atendido exitosamente.\n¿Deseas proceder al pago?',
          style: GoogleFonts.inter(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () { Navigator.pop(context); Navigator.popUntil(context, (route) => route.isFirst); },
            child: const Text('Después', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            onPressed: () { Navigator.pop(context); Navigator.pushReplacementNamed(context, '/pago', arguments: _incidente); },
            child: const Text('Ir a Pagar'),
          ),
        ],
      ),
    );
  }

  Future<void> _aceptarCotizacion(Cotizacion cot) async {
    final prov = context.read<EmergenciaProvider>();
    final success = await prov.aceptarCotizacion(cot.idCotizacion);
    if (mounted && success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('¡Cotización aceptada! Técnico en camino.'), backgroundColor: Colors.green),
      );
      // Reload cotizaciones
      await _loadCotizaciones();
      // Reload full incident details to get the updated estado + tecnico
      if (_incidente?.idIncidente != null) {
        final updated = await prov.loadIncidenteById(_incidente!.idIncidente!);
        if (updated != null && mounted) {
          setState(() {
            _incidente = updated;
            _estado = updated.estadoEnum ?? _estado;
            if (updated.latitudTecnico != null && updated.longitudTecnico != null) {
              _tecnicoPos = LatLng(updated.latitudTecnico!, updated.longitudTecnico!);
              _adjustMapBounds();
            }
          });
        }
      }
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${prov.error ?? "No se pudo aceptar"}'), backgroundColor: Colors.redAccent),
      );
    }
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    _wsConnSub?.cancel();
    _ws.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final emergencyPos = _incidente != null && _incidente!.latitudEmergencia != null
      ? LatLng(_incidente!.latitudEmergencia!, _incidente!.longitudEmergencia!)
      : const LatLng(-17.7833, -63.1821); // SCZ default

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white70),
          onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
        ),
        title: Text('Seguimiento en Vivo', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
        actions: [
          if (!_isWsConnected)
            Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.redAccent.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: Colors.redAccent.withValues(alpha: 0.3)),
              ),
              child: Text(
                'Reconectando...',
                style: GoogleFonts.inter(color: Colors.redAccent, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
          StatusBadge(status: _estado),
          const SizedBox(width: 16),
        ],
      ),
      body: Column(
        children: [
          // Map
          Expanded(
            flex: 3,
            child: FlutterMap(
              mapController: _mapCtrl,
              options: MapOptions(initialCenter: emergencyPos, initialZoom: 14.5),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.tallerpro.app',
                ),
                MarkerLayer(
                  markers: [
                    Marker(
                      point: emergencyPos,
                      width: 40, height: 40,
                      child: const Icon(Icons.location_on_rounded, color: Colors.redAccent, size: 40),
                    ),
                    if (_tecnicoPos != null)
                      Marker(
                        point: _tecnicoPos!,
                        width: 40, height: 40,
                        child: Container(
                          decoration: BoxDecoration(
                            color: const Color(0xFFF59E0B),
                            shape: BoxShape.circle,
                            boxShadow: [BoxShadow(color: const Color(0xFFF59E0B).withOpacity(0.4), blurRadius: 12)],
                          ),
                          child: const Icon(Icons.build_rounded, color: Color(0xFF0F172A), size: 22),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),

          // Bottom panel
          Expanded(
            flex: 2,
            child: Container(
              decoration: const BoxDecoration(
                color: Color(0xFF0F172A),
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(width: 40, height: 4,
                        decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
                    ),
                    const SizedBox(height: 16),

                    // Estado y Botón Llamar
                    Row(
                      children: [
                        const Icon(Icons.info_outline_rounded, color: Color(0xFFF59E0B), size: 20),
                        const SizedBox(width: 8),
                        Text('Estado: ', style: GoogleFonts.inter(color: Colors.white54, fontSize: 14)),
                        StatusBadge(status: _estado),
                        const Spacer(),
                        if (_estado == 'taller asignado' || _estado == 'en camino' || _estado == 'en atención' || _estado == 'taller_asignado' || _estado == 'en_proceso' || _estado == 'en_camino' || _estado == 'en_atencion')
                          IconButton(
                            icon: const Icon(Icons.phone_in_talk_rounded, color: Colors.greenAccent),
                            onPressed: () async {
                              final telNum = _incidente?.tallerTelefono ?? '77777777';
                              final Uri tel = Uri.parse('tel:$telNum');
                              if (await canLaunchUrl(tel)) {
                                await launchUrl(tel);
                              }
                            },
                          ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // Diagnóstico IA
                    if (_incidente?.clasificacionIa != null && _incidente!.clasificacionIa != 'Sin procesar') ...[
                      Container(
                        width: double.infinity,
                        margin: const EdgeInsets.only(bottom: 16),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E293B),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFF3B82F6).withOpacity(0.3)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                const Icon(Icons.psychology_rounded, color: Color(0xFF3B82F6), size: 22),
                                const SizedBox(width: 8),
                                Text('Diagnóstico Inteligente (IA)',
                                  style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                              ],
                            ),
                            const SizedBox(height: 10),
                            Text(
                              _incidente!.clasificacionIa!,
                              style: GoogleFonts.inter(color: Colors.white70, fontSize: 13, height: 1.4),
                            ),
                          ],
                        ),
                      ),
                    ],

                    // Técnico / Taller Info (when assigned)
                    if (_estado == 'en_proceso' || _estado == 'en_camino' || _estado == 'en_atencion') ...[
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [const Color(0xFFF59E0B).withOpacity(0.15), const Color(0xFF1E293B)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFFF59E0B).withOpacity(0.3)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 44, height: 44,
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFF59E0B).withOpacity(0.2),
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(Icons.build_rounded, color: Color(0xFFF59E0B), size: 22),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('Técnico en Camino',
                                        style: GoogleFonts.inter(color: const Color(0xFFF59E0B), fontWeight: FontWeight.w700, fontSize: 15)),
                                      const SizedBox(height: 4),
                                      Text(_incidente?.tallerNombre ?? 'Taller asignado',
                                        style: GoogleFonts.inter(color: Colors.white70, fontSize: 13)),
                                    ],
                                  ),
                                ),
                                if (_tecnicoPos != null)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                    decoration: BoxDecoration(
                                      color: Colors.greenAccent.withOpacity(0.15),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text('EN VIVO', style: GoogleFonts.inter(color: Colors.greenAccent, fontSize: 11, fontWeight: FontWeight.w700)),
                                  ),
                              ],
                            ),
                            if (_tecnicoPos != null) ...[
                              const Padding(
                                padding: EdgeInsets.symmetric(vertical: 10),
                                child: Divider(color: Colors.white10, height: 1),
                              ),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  if (_incidente?.latitudTaller != null && _incidente?.longitudTaller != null) ...[
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text('Al taller:', style: GoogleFonts.inter(color: Colors.white38, fontSize: 11)),
                                          const SizedBox(height: 4),
                                          Row(
                                            children: [
                                              const Icon(Icons.store_rounded, color: Colors.orangeAccent, size: 14),
                                              const SizedBox(width: 4),
                                              Text(
                                                '${_calculateDistance(_tecnicoPos!, LatLng(_incidente!.latitudTaller!, _incidente!.longitudTaller!)).toStringAsFixed(1)} km',
                                                style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                                              ),
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                  if (_incidente?.latitudEmergencia != null && _incidente?.longitudEmergencia != null) ...[
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.end,
                                        children: [
                                          Text('A tu ubicación:', style: GoogleFonts.inter(color: Colors.white38, fontSize: 11)),
                                          const SizedBox(height: 4),
                                          Row(
                                            mainAxisAlignment: MainAxisAlignment.end,
                                            children: [
                                              const Icon(Icons.directions_car_rounded, color: Colors.greenAccent, size: 14),
                                              const SizedBox(width: 4),
                                              Text(
                                                '${_calculateDistance(_tecnicoPos!, LatLng(_incidente!.latitudEmergencia!, _incidente!.longitudEmergencia!)).toStringAsFixed(1)} km (${((_calculateDistance(_tecnicoPos!, LatLng(_incidente!.latitudEmergencia!, _incidente!.longitudEmergencia!)) / 40) * 60).round()} min)',
                                                style: GoogleFonts.inter(color: Colors.greenAccent, fontWeight: FontWeight.w700, fontSize: 13),
                                              ),
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ],
                            if (_incidente?.tecnicoNombre != null) ...[
                              const Padding(
                                padding: EdgeInsets.symmetric(vertical: 12),
                                child: Divider(color: Colors.white12, height: 1),
                              ),
                              Row(
                                children: [
                                  CircleAvatar(
                                    radius: 18,
                                    backgroundColor: Colors.white10,
                                    child: Text(_incidente!.tecnicoNombre!.substring(0, 1).toUpperCase(),
                                      style: GoogleFonts.inter(color: Colors.white70, fontWeight: FontWeight.bold)),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(_incidente!.tecnicoNombre!,
                                          style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
                                        const SizedBox(height: 2),
                                        Text(_incidente!.tecnicoEspecialidad ?? 'Mecánico General',
                                          style: GoogleFonts.inter(color: Colors.white38, fontSize: 12)),
                                      ],
                                    ),
                                  ),
                                  if (_incidente!.tecnicoTelefono != null)
                                    IconButton(
                                      icon: const Icon(Icons.phone_android_rounded, color: Colors.greenAccent),
                                      tooltip: 'Llamar al técnico',
                                      onPressed: () async {
                                        final Uri tel = Uri.parse('tel:${_incidente!.tecnicoTelefono}');
                                        if (await canLaunchUrl(tel)) {
                                          await launchUrl(tel);
                                        }
                                      },
                                    ),
                                ],
                              ),
                            ],
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ] else if (_estado == 'taller_asignado') ...[
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E293B),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: Colors.orange.withOpacity(0.3)),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 44, height: 44,
                              decoration: BoxDecoration(
                                color: Colors.orange.withOpacity(0.2),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.store_rounded, color: Colors.orange, size: 22),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Taller Asignado',
                                    style: GoogleFonts.inter(color: Colors.orange, fontWeight: FontWeight.w700, fontSize: 15)),
                                  const SizedBox(height: 4),
                                  Text(_incidente?.tallerNombre ?? 'Taller asignado',
                                    style: GoogleFonts.inter(color: Colors.white70, fontSize: 13)),
                                  const SizedBox(height: 4),
                                  Text('Esperando asignación de mecánico...',
                                    style: GoogleFonts.inter(color: Colors.white38, fontSize: 11, fontStyle: FontStyle.italic)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Cotizaciones
                    if (_cotizaciones.isNotEmpty) ...[
                      Text('Cotizaciones Recibidas', style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white)),
                      const SizedBox(height: 10),
                      ..._cotizaciones.map((cot) => Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E293B),
                          borderRadius: BorderRadius.circular(12),
                          border: cot.estado == 'aceptada' ? Border.all(color: Colors.greenAccent.withOpacity(0.4)) : null,
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(cot.tallerNombre ?? 'Taller #${cot.tallerId}',
                                    style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
                                  const SizedBox(height: 4),
                                  Text('Bs. ${cot.precioEstimado.toStringAsFixed(0)} • ${cot.tiempoEstimadoMin} min',
                                    style: GoogleFonts.inter(color: const Color(0xFFF59E0B), fontWeight: FontWeight.w700, fontSize: 16)),
                                  if (cot.descripcion != null)
                                    Text(cot.descripcion!, style: GoogleFonts.inter(color: Colors.white54, fontSize: 12), maxLines: 2),
                                ],
                              ),
                            ),
                            if (cot.estado == 'pendiente')
                              ElevatedButton(
                                onPressed: () => _aceptarCotizacion(cot),
                                style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8)),
                                child: const Text('Aceptar'),
                              )
                            else if (cot.estado == 'aceptada')
                              const Icon(Icons.check_circle_rounded, color: Colors.greenAccent),
                          ],
                        ),
                      )),
                    ] else ...[
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(color: const Color(0xFF1E293B), borderRadius: BorderRadius.circular(12)),
                        child: Row(
                          children: [
                            const SizedBox(width: 20, height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B))),
                            const SizedBox(width: 14),
                            Expanded(child: Text('Esperando cotizaciones de talleres cercanos...',
                              style: GoogleFonts.inter(color: Colors.white54, fontSize: 13))),
                          ],
                        ),
                      ),
                    ],

                    if (_estado == 'pendiente' || _estado == 'cotizando') ...[
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        child: TextButton.icon(
                          icon: const Icon(Icons.cancel_rounded, color: Colors.redAccent),
                          label: Text('Cancelar Solicitud', style: GoogleFonts.inter(color: Colors.redAccent, fontWeight: FontWeight.bold)),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            backgroundColor: Colors.redAccent.withOpacity(0.1),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                          onPressed: () async {
                            final confirm = await showDialog<bool>(
                              context: context,
                              builder: (ctx) => AlertDialog(
                                backgroundColor: const Color(0xFF1E293B),
                                title: const Text('Cancelar Emergencia', style: TextStyle(color: Colors.white)),
                                content: const Text('¿Estás seguro que deseas cancelar esta solicitud?', style: TextStyle(color: Colors.white70)),
                                actions: [
                                  TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('No', style: TextStyle(color: Colors.white54))),
                                  TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Sí, cancelar', style: TextStyle(color: Colors.redAccent))),
                                ],
                              ),
                            );

                            if (confirm == true && mounted) {
                              final prov = context.read<EmergenciaProvider>();
                              final success = await prov.cancelarEmergencia(_incidente!.idIncidente!);
                              if (success && mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Solicitud cancelada exitosamente'), backgroundColor: Colors.green),
                                );
                                Navigator.popUntil(context, (route) => route.isFirst);
                              } else if (mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Error al cancelar: ${prov.error}'), backgroundColor: Colors.redAccent),
                                );
                              }
                            }
                          },
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
