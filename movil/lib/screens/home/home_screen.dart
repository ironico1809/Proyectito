import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../providers/emergencia_provider.dart';
import '../../providers/notificacion_provider.dart';
import '../../providers/taller_provider.dart';
import '../../services/location_service.dart';
import '../../models/incidente.dart';
import '../../widgets/status_badge.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../../services/websocket_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _locationService = LocationService();
  Position? _currentPosition;
  final MapController _mapController = MapController();
  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;
  bool _isSyncing = false;
  bool _wasOffline = false;

  WebSocketService? _wsHome;
  StreamSubscription? _wsHomeSub;
  int? _connectedIncidenteId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<EmergenciaProvider>().loadActiveEmergency();
      context.read<NotificacionProvider>().loadUnreadCount();
      context.read<TallerProvider>().loadTalleresCercanos();
      _initLocation();
      _checkInitialSync();
      _setupConnectivityListener();
    });
  }

  @override
  void dispose() {
    _connectivitySub?.cancel();
    _wsHomeSub?.cancel();
    _wsHome?.disconnect();
    super.dispose();
  }

  void _updateWebSocketAndNavigation() {
    final isCurrent = ModalRoute.of(context)?.isCurrent ?? false;
    final emergencia = Provider.of<EmergenciaProvider>(context, listen: false);
    final activeInc = emergencia.activeIncidente;

    if (!isCurrent || activeInc == null || activeInc.idIncidente == null) {
      if (_connectedIncidenteId != null) {
        _wsHome?.disconnect();
        _wsHomeSub?.cancel();
        _wsHome = null;
        _wsHomeSub = null;
        _connectedIncidenteId = null;
      }
      return;
    }

    final id = activeInc.idIncidente!;
    if (_connectedIncidenteId != id) {
      _wsHome?.disconnect();
      _wsHomeSub?.cancel();
      
      _connectedIncidenteId = id;
      _wsHome = WebSocketService();
      _wsHome!.connect(id);

      _wsHomeSub = _wsHome!.messages.listen((data) {
        final tipo = data['tipo'] ?? data['type'];
        if (tipo == 'cambio_estado') {
          emergencia.loadActiveEmergency();
        }
      });
    }
  }

  Future<void> _checkInitialSync() async {
    final prov = context.read<EmergenciaProvider>();
    await prov.loadPendingOfflineCount();
    final results = await Connectivity().checkConnectivity();
    final hasInternet = results.any((r) => r != ConnectivityResult.none);
    if (hasInternet && prov.pendingOfflineCount > 0) {
      setState(() => _isSyncing = true);
      await prov.syncOfflineEmergencies();
      setState(() => _isSyncing = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('✓ Emergencias sincronizadas exitosamente'),
            backgroundColor: Colors.green.shade700,
          ),
        );
      }
    }
  }

  void _setupConnectivityListener() {
    final prov = context.read<EmergenciaProvider>();
    _connectivitySub = Connectivity().onConnectivityChanged.listen((results) async {
      final hasInternet = results.any((r) => r != ConnectivityResult.none);
      
      if (hasInternet && _wasOffline) {
        final pending = prov.pendingOfflineCount;
        if (pending > 0) {
          setState(() => _isSyncing = true);
          await prov.syncOfflineEmergencies();
          setState(() => _isSyncing = false);
          
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: const Text('✓ Emergencias sincronizadas exitosamente'),
                backgroundColor: Colors.green.shade700,
              ),
            );
          }
        }
      }
      
      _wasOffline = !hasInternet;
    });
  }

  Future<void> _initLocation() async {
    final hasPermission = await _locationService.checkPermissions();
    if (hasPermission) {
      try {
        final position = await _locationService.getCurrentLocation();
        if (position != null) {
          setState(() => _currentPosition = position);
          _mapController.move(LatLng(position.latitude, position.longitude), 14.0);
        }
      } catch (e) {
        debugPrint('Error de ubicación: $e');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    _updateWebSocketAndNavigation();
    final auth = context.watch<AuthProvider>();
    final emergencia = context.watch<EmergenciaProvider>();
    final notif = context.watch<NotificacionProvider>();

    return Scaffold(
      body: Stack(
        children: [
          // 1. FULL SCREEN MAP
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _currentPosition != null 
                  ? LatLng(_currentPosition!.latitude, _currentPosition!.longitude)
                  : const LatLng(-17.7833, -63.1821),
              initialZoom: 14.0,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.tallerpro.app',
              ),
              MarkerLayer(
                markers: [
                  if (_currentPosition != null)
                    Marker(
                      point: LatLng(_currentPosition!.latitude, _currentPosition!.longitude),
                      width: 50,
                      height: 50,
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.blueAccent.withValues(alpha: 0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Center(
                          child: Icon(Icons.my_location_rounded, color: Colors.blueAccent, size: 28),
                        ),
                      ),
                    ),
                  ...context.watch<TallerProvider>().talleresCercanos.map((t) => Marker(
                        point: LatLng(t.latitudDecimal, t.longitudDecimal),
                        width: 40,
                        height: 40,
                        child: GestureDetector(
                          onTap: () {
                            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                              content: Text('🔧 ${t.nombreTaller}\n📍 ${t.direccion}'),
                              duration: const Duration(seconds: 4),
                              backgroundColor: const Color(0xFF1E293B),
                            ));
                          },
                          child: Container(
                            decoration: BoxDecoration(
                              color: const Color(0xFFF59E0B),
                              shape: BoxShape.circle,
                              border: Border.all(color: Colors.white, width: 2),
                            ),
                            child: const Icon(Icons.handyman_rounded, color: Colors.white, size: 20),
                          ),
                        ),
                      )),
                ],
              ),
            ],
          ),

          // 2. TOP BAR (Greeting & Notifications)
          SafeArea(
            child: Align(
              alignment: Alignment.topCenter,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_isSyncing)
                      Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E293B).withValues(alpha: 0.9),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFFF59E0B), width: 1.5),
                          boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 8, offset: Offset(0, 4))],
                        ),
                        child: Row(
                          children: [
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B)),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Sincronizando emergencias pendientes...',
                                style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                              ),
                            ),
                          ],
                        ),
                      )
                    else if (emergencia.pendingOfflineCount > 0)
                      Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                          color: Colors.orangeAccent.withValues(alpha: 0.9),
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 8, offset: Offset(0, 4))],
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.cloud_off_rounded, color: Colors.white),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Tienes ${emergencia.pendingOfflineCount} emergencia(s) pendiente(s) de envío.',
                                style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                              ),
                            ),
                          ],
                        ),
                      ),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F172A).withValues(alpha: 0.9),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: const [
                          BoxShadow(color: Colors.black26, blurRadius: 10, offset: Offset(0, 4))
                        ],
                      ),
                      child: Row(
                    children: [
                      Container(
                        width: 48, height: 48,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(colors: [Color(0xFFF59E0B), Color(0xFFD97706)]),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Center(
                          child: Text(
                            auth.currentUser?.nombre.isNotEmpty == true ? auth.currentUser!.nombre[0].toUpperCase() : 'U',
                            style: GoogleFonts.inter(fontSize: 20, fontWeight: FontWeight.w800, color: const Color(0xFF0F172A)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('Hola, ${auth.currentUser?.nombre ?? 'Usuario'}',
                              style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white)),
                            Text('Bienvenido a TallerPro',
                              style: GoogleFonts.inter(fontSize: 12, color: Colors.white54)),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.history_rounded, color: Colors.white70, size: 28),
                        onPressed: () => Navigator.pushNamed(context, '/historial'),
                      ),
                      IconButton(
                        icon: const Icon(Icons.payments_rounded, color: Colors.white70, size: 28),
                        onPressed: () => Navigator.pushNamed(context, '/mis_pagos'),
                      ),
                    ],
                  ),
                    ),
                    if (emergencia.activeIncidente != null) ...[
                      const SizedBox(height: 12),
                      _buildActiveEmergencyCard(emergencia.activeIncidente!),
                    ],
                  ],
                ),
              ),
            ),
          ),

          // 4. EMERGENCY BUTTON (Floating at the bottom)
          SafeArea(
            child: Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/nueva-emergencia'),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFFF59E0B), Color(0xFFEF4444)],
                        begin: Alignment.topLeft, end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(color: const Color(0xFFF59E0B).withValues(alpha: 0.3), blurRadius: 20, offset: const Offset(0, 8)),
                      ],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 48, height: 48,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.2),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.emergency_rounded, color: Colors.white, size: 28),
                        ),
                        const SizedBox(width: 16),
                        Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('SOLICITAR AUXILIO', style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w800, color: Colors.white, letterSpacing: 1)),
                            Text('Toca para reportar emergencia', style: GoogleFonts.inter(fontSize: 12, color: Colors.white70)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),

          // Botón flotante pequeño para recargar GPS
          SafeArea(
            child: Align(
              alignment: Alignment.bottomRight,
              child: Padding(
                padding: const EdgeInsets.only(bottom: 110, right: 24),
                child: FloatingActionButton(
                  heroTag: 'gps_btn',
                  mini: true,
                  backgroundColor: const Color(0xFF0F172A).withValues(alpha: 0.9),
                  child: const Icon(Icons.my_location_rounded, color: Color(0xFFF59E0B)),
                  onPressed: () async {
                    final tallerProvider = context.read<TallerProvider>();
                    await _initLocation();
                    await tallerProvider.loadTalleresCercanos();
                  },
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActiveEmergencyCard(Incidente inc) {
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, '/tracking', arguments: inc),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B).withValues(alpha: 0.95),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFF59E0B).withValues(alpha: 0.5), width: 2),
          boxShadow: [
             const BoxShadow(color: Colors.black26, blurRadius: 8, offset: Offset(0, 4))
          ]
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                StatusBadge(status: inc.estadoEnum ?? 'pendiente'),
                const Spacer(),
                const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white38, size: 16),
              ],
            ),
            const SizedBox(height: 12),
            if (inc.descripcionTexto != null)
              Text(inc.descripcionTexto!, style: GoogleFonts.inter(fontSize: 14, color: Colors.white70), maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 8),
            if (inc.tallerNombre != null)
              Row(
                children: [
                  const Icon(Icons.handyman_rounded, color: Color(0xFFF59E0B), size: 16),
                  const SizedBox(width: 6),
                  Text(inc.tallerNombre!, style: GoogleFonts.inter(fontSize: 13, color: Color(0xFFF59E0B), fontWeight: FontWeight.w600)),
                ],
              ),
            const SizedBox(height: 8),
            Text('Toca para ver seguimiento en vivo →', style: GoogleFonts.inter(fontSize: 12, color: Colors.white38)),
          ],
        ),
      ),
    );
  }
}
