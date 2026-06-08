import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_input.dart';
import '../../widgets/bottom_nav.dart';

class PerfilScreen extends StatefulWidget {
  const PerfilScreen({super.key});

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nombreCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _telefonoCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _isInit = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_isInit) {
      final user = context.read<AuthProvider>().currentUser;
      if (user != null) {
        _nombreCtrl.text = user.nombre;
        _emailCtrl.text = user.email;
        _telefonoCtrl.text = user.telefono ?? '';
      }
      _isInit = true;
    }
  }

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _emailCtrl.dispose();
    _telefonoCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _updateProfile() async {
    if (!_formKey.currentState!.validate()) return;

    final auth = context.read<AuthProvider>();
    final success = await auth.updateProfile(
      _nombreCtrl.text.trim(),
      _telefonoCtrl.text.trim().isEmpty ? null : _telefonoCtrl.text.trim(),
      _emailCtrl.text.trim(),
      _passwordCtrl.text.isEmpty ? null : _passwordCtrl.text,
    );

    if (mounted) {
      if (success) {
        _passwordCtrl.clear();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Perfil actualizado con éxito'), backgroundColor: Colors.green),
        );
      } else {
        final error = auth.error ?? 'Error al actualizar perfil';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: Text('Cerrar Sesión', style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Text('¿Está seguro de que desea cerrar sesión?', style: GoogleFonts.inter(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('Cancelar', style: GoogleFonts.inter(color: Colors.white54)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text('Salir', style: GoogleFonts.inter(color: Colors.redAccent, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      await context.read<AuthProvider>().logout();
      if (mounted) {
        Navigator.popUntil(context, (route) => route.isFirst);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: Text('Mi Perfil', style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: user == null
            ? const Center(child: CircularProgressIndicator(color: Color(0xFFF59E0B)))
            : SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Form(
                  key: _formKey,
                  child: Column(
                    children: [
                      // Avatar Card
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E293B),
                          borderRadius: BorderRadius.circular(20),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.15),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Column(
                          children: [
                            Container(
                              width: 80,
                              height: 80,
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [Color(0xFFF59E0B), Color(0xFFD97706)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                shape: BoxShape.circle,
                              ),
                              child: Center(
                                child: Text(
                                  user.nombre.isNotEmpty ? user.nombre[0].toUpperCase() : 'U',
                                  style: GoogleFonts.inter(fontSize: 32, fontWeight: FontWeight.w800, color: const Color(0xFF0F172A)),
                                ),
                              ),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              user.nombre,
                              style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              user.email,
                              style: GoogleFonts.inter(fontSize: 14, color: Colors.white54),
                            ),
                            const SizedBox(height: 12),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF59E0B).withOpacity(0.1),
                                borderRadius: BorderRadius.circular(100),
                              ),
                              child: Text(
                                user.rol.toUpperCase(),
                                style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w800, color: const Color(0xFFF59E0B), letterSpacing: 0.5),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 32),

                      // Edit Fields
                      AppInput(
                        label: 'Nombre completo',
                        hint: 'Ingresa tu nombre',
                        controller: _nombreCtrl,
                        prefixIcon: Icons.person_outline_rounded,
                        validator: (v) => v == null || v.isEmpty ? 'El nombre es obligatorio' : null,
                      ),
                      const SizedBox(height: 16),
                      AppInput(
                        label: 'Correo electrónico',
                        hint: 'Ingresa tu correo',
                        controller: _emailCtrl,
                        prefixIcon: Icons.email_outlined,
                        keyboardType: TextInputType.emailAddress,
                        validator: (v) => v == null || v.isEmpty ? 'El correo es obligatorio' : null,
                      ),
                      const SizedBox(height: 16),
                      AppInput(
                        label: 'Teléfono',
                        hint: 'Ingresa tu número de teléfono',
                        controller: _telefonoCtrl,
                        prefixIcon: Icons.phone_android_outlined,
                        keyboardType: TextInputType.phone,
                      ),
                      const SizedBox(height: 16),
                      AppInput(
                        label: 'Nueva Contraseña (opcional)',
                        hint: 'Dejar vacío si no deseas cambiarla',
                        controller: _passwordCtrl,
                        prefixIcon: Icons.lock_outline,
                        obscureText: true,
                      ),
                      const SizedBox(height: 36),

                      AppButton(
                        text: 'Ver Mi Historial',
                        onPressed: () => Navigator.pushNamed(context, '/historial'),
                        isOutlined: true,
                        icon: Icons.history_rounded,
                      ),
                      const SizedBox(height: 16),

                      AppButton(
                        text: 'Actualizar Perfil',
                        onPressed: _updateProfile,
                        isLoading: auth.isLoading,
                        icon: Icons.check_circle_outline_rounded,
                      ),
                      const SizedBox(height: 16),
                      AppButton(
                        text: 'Cerrar Sesión',
                        onPressed: _logout,
                        isOutlined: true,
                        icon: Icons.logout_rounded,
                      ),
                    ],
                  ),
                ),
              ),
      ),
    );
  }
}
