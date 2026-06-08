import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static const Color _slate950 = Color(0xFF0F172A);
  static const Color _slate900 = Color(0xFF0F1629);
  static const Color _slate800 = Color(0xFF1E293B);
  static const Color _slate700 = Color(0xFF334155);
  static const Color _slate600 = Color(0xFF475569);
  static const Color _slate400 = Color(0xFF94A3B8);
  static const Color _slate300 = Color(0xFFCBD5E1);
  static const Color _amber = Color(0xFFF59E0B);
  static const Color _amberLight = Color(0xFFFBBF24);
  static const Color _amberDark = Color(0xFFD97706);
  static const Color _white = Color(0xFFFFFFFF);
  static const Color _errorRed = Color(0xFFEF4444);
  static const Color _successGreen = Color(0xFF22C55E);

  static ThemeData get darkTheme {
    final baseTextTheme = GoogleFonts.interTextTheme(ThemeData.dark().textTheme);

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: _slate950,
      primaryColor: _amber,
      colorScheme: const ColorScheme.dark(
        primary: _amber,
        onPrimary: _slate950,
        secondary: _amberLight,
        onSecondary: _slate950,
        tertiary: _amberDark,
        surface: _slate950,
        onSurface: _slate300,
        surfaceContainerHighest: _slate800,
        error: _errorRed,
        onError: _white,
        outline: _slate700,
      ),
      textTheme: baseTextTheme.copyWith(
        displayLarge: baseTextTheme.displayLarge?.copyWith(color: _white, fontWeight: FontWeight.w700),
        displayMedium: baseTextTheme.displayMedium?.copyWith(color: _white, fontWeight: FontWeight.w700),
        displaySmall: baseTextTheme.displaySmall?.copyWith(color: _white, fontWeight: FontWeight.w600),
        headlineLarge: baseTextTheme.headlineLarge?.copyWith(color: _white, fontWeight: FontWeight.w700),
        headlineMedium: baseTextTheme.headlineMedium?.copyWith(color: _white, fontWeight: FontWeight.w600),
        headlineSmall: baseTextTheme.headlineSmall?.copyWith(color: _white, fontWeight: FontWeight.w600),
        titleLarge: baseTextTheme.titleLarge?.copyWith(color: _white, fontWeight: FontWeight.w600),
        titleMedium: baseTextTheme.titleMedium?.copyWith(color: _slate300, fontWeight: FontWeight.w500),
        titleSmall: baseTextTheme.titleSmall?.copyWith(color: _slate400, fontWeight: FontWeight.w500),
        bodyLarge: baseTextTheme.bodyLarge?.copyWith(color: _slate300),
        bodyMedium: baseTextTheme.bodyMedium?.copyWith(color: _slate400),
        bodySmall: baseTextTheme.bodySmall?.copyWith(color: _slate600),
        labelLarge: baseTextTheme.labelLarge?.copyWith(color: _amber, fontWeight: FontWeight.w600),
        labelMedium: baseTextTheme.labelMedium?.copyWith(color: _slate400),
        labelSmall: baseTextTheme.labelSmall?.copyWith(color: _slate600),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        systemOverlayStyle: SystemUiOverlayStyle.light,
        titleTextStyle: GoogleFonts.inter(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: _white,
          letterSpacing: -0.3,
        ),
        iconTheme: const IconThemeData(color: _amber, size: 24),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: _amber,
          foregroundColor: _slate950,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: GoogleFonts.inter(
            fontSize: 15,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.3,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: _amber,
          side: const BorderSide(color: _amber, width: 1.5),
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: GoogleFonts.inter(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.3,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: _amber,
          textStyle: GoogleFonts.inter(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: _slate800,
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        hintStyle: GoogleFonts.inter(color: _slate600, fontSize: 14),
        labelStyle: GoogleFonts.inter(color: _slate400, fontSize: 14),
        prefixIconColor: _slate600,
        suffixIconColor: _slate600,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _slate700, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _amber, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _errorRed, width: 1),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _errorRed, width: 1.5),
        ),
        floatingLabelStyle: GoogleFonts.inter(color: _amber, fontWeight: FontWeight.w500),
      ),
      cardTheme: CardThemeData(
        color: _slate800,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        margin: const EdgeInsets.symmetric(horizontal: 0, vertical: 6),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: _slate800,
        selectedColor: _amber.withOpacity(0.2),
        labelStyle: GoogleFonts.inter(color: _slate300, fontSize: 12, fontWeight: FontWeight.w500),
        side: const BorderSide(color: _slate700, width: 1),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: _slate900,
        selectedItemColor: _amber,
        unselectedItemColor: _slate600,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w600),
        unselectedLabelStyle: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w500),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: _slate900,
        indicatorColor: _amber.withOpacity(0.15),
        elevation: 0,
        height: 70,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w700, color: _amber);
          }
          return GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w500, color: _slate600);
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: _amber, size: 24);
          }
          return const IconThemeData(color: _slate600, size: 24);
        }),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: _amber,
        foregroundColor: _slate950,
        elevation: 4,
        shape: CircleBorder(),
      ),
      dividerTheme: const DividerThemeData(
        color: _slate700,
        thickness: 0.5,
        space: 0,
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: _slate800,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        titleTextStyle: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: _white),
        contentTextStyle: GoogleFonts.inter(fontSize: 14, color: _slate300),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: _slate800,
        contentTextStyle: GoogleFonts.inter(color: _slate300, fontSize: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: _slate800,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: _amber,
        linearTrackColor: _slate700,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return _amber;
          return _slate600;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return _amber.withOpacity(0.3);
          return _slate700;
        }),
      ),
    );
  }

  static const Color amber = _amber;
  static const Color amberLight = _amberLight;
  static const Color amberDark = _amberDark;
  static const Color slate950 = _slate950;
  static const Color slate800 = _slate800;
  static const Color slate700 = _slate700;
  static const Color slate600 = _slate600;
  static const Color slate400 = _slate400;
  static const Color slate300 = _slate300;
  static const Color successGreen = _successGreen;
  static const Color errorRed = _errorRed;
}
