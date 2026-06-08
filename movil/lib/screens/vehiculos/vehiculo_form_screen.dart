import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../providers/vehiculo_provider.dart';
import '../../models/vehiculo.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_input.dart';

class VehiculoFormScreen extends StatefulWidget {
  const VehiculoFormScreen({super.key});

  @override
  State<VehiculoFormScreen> createState() => _VehiculoFormScreenState();
}

class _VehiculoFormScreenState extends State<VehiculoFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _placaCtrl = TextEditingController();
  final _marcaCtrl = TextEditingController();
  final _modeloCtrl = TextEditingController();
  final _colorCtrl = TextEditingController();
  bool _isInit = false;
  Vehiculo? _vehiculo;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_isInit) {
      _vehiculo = ModalRoute.of(context)?.settings.arguments as Vehiculo?;
      if (_vehiculo != null) {
        _placaCtrl.text = _vehiculo!.placa;
        _marcaCtrl.text = _vehiculo!.marca;
        _modeloCtrl.text = _vehiculo!.modelo;
        _colorCtrl.text = _vehiculo!.color;
      }
      _isInit = true;
    }
  }

  @override
  void dispose() {
    _placaCtrl.dispose();
    _marcaCtrl.dispose();
    _modeloCtrl.dispose();
    _colorCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    final provider = context.read<VehiculoProvider>();
    final v = Vehiculo(
      idVehiculo: _vehiculo?.idVehiculo,
      placa: _placaCtrl.text.trim().toUpperCase(),
      marca: _marcaCtrl.text.trim(),
      modelo: _modeloCtrl.text.trim(),
      color: _colorCtrl.text.trim(),
    );

    bool success;
    if (_vehiculo == null) {
      success = await provider.addVehiculo(v);
    } else {
      success = await provider.updateVehiculo(_vehiculo!.idVehiculo!, v);
    }

    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_vehiculo == null ? 'Vehículo registrado' : 'Vehículo actualizado'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      } else {
        final error = provider.error ?? 'Ocurrió un error al guardar';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<VehiculoProvider>();
    final isEdit = _vehiculo != null;

    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Editar Vehículo' : 'Nuevo Vehículo',
            style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isEdit ? 'Modifica los datos de tu vehículo' : 'Registra un nuevo vehículo para solicitar asistencia',
                  style: GoogleFonts.inter(fontSize: 14, color: Colors.white54),
                ),
                const SizedBox(height: 32),
                AppInput(
                  label: 'Placa (Ej: 1234ABC)',
                  hint: 'Ingresa la placa del vehículo',
                  controller: _placaCtrl,
                  prefixIcon: Icons.badge_outlined,
                  validator: (v) => v == null || v.isEmpty ? 'La placa es obligatoria' : null,
                ),
                const SizedBox(height: 16),
                AppInput(
                  label: 'Marca (Ej: Toyota)',
                  hint: 'Ingresa la marca del vehículo',
                  controller: _marcaCtrl,
                  prefixIcon: Icons.branding_watermark_outlined,
                  validator: (v) => v == null || v.isEmpty ? 'La marca es obligatoria' : null,
                ),
                const SizedBox(height: 16),
                AppInput(
                  label: 'Modelo (Ej: Corolla)',
                  hint: 'Ingresa el modelo del vehículo',
                  controller: _modeloCtrl,
                  prefixIcon: Icons.model_training_outlined,
                  validator: (v) => v == null || v.isEmpty ? 'El modelo es obligatorio' : null,
                ),
                const SizedBox(height: 16),
                AppInput(
                  label: 'Color (Ej: Blanco)',
                  hint: 'Ingresa el color del vehículo',
                  controller: _colorCtrl,
                  prefixIcon: Icons.color_lens_outlined,
                  validator: (v) => v == null || v.isEmpty ? 'El color es obligatorio' : null,
                ),
                const SizedBox(height: 48),
                AppButton(
                  text: isEdit ? 'Guardar Cambios' : 'Registrar Vehículo',
                  onPressed: _save,
                  isLoading: provider.isLoading,
                  icon: Icons.save_rounded,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
