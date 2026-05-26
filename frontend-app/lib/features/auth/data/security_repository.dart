import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../../../shared/models/security.dart';
import '../../../shared/utils/json.dart';

/// Self-service security endpoints (mounted at the root, no `/api` prefix).
class SecurityRepository {
  SecurityRepository(this._client);
  final DioClient _client;

  Future<List<UserSession>> sessions() async {
    final r = await _client.get('/auth/security/sessions');
    return asMapList(r.data).map(UserSession.fromJson).toList();
  }

  Future<int> revokeOthers() async {
    final r = await _client.post('/auth/security/sessions/revoke-others');
    final d = r.data;
    return (d is Map ? asInt(d['revoked_count']) : null) ?? 0;
  }

  Future<void> revokeSession(String id) =>
      _client.post('/auth/security/sessions/$id/revoke');

  Future<List<LoginHistoryItem>> loginHistory({int limit = 50}) async {
    final r = await _client
        .get('/auth/security/login-history', query: {'limit': limit});
    return asMapList(r.data).map(LoginHistoryItem.fromJson).toList();
  }

  /// Set/replace the signed-in privileged user's face reference
  /// (admin / campus-admin). Students use `AttendanceRepository.registerFace`.
  Future<void> setFaceReference(String imageBase64) => _client
      .post('/auth/security/face-reference', data: {'image_base64': imageBase64});
}

final securityRepositoryProvider =
    Provider<SecurityRepository>((ref) => SecurityRepository(ref.watch(dioClientProvider)));

final sessionsProvider = FutureProvider.autoDispose<List<UserSession>>((ref) {
  return ref.watch(securityRepositoryProvider).sessions();
});

final loginHistoryProvider =
    FutureProvider.autoDispose<List<LoginHistoryItem>>((ref) {
  return ref.watch(securityRepositoryProvider).loginHistory();
});
