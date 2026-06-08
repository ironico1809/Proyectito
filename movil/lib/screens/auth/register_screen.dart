import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_input.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;
    final auth = context.read<AuthProvider>();
    await auth.register(_nameCtrl.text.trim(), _emailCtrl.text.trim(), _passCtrl.text, _phoneCtrl.text.trim());
    if (auth.error != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(auth.error!), backgroundColor: Colors.redAccent),
      );
    } else if (mounted) {
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white70),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Form(
              key: _formKey,
              child: Column(
                children: [
                  Text('Crear Cuenta', style: GoogleFonts.inter(fontSize: 26, fontWeight: FontWeight.w800, color: Colors.white)),
                  const SizedBox(height: 8),
                  Text('Regístrate para solicitar auxilio vehicular', style: GoogleFonts.inter(fontSize: 13, color: Colors.white54)),
                  const SizedBox(height: 40),
                  AppInput(
                    label: 'Nombre completo',
                    controller: _nameCtrl,
                    prefixIcon: Icons.person_outline,
                    validator: (v) => v == null || v.isEmpty ? 'Ingresa tu nombre' : null,
                  ),
                  const SizedBox(height: 16),
                  AppInput(
                    label: 'Correo electrónico',
                    controller: _emailCtrl,
                    prefixIcon: Icons.email_outlined,
                    keyboardType: TextInputType.emailAddress,
                    validator: (v) => v == null || !v.contains('@') ? 'Correo inválido' : null,
                  ),
                  const SizedBox(height: 16),
                  AppInput(
                    label: 'Teléfono',
                    controller: _phoneCtrl,
                    prefixIcon: Icons.phone_outlined,
                    keyboardType: TextInputType.phone,
                  ),
                  const SizedBox(height: 16),
                  AppInput(
                    label: 'Contraseña',
                    controller: _passCtrl,
                    prefixIcon: Icons.lock_outline,
                    obscureText: true,
                    validator: (v) => v == null || v.length < 6 ? 'Mínimo 6 caracteres' : null,
                  ),
                  const SizedBox(height: 32),
                  AppButton(
                    text: 'Registrarme',
                    onPressed: _register,
                    isLoading: auth.isLoading,
                    icon: Icons.person_add_rounded,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
