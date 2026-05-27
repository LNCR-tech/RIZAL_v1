import java.util.Properties
import java.io.FileInputStream

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// Release signing — credentials live in android/key.properties (git-ignored).
// If the file is missing we still build, but the release signingConfig is left
// unset so `flutter build apk --release` will fail loudly rather than silently
// fall back to the debug keystore. To set up: `keytool -genkeypair ...` then
// write storeFile, storePassword, keyPassword, keyAlias to key.properties.
val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

android {
    namespace = "com.aura.aura_app"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        // Required by flutter_local_notifications (uses java.time on older Android).
        isCoreLibraryDesugaringEnabled = true
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.aura.aura_app"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            val storeFileName = keystoreProperties["storeFile"] as String?
            if (storeFileName != null) {
                // Resolve relative to the `android/` directory (rootProject)
                // so `storeFile=aura-release.jks` in key.properties picks up
                // android/aura-release.jks.
                storeFile = rootProject.file(storeFileName)
                storePassword = keystoreProperties["storePassword"] as String?
                keyAlias = keystoreProperties["keyAlias"] as String?
                keyPassword = keystoreProperties["keyPassword"] as String?
            }
        }
    }

    buildTypes {
        release {
            // Release builds use the keystore configured via key.properties.
            // If key.properties is missing, this still resolves to a defined
            // signingConfig with all fields null, and Gradle will fail with a
            // clear "No signing config specified" error rather than silently
            // falling back to debug keys.
            signingConfig = signingConfigs.getByName("release")
            // Dart code is AOT-compiled + obfuscated via Flutter's
            // --obfuscate flag, not via R8. Java/Kotlin minification on
            // release would also need ProGuard rules for every plugin
            // that uses reflection (camera, geolocator, share_plus,
            // flutter_local_notifications, …) — left off until those
            // rules are written and verified on a device. APK size is
            // managed via the per-ABI split build below.
        }
    }
}

flutter {
    source = "../.."
}

dependencies {
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
}
