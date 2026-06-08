import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:uuid/uuid.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../providers/emergencia_provider.dart';
import '../../providers/vehiculo_provider.dart';
import '../../services/location_service.dart';
import '../../services/offline_service.dart';
import '../../models/vehiculo.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_input.dart';

class NuevaEmergenciaScreen extends StatefulWidget {
  const NuevaEmergenciaScreen({super.key});

  @override
  State<NuevaEmergenciaScreen> createState() => _NuevaEmergenciaScreenState();
}

class _NuevaEmergenciaScreenState extends State<NuevaEmergenciaScreen> {
  final _descCtrl = TextEditingController();
  Vehiculo? _selectedVehiculo;
  String? _imagenBase64;
  String? _audioBase64;
  
  double? _lat, _lng;
  bool _loadingLocation = false;
  bool _sending = false;

  final _audioRecorder = AudioRecorder();
  bool _isRecording = false;
  Timer? _connectivityTimer;

  @override
  void initState() {
    super.initState();
    _getLocation();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VehiculoProvider>().loadVehiculos();
    });
  }

  Future<void> _getLocation() async {
    setState(() => _loadingLocation = true);
    try {
      final loc = LocationService();
      await loc.checkPermissions();
      final pos = await loc.getCurrentLocation();
      if (pos != null && mounted) {
        setState(() { _lat = pos.latitude; _lng = pos.longitude; });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error GPS: $e'), backgroundColor: Colors.redAccent),
        );
      }
    }
    if (mounted) setState(() => _loadingLocation = false);
  }

  Future<void> _pickImage() async {
    final cam = await Permission.camera.request();
    if (!cam.isGranted) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Permiso de cámara denegado'), backgroundColor: Colors.redAccent),
        );
      }
      return;
    }
    final picker = ImagePicker();
    final img = await picker.pickImage(source: ImageSource.camera, maxWidth: 800, imageQuality: 70);
    if (img != null) {
      final bytes = await img.readAsBytes();
      setState(() {
        _imagenBase64 = base64Encode(bytes);
      });
    }
  }

  Future<void> _pickGallery() async {
    PermissionStatus status;
    if (Platform.isAndroid) {
      // Android 13+ requires photos permission for gallery access
      if (await Permission.photos.request().isGranted) {
        status = PermissionStatus.granted;
      } else {
        status = await Permission.storage.request();
      }
    } else {
      status = await Permission.photos.request();
    }

    if (!status.isGranted) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Permiso de almacenamiento denegado'), backgroundColor: Colors.redAccent),
        );
      }
      return;
    }
    final picker = ImagePicker();
    final img = await picker.pickImage(source: ImageSource.gallery, maxWidth: 800, imageQuality: 70);
    if (img != null) {
      final bytes = await img.readAsBytes();
      setState(() {
        _imagenBase64 = base64Encode(bytes);
      });
    }
  }

  bool _transcribing = false;

  Future<void> _transcribeAudioAndFillInput(String b64) async {
    setState(() => _transcribing = true);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Row(
          children: [
            SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B)),
            ),
            SizedBox(width: 12),
            Text('Transcribiendo voz a texto...'),
          ],
        ),
        backgroundColor: Color(0xFF1E293B),
        duration: Duration(seconds: 4),
      ),
    );

    try {
      final prov = context.read<EmergenciaProvider>();
      final text = await prov.transcribeAudio(b64);
      if (text != null && text.isNotEmpty) {
        setState(() {
          if (_descCtrl.text.isEmpty) {
            _descCtrl.text = text;
          } else {
            _descCtrl.text += ' ' + text;
          }
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('✓ Transcripción completada e insertada.'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('No se pudo transcribir el audio (audio inaudible o vacío).'),
              backgroundColor: Colors.orangeAccent,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error de transcripción: $e'), backgroundColor: Colors.redAccent),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _transcribing = false);
      }
    }
  }

  Future<void> _toggleRecording() async {
    try {
      if (_isRecording) {
        final path = await _audioRecorder.stop();
        if (path != null) {
          final bytes = await File(path).readAsBytes();
          final b64 = base64Encode(bytes);
          setState(() {
            _audioBase64 = b64;
            _isRecording = false;
          });
          if (mounted) {
            _transcribeAudioAndFillInput(b64);
          }
        }
      } else {
        if (await _audioRecorder.hasPermission()) {
          final dir = await getTemporaryDirectory();
          final path = '${dir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
          await _audioRecorder.start(const RecordConfig(), path: path);
          setState(() => _isRecording = true);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Permiso de micrófono denegado'), backgroundColor: Colors.redAccent),
          );
        }
      }
    } catch (e) {
      debugPrint('Error de grabación: $e');
      setState(() => _isRecording = false);
    }
  }

  void _startOfflineSyncPolling() {
    _connectivityTimer?.cancel();
    _connectivityTimer = Timer.periodic(const Duration(seconds: 5), (timer) async {
      final connectivity = await Connectivity().checkConnectivity();
      final hasInternet = connectivity.any((c) => c != ConnectivityResult.none);
      if (hasInternet) {
        timer.cancel();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Conexión detectada. Sincronizando emergencias...'),
              backgroundColor: Color(0xFF1E293B),
            ),
          );
        }
        final prov = context.read<EmergenciaProvider>();
        await prov.syncOfflineEmergencies();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('✓ Emergencias sincronizadas con el servidor.'),
              backgroundColor: Colors.green,
            ),
          );
          if (prov.activeIncidente != null) {
            Navigator.pushReplacementNamed(context, '/tracking', arguments: prov.activeIncidente);
          } else {
            Navigator.pop(context);
          }
        }
      }
    });
  }

  Future<void> _submit() async {
    if (_selectedVehiculo == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona un vehículo'), backgroundColor: Colors.redAccent),
      );
      return;
    }
    if (_lat == null || _lng == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Esperando ubicación GPS...'), backgroundColor: Colors.orangeAccent),
      );
      return;
    }

    setState(() => _sending = true);

    // Check connectivity
    final connectivity = await Connectivity().checkConnectivity();
    final hasInternet = connectivity.any((c) => c != ConnectivityResult.none);

    if (!hasInternet) {
      // OFFLINE MODE: save locally
      final uuid = const Uuid().v4();
      final offlineService = OfflineService();
      await offlineService.saveEmergency({
        'uuid': uuid,
        'vehiculo_id': _selectedVehiculo!.idVehiculo,
        'descripcion': _descCtrl.text,
        'latitud': _lat,
        'longitud': _lng,
        'imagen_base64': _imagenBase64 ?? '',
        'audio_base64': '',
        'created_at': DateTime.now().toIso8601String(),
      });
      setState(() => _sending = false);
      
      final pendingList = await offlineService.getPendingEmergencies();
      final pendingCount = pendingList.length;
      _startOfflineSyncPolling();

      if (mounted) {
        showDialog(
          context: context,
          builder: (_) => AlertDialog(
            backgroundColor: const Color(0xFF1E293B),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            title: Row(children: [
              const Icon(Icons.cloud_off_rounded, color: Colors.orangeAccent),
              const SizedBox(width: 10),
              Text('Sin Conexión', style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w700)),
            ]),
            content: Text('Tu emergencia fue guardada localmente (Total: $pendingCount pendiente(s) de envío) y se enviará automáticamente cuando recuperes conexión a internet.',
              style: GoogleFonts.inter(color: Colors.white70)),
            actions: [
              TextButton(
                onPressed: () { Navigator.pop(context); Navigator.pop(context); },
                child: const Text('Entendido', style: TextStyle(color: Color(0xFFF59E0B))),
              ),
            ],
          ),
        );
      }
      return;
    }

    // ONLINE MODE: send to backend
    try {
      final emergencia = context.read<EmergenciaProvider>();
      await emergencia.createEmergency(
        vehiculoId: _selectedVehiculo!.idVehiculo!,
        descripcion: _descCtrl.text,
        lat: _lat!,
        lng: _lng!,
        imagenBase64: _imagenBase64,
        audioBase64: null,
      );
      if (mounted) {
        if (emergencia.error != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(emergencia.error!), backgroundColor: Colors.redAccent),
          );
        } else {
          Navigator.pushReplacementNamed(context, '/tracking', arguments: emergencia.activeIncidente);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.redAccent),
        );
      }
    }
    if (mounted) setState(() => _sending = false);
  }

  @override
  void dispose() {
    _descCtrl.dispose();
    _audioRecorder.dispose();
    _connectivityTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final vehiculos = context.watch<VehiculoProvider>();

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white70), onPressed: () => Navigator.pop(context)),
        title: Text('Nueva Emergencia', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // GPS Status
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: _lat != null ? Colors.green.withOpacity(0.3) : Colors.orange.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  Icon(_lat != null ? Icons.gps_fixed_rounded : Icons.gps_not_fixed_rounded,
                    color: _lat != null ? Colors.greenAccent : Colors.orangeAccent),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(_lat != null ? 'Ubicación Detectada' : 'Buscando ubicación...',
                          style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
                        if (_lat != null)
                          Text('${_lat!.toStringAsFixed(4)}, ${_lng!.toStringAsFixed(4)}',
                            style: GoogleFonts.inter(color: Colors.white54, fontSize: 12)),
                      ],
                    ),
                  ),
                  if (_loadingLocation) const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B))),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Vehicle selection
            Text('Vehículo', style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white70)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(12),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<Vehiculo>(
                  isExpanded: true,
                  value: _selectedVehiculo,
                  hint: Text('Selecciona tu vehículo', style: GoogleFonts.inter(color: Colors.white38)),
                  dropdownColor: const Color(0xFF1E293B),
                  items: vehiculos.vehiculos.map((v) => DropdownMenuItem(
                    value: v,
                    child: Text('${v.marca} ${v.modelo} (${v.placa})', style: GoogleFonts.inter(color: Colors.white)),
                  )).toList(),
                  onChanged: (v) => setState(() => _selectedVehiculo = v),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Description
            Text('Describe el problema (Opcional)', style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white70)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: AppInput(
                    label: 'Descripción (Opcional)',
                    hint: 'El vehículo no enciende...',
                    controller: _descCtrl,
                    maxLines: 3,
                  ),
                ),
                const SizedBox(width: 12),
                GestureDetector(
                  onTap: _transcribing ? null : _toggleRecording,
                  child: Container(
                    width: 64,
                    height: 90,
                    decoration: BoxDecoration(
                      color: _isRecording ? Colors.redAccent.withOpacity(0.2) : const Color(0xFF1E293B),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: _isRecording ? Colors.redAccent : Colors.white12),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (_transcribing)
                          const SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B)),
                          )
                        else
                          Icon(
                            _isRecording ? Icons.stop_circle_rounded : Icons.mic_rounded,
                            color: _isRecording ? Colors.redAccent : const Color(0xFFF59E0B),
                            size: 32,
                          ),
                        const SizedBox(height: 4),
                        Text(
                          _transcribing ? 'Procesando' : (_isRecording ? 'Detener' : 'Grabar'),
                          style: GoogleFonts.inter(fontSize: 10, color: Colors.white70),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Photo
            Text('Evidencia Fotográfica', style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white70)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: GestureDetector(
                    onTap: _pickImage,
                    child: Container(
                      height: 100,
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.camera_alt_rounded, color: _imagenBase64 != null ? const Color(0xFFF59E0B) : Colors.white38, size: 32),
                          const SizedBox(height: 6),
                          Text(_imagenBase64 != null ? 'Foto capturada ✓' : 'Cámara',
                            style: GoogleFonts.inter(fontSize: 12, color: _imagenBase64 != null ? const Color(0xFFF59E0B) : Colors.white38)),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: GestureDetector(
                    onTap: _pickGallery,
                    child: Container(
                      height: 100,
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.photo_library_rounded, color: Colors.white38, size: 32),
                          const SizedBox(height: 6),
                          Text('Galería', style: GoogleFonts.inter(fontSize: 12, color: Colors.white38)),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 36),

            AppButton(
              text: 'ENVIAR EMERGENCIA',
              onPressed: _submit,
              isLoading: _sending,
              icon: Icons.emergency_rounded,
            ),
          ],
        ),
      ),
      if (_sending)
        Container(
          color: Colors.black54,
          child: Center(
            child: Card(
              color: const Color(0xFF1E293B),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(color: Color(0xFFF59E0B)),
                    const SizedBox(height: 20),
                    Text('Procesando reporte con IA...',
                      style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                    const SizedBox(height: 8),
                    Text('Por favor, espera unos segundos.',
                      style: GoogleFonts.inter(color: Colors.white70, fontSize: 12)),
                  ],
                ),
              ),
            ),
          ),
        ),
    ],
  ),
);
  }
}

