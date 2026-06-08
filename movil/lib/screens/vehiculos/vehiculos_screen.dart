import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../providers/vehiculo_provider.dart';
import '../../widgets/app_button.dart';

class VehiculosScreen extends StatefulWidget {
  const VehiculosScreen({super.key});

  @override
  State<VehiculosScreen> createState() => _VehiculosScreenState();
}

class _VehiculosScreenState extends State<VehiculosScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VehiculoProvider>().loadVehiculos();
    });
  }

  Future<void> _deleteVehiculo(int id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: Text('Eliminar Vehículo', style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Text('¿Está seguro de que desea eliminar este vehículo?', style: GoogleFonts.inter(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('Cancelar', style: GoogleFonts.inter(color: Colors.white54)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text('Eliminar', style: GoogleFonts.inter(color: Colors.redAccent, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      final success = await context.read<VehiculoProvider>().deleteVehiculo(id);
      if (mounted) {
        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Vehículo eliminado con éxito'), backgroundColor: Colors.green),
          );
        } else {
          final error = context.read<VehiculoProvider>().error ?? 'Error al eliminar vehículo';
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(error), backgroundColor: Colors.redAccent),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<VehiculoProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text('Mis Vehículos', style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: provider.isLoading && provider.vehiculos.isEmpty
            ? const Center(child: CircularProgressIndicator(color: Color(0xFFF59E0B)))
            : RefreshIndicator(
                color: const Color(0xFFF59E0B),
                onRefresh: () => provider.loadVehiculos(),
                child: provider.vehiculos.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.directions_car_rounded, size: 72, color: Colors.white24),
                            const SizedBox(height: 16),
                            Text('No tienes vehículos registrados',
                                style: GoogleFonts.inter(fontSize: 16, color: Colors.white54)),
                            const SizedBox(height: 24),
                            SizedBox(
                              width: 200,
                              child: AppButton(
                                text: 'Agregar Vehículo',
                                onPressed: () => Navigator.pushNamed(context, '/vehiculo-form'),
                                icon: Icons.add_rounded,
                              ),
                            )
                          ],
                        ),
                      )
                    : Column(
                        children: [
                          Expanded(
                            child: ListView.builder(
                              padding: const EdgeInsets.all(24),
                              itemCount: provider.vehiculos.length,
                              itemBuilder: (context, index) {
                                final v = provider.vehiculos[index];
                                return Container(
                                  margin: const EdgeInsets.only(bottom: 16),
                                  padding: const EdgeInsets.all(20),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF1E293B),
                                    borderRadius: BorderRadius.circular(16),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.black.withOpacity(0.15),
                                        blurRadius: 10,
                                        offset: const Offset(0, 4),
                                      ),
                                    ],
                                  ),
                                  child: Row(
                                    children: [
                                      Container(
                                        width: 52,
                                        height: 52,
                                        decoration: BoxDecoration(
                                          color: const Color(0xFFF59E0B).withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: const Icon(Icons.directions_car_rounded, color: Color(0xFFF59E0B), size: 28),
                                      ),
                                      const SizedBox(width: 16),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              '${v.marca} ${v.modelo}',
                                              style: GoogleFonts.inter(
                                                  fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              'Placa: ${v.placa} • Color: ${v.color}',
                                              style: GoogleFonts.inter(fontSize: 13, color: Colors.white54),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Row(
                                        children: [
                                          IconButton(
                                            icon: const Icon(Icons.edit_outlined, color: Colors.white70),
                                            onPressed: () => Navigator.pushNamed(context, '/vehiculo-form', arguments: v),
                                          ),
                                          IconButton(
                                            icon: const Icon(Icons.delete_outline_rounded, color: Colors.redAccent),
                                            onPressed: () {
                                              if (v.idVehiculo != null) {
                                                _deleteVehiculo(v.idVehiculo!);
                                              }
                                            },
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                );
                              },
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                            child: AppButton(
                              text: 'Agregar Vehículo',
                              onPressed: () => Navigator.pushNamed(context, '/vehiculo-form'),
                              icon: Icons.add_rounded,
                            ),
                          ),
                        ],
                      ),
              ),
      ),
    );
  }
}
