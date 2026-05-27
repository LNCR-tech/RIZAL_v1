import 'package:flutter/material.dart';

import '../theme/app_tokens.dart';

/// Labeled text field that inherits the app's [InputDecorationTheme], with the
/// label above the field and error text below the cause.
class AuraTextField extends StatelessWidget {
  const AuraTextField({
    super.key,
    this.label,
    this.hint,
    this.controller,
    this.focusNode,
    this.obscure = false,
    this.keyboardType,
    this.textInputAction,
    this.onSubmitted,
    this.prefixIcon,
    this.suffix,
    this.errorText,
    this.autofillHints,
    this.enabled = true,
  });

  final String? label;
  final String? hint;
  final TextEditingController? controller;
  final FocusNode? focusNode;
  final bool obscure;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final ValueChanged<String>? onSubmitted;
  final IconData? prefixIcon;
  final Widget? suffix;
  final String? errorText;
  final Iterable<String>? autofillHints;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final t = AppTokens.of(context);
    final textTheme = Theme.of(context).textTheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 6, left: 4),
            child: Text(label!,
                style: textTheme.labelMedium?.copyWith(color: t.textSecondary)),
          ),
        TextField(
          controller: controller,
          focusNode: focusNode,
          obscureText: obscure,
          keyboardType: keyboardType,
          textInputAction: textInputAction,
          onSubmitted: onSubmitted,
          enabled: enabled,
          autofillHints: autofillHints,
          style: textTheme.bodyLarge,
          decoration: InputDecoration(
            hintText: hint,
            prefixIcon: prefixIcon != null ? Icon(prefixIcon, size: 20) : null,
            suffixIcon: suffix,
            errorText: errorText,
          ),
        ),
      ],
    );
  }
}
