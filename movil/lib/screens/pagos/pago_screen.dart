import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import '../../providers/emergencia_provider.dart';
import '../../models/incidente.dart';
import '../../widgets/app_button.dart';

class PagoScreen extends StatefulWidget {
  const PagoScreen({super.key});

  @override
  State<PagoScreen> createState() => _PagoScreenState();
}

class _PagoScreenState extends State<PagoScreen> {
  String _metodo = 'qr';
  bool _sending = false;

  final _metodos = [
    {'key': 'qr', 'label': 'Código QR', 'icon': Icons.qr_code_2_rounded},
    {'key': 'transferencia', 'label': 'Transferencia', 'icon': Icons.account_balance_rounded},
    {'key': 'tarjeta', 'label': 'Tarjeta', 'icon': Icons.credit_card_rounded},
    {'key': 'paypal', 'label': 'PayPal', 'icon': Icons.paypal_rounded},
  ];

  Future<void> _pagar(Incidente inc) async {
    final provider = context.read<EmergenciaProvider>();
    final double monto = inc.costoFinalDecimal ?? 100.0;

    if (_metodo == 'tarjeta') {
      setState(() => _sending = true);
      // 1. Obtener client_secret de Stripe desde el backend
      final clientSecret = await provider.crearStripeIntent(inc.idIncidente!);
      if (clientSecret == null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(provider.error ?? 'Error al iniciar Stripe'), backgroundColor: Colors.redAccent),
          );
        }
        setState(() => _sending = false);
        return;
      }

      // 2. Inicializar Payment Sheet de Stripe
      try {
        await Stripe.instance.initPaymentSheet(
          paymentSheetParameters: SetupPaymentSheetParameters(
            paymentIntentClientSecret: clientSecret,
            merchantDisplayName: 'TallerPro',
            style: ThemeMode.dark,
            appearance: const PaymentSheetAppearance(
              colors: PaymentSheetAppearanceColors(
                background: Color(0xFF0F172A),
                primary: Color(0xFFF59E0B),
                componentBackground: Color(0xFF1E293B),
              )
            )
          ),
        );

        // 3. Desplegar el Payment Sheet
        await Stripe.instance.presentPaymentSheet();

        // 4. Si se confirma el pago, registrar en la base de datos
        final success = await provider.registrarPago(
          incidenteId: inc.idIncidente!,
          duenoTallerId: inc.tallerActualId ?? 0,
          montoTotal: monto,
          metodo: 'tarjeta',
        );

        if (mounted) {
          if (success) {
            Navigator.pushReplacementNamed(context, '/calificacion', arguments: inc.idIncidente);
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(provider.error ?? 'Error al registrar el pago'), backgroundColor: Colors.redAccent),
            );
          }
        }
      } catch (e) {
        if (mounted) {
          if (e is StripeException) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Pago cancelado: ${e.error.localizedMessage}'), backgroundColor: Colors.orangeAccent),
            );
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Error Stripe: $e'), backgroundColor: Colors.redAccent),
            );
          }
        }
      } finally {
        if (mounted) {
          setState(() => _sending = false);
        }
      }
    } else if (_metodo == 'qr') {
      _mostrarDialogoQR(inc, monto);
    } else {
      setState(() => _sending = true);
      final success = await provider.registrarPago(
        incidenteId: inc.idIncidente!,
        duenoTallerId: inc.tallerActualId ?? 0,
        montoTotal: monto,
        metodo: _metodo,
      );

      if (mounted) {
        if (success) {
          Navigator.pushReplacementNamed(context, '/calificacion', arguments: inc.idIncidente);
        } else {
          final error = provider.error ?? 'Error al procesar el pago';
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(error), backgroundColor: Colors.redAccent),
          );
        }
      }
      setState(() => _sending = false);
    }
  }

  void _mostrarDialogoQR(Incidente inc, double monto) {
    final String qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=250x250&color=0f172a&data=TallerPro%20Incidente%20%23${inc.idIncidente}%20Monto%20Bs.%20${monto.toStringAsFixed(2)}';
    
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            const Icon(Icons.qr_code_2_rounded, color: Color(0xFFF59E0B), size: 26),
            const SizedBox(width: 8),
            Text('Código QR Dinámico', style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Escanea el QR para transferir Bs. ${monto.toStringAsFixed(2)} directamente al taller.',
              style: GoogleFonts.inter(color: Colors.white70, fontSize: 13),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
              child: Image.network(
                qrUrl,
                width: 200,
                height: 200,
                loadingBuilder: (context, child, loadingProgress) {
                  if (loadingProgress == null) return child;
                  return const SizedBox(
                    width: 200,
                    height: 200,
                    child: Center(child: CircularProgressIndicator(color: Color(0xFFF59E0B))),
                  );
                },
              ),
            ),
            const SizedBox(height: 12),
            Text('Taller: ${inc.tallerNombre ?? "Asignado"}', style: GoogleFonts.inter(color: Colors.white54, fontSize: 12)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              setState(() => _sending = true);
              final provider = context.read<EmergenciaProvider>();
              final success = await provider.registrarPago(
                incidenteId: inc.idIncidente!,
                duenoTallerId: inc.tallerActualId ?? 0,
                montoTotal: monto,
                metodo: 'qr',
              );
              if (mounted) {
                if (success) {
                  Navigator.pushReplacementNamed(context, '/calificacion', arguments: inc.idIncidente);
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(provider.error ?? 'Error al registrar el pago'), backgroundColor: Colors.redAccent),
                  );
                }
              }
              setState(() => _sending = false);
            },
            child: const Text('YA ESCANEÉ Y PAGUÉ'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final inc = ModalRoute.of(context)?.settings.arguments as Incidente?;
    final monto = inc?.costoFinalDecimal ?? 100.0;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white70), onPressed: () => Navigator.pop(context)),
        title: Text('Realizar Pago', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF1E293B), Color(0xFF334155)]),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  Text('Total a Pagar', style: GoogleFonts.inter(color: Colors.white54, fontSize: 14)),
                  const SizedBox(height: 8),
                  Text('Bs. ${monto.toStringAsFixed(2)}',
                    style: GoogleFonts.inter(fontSize: 36, fontWeight: FontWeight.w800, color: const Color(0xFFF59E0B))),
                  const SizedBox(height: 4),
                  Text('Incidente #${inc?.idIncidente ?? '-'}', style: GoogleFonts.inter(color: Colors.white38, fontSize: 13)),
                ],
              ),
            ),
            const SizedBox(height: 28),

            Text('Método de Pago', style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white)),
            const SizedBox(height: 14),

            ...(_metodos.map((m) => GestureDetector(
              onTap: () => setState(() => _metodo = m['key'] as String),
              child: Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: _metodo == m['key'] ? const Color(0xFFF59E0B) : Colors.transparent,
                    width: 2,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(m['icon'] as IconData, color: _metodo == m['key'] ? const Color(0xFFF59E0B) : Colors.white54, size: 28),
                    const SizedBox(width: 16),
                    Text(m['label'] as String, style: GoogleFonts.inter(
                      color: _metodo == m['key'] ? Colors.white : Colors.white70,
                      fontWeight: _metodo == m['key'] ? FontWeight.w600 : FontWeight.w400,
                      fontSize: 15,
                    )),
                    const Spacer(),
                    if (_metodo == m['key'])
                      const Icon(Icons.check_circle_rounded, color: Color(0xFFF59E0B), size: 22),
                  ],
                ),
              ),
            ))),
            const SizedBox(height: 28),

            AppButton(
              text: 'CONFIRMAR PAGO',
              onPressed: inc != null ? () => _pagar(inc) : null,
              isLoading: _sending,
              icon: Icons.payment_rounded,
            ),
          ],
        ),
      ),
    );
  }
}
