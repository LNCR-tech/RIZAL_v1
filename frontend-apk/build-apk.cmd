@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "APP_DIR=%ROOT_DIR%..\frontend-web"
set "OUTPUT_DIR=%ROOT_DIR%outputs"
set "BUILD_MODE=%~1"

if "%BUILD_MODE%"=="" set "BUILD_MODE=debug"

if /I not "%BUILD_MODE%"=="debug" if /I not "%BUILD_MODE%"=="release" (
  echo [build-apk] Invalid mode "%BUILD_MODE%". Use "debug" or "release".
  exit /b 1
)

if not exist "%APP_DIR%\package.json" (
  echo [build-apk] Could not find frontend\package.json
  exit /b 1
)

pushd "%APP_DIR%" >nul
if errorlevel 1 (
  echo [build-apk] Failed to enter "%APP_DIR%"
  exit /b 1
)

set "NODE_OPTIONS=--max-old-space-size=4096"

if /I "%BUILD_MODE%"=="release" (
  echo [build-apk] Building release APK from frontend...
  call npm run android:build:release
  if errorlevel 1 goto :fail
  set "APK_SOURCE=%ROOT_DIR%android\app\build\outputs\apk\release\app-release.apk"
  set "APK_TARGET=%OUTPUT_DIR%\Aura-release.apk"
) else (
  echo [build-apk] Building debug APK from frontend...
  call npm run android:build:debug
  if errorlevel 1 goto :fail
  set "APK_SOURCE=%ROOT_DIR%android\app\build\outputs\apk\debug\app-debug.apk"
  set "APK_TARGET=%OUTPUT_DIR%\Aura-debug.apk"
)

popd >nul

if not exist "%APK_SOURCE%" (
  echo [build-apk] APK was not generated at "%APK_SOURCE%"
  exit /b 1
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
copy /Y "%APK_SOURCE%" "%APK_TARGET%" >nul
if errorlevel 1 (
  echo [build-apk] Failed to copy APK to "%APK_TARGET%"
  exit /b 1
)

echo [build-apk] APK ready at "%APK_TARGET%"
exit /b 0

:fail
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%
