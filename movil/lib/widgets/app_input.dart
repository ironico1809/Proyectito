import 'package:flutter/material.dart';

class AppInput extends StatelessWidget {
  final String label;
  final String? hint;
  final TextEditingController controller;
  final bool obscureText;
  final IconData? prefixIcon;
  final String? Function(String?)? validator;
  final int maxLines;
  final TextInputType? keyboardType;

  const AppInput({
    super.key,
    required this.label,
    this.hint,
    required this.controller,
    this.obscureText = false,
    this.prefixIcon,
    this.validator,
    this.maxLines = 1,
    this.keyboardType,
  });

  static const _slate800 = Color(0xFF1E293B);
  static const _slate600 = Color(0xFF475569);
  static const _amber = Color(0xFFF59E0B);

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      obscureText: obscureText,
      validator: validator,
      maxLines: maxLines,
      keyboardType: keyboardType,
      style: const TextStyle(color: Colors.white, fontSize: 15),
      cursorColor: _amber,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        labelStyle: TextStyle(color: _slate600, fontSize: 14),
        hintStyle: TextStyle(color: _slate600.withValues(alpha: 0.7), fontSize: 14),
        floatingLabelStyle: const TextStyle(color: _amber, fontSize: 14),
        filled: true,
        fillColor: _slate800,
        prefixIcon: prefixIcon != null
            ? Icon(prefixIcon, color: _slate600, size: 20)
            : null,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: _slate800, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _amber, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.red.shade400, width: 1.5),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.red.shade400, width: 1.5),
        ),
        errorStyle: TextStyle(color: Colors.red.shade400, fontSize: 12),
      ),
    );
  }
}
