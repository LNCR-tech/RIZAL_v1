import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Per-school "Aura AI access" decision.
///
/// NOTE: the cloud backend has no `ai_enabled` field yet, so this is persisted
/// **on this device** as a stop-gap admin control. Real cross-device / per-user
/// enforcement needs a backend field on the school + a check in the assistant
/// service. Wire [setEnabled] to that endpoint when it exists.
class AiAccessStore {
  static String _key(int schoolId) => 'aura_ai_enabled_$schoolId';

  Future<bool> isEnabled(int schoolId) async {
    final p = await SharedPreferences.getInstance();
    return p.getBool(_key(schoolId)) ?? true;
  }

  Future<void> setEnabled(int schoolId, bool value) async {
    final p = await SharedPreferences.getInstance();
    await p.setBool(_key(schoolId), value);
  }
}

final aiAccessStoreProvider = Provider<AiAccessStore>((ref) => AiAccessStore());

final aiAccessProvider =
    FutureProvider.autoDispose.family<bool, int>((ref, schoolId) {
  return ref.watch(aiAccessStoreProvider).isEnabled(schoolId);
});
