import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_paths.dart';
import '../../../core/network/dio_client.dart';
import '../../../shared/models/profile.dart';

class ProfileRepository {
  ProfileRepository(this._client);
  final DioClient _client;

  Future<UserProfile> me() async {
    final res = await _client.get(Api.me);
    return UserProfile.fromJson((res.data as Map).cast<String, dynamic>());
  }

  Future<UserProfile> updateStudentProfile(
      int profileId, Map<String, dynamic> patch) async {
    final res =
        await _client.patch(Api.studentProfile(profileId), data: patch);
    return UserProfile.fromJson((res.data as Map).cast<String, dynamic>());
  }

  /// Update the signed-in user's own account (name / email).
  Future<UserProfile> updateUser(int userId, Map<String, dynamic> patch) async {
    final res = await _client.patch(Api.user(userId), data: patch);
    return UserProfile.fromJson((res.data as Map).cast<String, dynamic>());
  }
}

final profileRepositoryProvider = Provider<ProfileRepository>(
  (ref) => ProfileRepository(ref.watch(dioClientProvider)),
);
