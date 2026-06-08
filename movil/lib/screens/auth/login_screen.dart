import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_input.dart';
import '../../providers/auth_provider.dart';
import 'package:provider/provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController(text: 'juan@gmail.com');
  final _passCtrl = TextEditingController(text: '123456');
  late AnimationController _animCtrl;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 800));
    _fadeAnim = CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut);
    _animCtrl.forward();
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    final auth = context.read<AuthProvider>();
    await auth.login(_emailCtrl.text.trim(), _passCtrl.text);
    if (auth.error != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(auth.error!), backgroundColor: Colors.redAccent),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnim,
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 80, height: 80,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFFF59E0B), Color(0xFFD97706)],
                          begin: Alignment.topLeft, end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(color: const Color(0xFFF59E0B).withOpacity(0.3), blurRadius: 20, spreadRadius: 2),
                        ],
                      ),
                      child: const Icon(Icons.build_rounded, color: Color(0xFF0F172A), size: 40),
                    ),
                    const SizedBox(height: 24),
                    Text('TallerPro', style: GoogleFonts.inter(fontSize: 28, fontWeight: FontWeight.w800, color: Colors.white)),
                    const SizedBox(height: 8),
                    Text('Emergencias Vehiculares', style: GoogleFonts.inter(fontSize: 14, color: Colors.white54)),
                    const SizedBox(height: 48),
                    AppInput(
                      label: 'Correo electrónico',
                      hint: 'tu@email.com',
                      controller: _emailCtrl,
                      prefixIcon: Icons.email_outlined,
                      keyboardType: TextInputType.emailAddress,
                      validator: (v) => v == null || v.isEmpty ? 'Ingresa tu correo' : null,
                    ),
                    const SizedBox(height: 16),
                    AppInput(
                      label: 'Contraseña',
                      controller: _passCtrl,
                      prefixIcon: Icons.lock_outline,
                      obscureText: true,
                      validator: (v) => v == null || v.isEmpty ? 'Ingresa tu contraseña' : null,
                    ),
                    const SizedBox(height: 32),
                    AppButton(
                      text: 'Iniciar Sesión',
                      onPressed: _login,
                      isLoading: auth.isLoading,
                      icon: Icons.login_rounded,
                    ),
                    const SizedBox(height: 16),
                    AppButton(
                      text: 'Crear Cuenta',
                      onPressed: () => Navigator.pushNamed(context, '/register'),
                      isOutlined: true,
                      icon: Icons.person_add_outlined,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
