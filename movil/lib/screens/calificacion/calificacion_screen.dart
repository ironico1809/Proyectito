import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../providers/emergencia_provider.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_input.dart';

class CalificacionScreen extends StatefulWidget {
  const CalificacionScreen({super.key});

  @override
  State<CalificacionScreen> createState() => _CalificacionScreenState();
}

class _CalificacionScreenState extends State<CalificacionScreen> {
  final _comentarioCtrl = TextEditingController();
  int _puntuacion = 5;

  @override
  void dispose() {
    _comentarioCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final incidenteId = ModalRoute.of(context)!.settings.arguments as int;
    final provider = context.read<EmergenciaProvider>();

    final success = await provider.calificarIncidente(
      incidenteId: incidenteId,
      puntuacion: _puntuacion,
      comentario: _comentarioCtrl.text.trim().isEmpty ? null : _comentarioCtrl.text.trim(),
    );

    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('¡Gracias por tu calificación!'), backgroundColor: Colors.green),
        );
        provider.clear();
        Navigator.popUntil(context, (route) => route.isFirst);
      } else {
        final error = provider.error ?? 'Error al registrar calificación';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<EmergenciaProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text('Calificar Servicio', style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 16),
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: const Color(0xFFF59E0B).withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.star_rounded, color: Color(0xFFF59E0B), size: 40),
              ),
              const SizedBox(height: 24),
              Text(
                '¿Cómo calificarías el servicio?',
                style: GoogleFonts.inter(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Tu opinión ayuda a mejorar la calidad de los talleres mecánicos afiliados.',
                style: GoogleFonts.inter(fontSize: 13, color: Colors.white54),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 36),

              // Stars selector
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(5, (index) {
                  final starVal = index + 1;
                  final isSelected = starVal <= _puntuacion;
                  return IconButton(
                    icon: Icon(
                      isSelected ? Icons.star_rounded : Icons.star_outline_rounded,
                      color: isSelected ? const Color(0xFFF59E0B) : Colors.white24,
                      size: 48,
                    ),
                    onPressed: () {
                      setState(() {
                        _puntuacion = starVal;
                      });
                    },
                  );
                }),
              ),
              const SizedBox(height: 12),
              Text(
                _puntuacionText(),
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: const Color(0xFFF59E0B),
                ),
              ),
              const SizedBox(height: 36),

              // Review Input
              AppInput(
                label: 'Comentarios adicionales (opcional)',
                hint: 'Cuéntanos qué te pareció el trabajo, puntualidad, limpieza, etc.',
                controller: _comentarioCtrl,
                maxLines: 4,
                prefixIcon: Icons.rate_review_outlined,
              ),
              const SizedBox(height: 48),

              AppButton(
                text: 'Enviar Calificación',
                onPressed: _submit,
                isLoading: provider.isLoading,
                icon: Icons.send_rounded,
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: () {
                  provider.clear();
                  Navigator.popUntil(context, (route) => route.isFirst);
                },
                child: Text(
                  'Omitir calificación',
                  style: GoogleFonts.inter(color: Colors.white38, fontSize: 13),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _puntuacionText() {
    switch (_puntuacion) {
      case 1:
        return 'Pésimo';
      case 2:
        return 'Malo';
      case 3:
        return 'Aceptable';
      case 4:
        return 'Muy Bueno';
      case 5:
        return 'Excelente';
      default:
        return '';
    }
  }
}
