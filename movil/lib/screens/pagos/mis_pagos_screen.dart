import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../models/pago.dart';
import '../../models/incidente.dart';
import '../../config/api_config.dart';
import '../../services/api_service.dart';
import '../../services/storage_service.dart';
import '../../providers/auth_provider.dart';
import '../../providers/emergencia_provider.dart';

class MisPagosScreen extends StatefulWidget {
  const MisPagosScreen({super.key});

  @override
  State<MisPagosScreen> createState() => _MisPagosScreenState();
}

class _MisPagosScreenState extends State<MisPagosScreen> {
  bool _isLoading = true;
  List<Pago> _pagos = [];

  @override
  void initState() {
    super.initState();
    // Usar Microtask para llamar al provider después del primer build
    Future.microtask(() => _loadPagos());
  }

  Future<void> _loadPagos() async {
    if (!mounted) return;
    setState(() => _isLoading = true);
    try {
      final api = context.read<EmergenciaProvider>().apiService;
      final res = await api.get('/pagos/historial/cliente');
      if (res.data is List) {
        setState(() {
          _pagos = (res.data as List).map((p) => Pago.fromJson(p)).toList();
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error cargando pagos: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _abrirFactura(Pago pago) async {
    setState(() => _isLoading = true);
    try {
      final storage = StorageService();
      await storage.init();
      final token = await storage.getToken();

      if (token == null) {
        throw 'No se pudo obtener el token de sesión.';
      }

      // El endpoint en el backend es: /pagos/incidente/{id_incidente}/factura?token=xxx
      final baseUrl = ApiConfig.baseUrl;
      final urlStr = '$baseUrl/pagos/incidente/${pago.incidenteId}/factura?token=$token';

      final Uri url = Uri.parse(urlStr);
      if (await canLaunchUrl(url)) {
        await launchUrl(url, mode: LaunchMode.externalApplication);
      } else {
        throw 'No se pudo abrir el navegador para descargar la factura.';
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Clasificar pagos
    final pendientes = _pagos.where((p) => p.estadoPago == 'pendiente').toList();
    final completados = _pagos.where((p) => p.estadoPago != 'pendiente').toList();

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white70),
            onPressed: () => Navigator.pop(context),
          ),
          title: Text('Mis Pagos', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
          bottom: const TabBar(
            indicatorColor: Color(0xFFF59E0B),
            labelColor: Color(0xFFF59E0B),
            unselectedLabelColor: Colors.white54,
            tabs: [
              Tab(text: 'Pendientes'),
              Tab(text: 'Finalizados'),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                children: [
                  _buildList(pendientes, isPending: true),
                  _buildList(completados, isPending: false),
                ],
              ),
      ),
    );
  }

  Widget _buildList(List<Pago> list, {required bool isPending}) {
    if (list.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(isPending ? Icons.receipt_long : Icons.check_circle_outline, 
                size: 64, color: Colors.white24),
            const SizedBox(height: 16),
            Text(
              isPending ? 'No tienes pagos pendientes.' : 'No tienes pagos registrados.',
              style: GoogleFonts.inter(color: Colors.white54, fontSize: 16),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadPagos,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: list.length,
        itemBuilder: (context, i) {
          final p = list[i];
          return Container(
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Orden #${p.incidenteId}', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 16)),
                    Text('${p.montoTotal} Bs.', style: GoogleFonts.inter(color: Colors.greenAccent, fontWeight: FontWeight.bold, fontSize: 18)),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Método: ${p.metodo}', style: GoogleFonts.inter(color: Colors.white70, fontSize: 14)),
                Text('Fecha: ${p.fechaPago != null ? p.fechaPago.toString().split('.')[0] : 'N/A'}', 
                  style: GoogleFonts.inter(color: Colors.white54, fontSize: 13)),
                
                const SizedBox(height: 16),
                if (isPending)
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF59E0B),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      icon: const Icon(Icons.payment, color: Color(0xFF0F172A)),
                      label: Text('Pagar Ahora', style: GoogleFonts.inter(color: const Color(0xFF0F172A), fontWeight: FontWeight.bold)),
                      onPressed: () {
                        // Navegar a la pantalla de pago detallada pero con un objeto incidente dummy solo con ID
                        final dummyIncidente = Incidente(
                          idIncidente: p.incidenteId,
                          estadoEnum: 'finalizado',
                        );
                        Navigator.pushNamed(context, '/pago', arguments: dummyIncidente);
                      },
                    ),
                  )
                else
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Color(0xFF3B82F6)),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      icon: const Icon(Icons.receipt, color: Color(0xFF3B82F6)),
                      label: Text('Ver Factura', style: GoogleFonts.inter(color: Color(0xFF3B82F6), fontWeight: FontWeight.bold)),
                      onPressed: () => _abrirFactura(p),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
