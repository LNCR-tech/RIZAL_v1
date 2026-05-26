import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Secure storage for the JWT access token (Keychain / EncryptedSharedPrefs).
class TokenStore {
  TokenStore([FlutterSecureStorage? storage])
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  final FlutterSecureStorage _storage;
  static const _kToken = 'aura_access_token';

  Future<String?> read() => _storage.read(key: _kToken);
  Future<void> write(String token) => _storage.write(key: _kToken, value: token);
  Future<void> clear() => _storage.delete(key: _kToken);
}

final tokenStoreProvider = Provider<TokenStore>((ref) => TokenStore());
