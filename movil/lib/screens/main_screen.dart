import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../widgets/bottom_nav.dart';
import 'home/home_screen.dart';
import 'vehiculos/vehiculos_screen.dart';
import 'notificaciones/notificaciones_screen.dart';
import 'perfil/perfil_screen.dart';
import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:permission_handler/permission_handler.dart';
import '../providers/emergencia_provider.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  
  final List<Widget> _screens = [
    const HomeScreen(),
    const VehiculosScreen(),
    const NotificacionesScreen(),
    const PerfilScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _requestInitialPermissions();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _requestInitialPermissions() async {
    // Pedir permisos obligatorios al inicio (Storage se ignora en Android 13+)
    Map<Permission, PermissionStatus> statuses = await [
      Permission.location,
      Permission.microphone,
      Permission.camera,
    ].request();

    if (statuses[Permission.location] != PermissionStatus.granted ||
        statuses[Permission.microphone] != PermissionStatus.granted ||
        statuses[Permission.camera] != PermissionStatus.granted) {
      if (mounted) {
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (_) => AlertDialog(
            backgroundColor: const Color(0xFF1E293B),
            title: const Text('Permisos Requeridos', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            content: const Text(
              'La aplicación necesita permisos de ubicación, micrófono y cámara para registrar emergencias correctamente. Por favor, otórgalos en la configuración.',
              style: TextStyle(color: Colors.white70),
            ),
            actions: [
              TextButton(
                onPressed: () {
                  openAppSettings();
                  Navigator.pop(context);
                },
                child: const Text('Abrir Configuración', style: TextStyle(color: Color(0xFFF59E0B))),
              ),
              TextButton(
                onPressed: () {
                  context.read<AuthProvider>().logout();
                },
                child: const Text('Cerrar Sesión', style: TextStyle(color: Colors.redAccent)),
              ),
            ],
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNav(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
      ),
    );
  }
}
