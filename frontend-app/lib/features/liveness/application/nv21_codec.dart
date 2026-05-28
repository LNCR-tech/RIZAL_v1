import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:image/image.dart' as img;

import '../domain/liveness_models.dart';

/// Build a packed NV21 buffer from a [CameraImage] received in image-stream
/// mode. Most Android devices deliver NV21 natively when the controller is
/// created with `imageFormatGroup: ImageFormatGroup.nv21`, in which case we
/// concatenate the two planes (`Y` then interleaved `VU`). When the camera
/// fell back to two-plane semi-planar that's bitwise NV21, this still works.
///
/// Returns `null` when the frame doesn't look like NV21 (e.g. the device
/// silently fell back to YUV_420_888 with three separate U/V planes) — the
/// caller treats this as "pipeline unavailable for this frame" and skips
/// the on-device check rather than feeding the plugin garbage.
Nv21Frame? buildNv21FrameFromCamera(
  CameraImage image, {
  required int sensorOrientationDegrees,
}) {
  if (image.planes.length != 2) {
    // Three-plane YUV_420_888 needs a different packer; we don't support it
    // here. The caller's `usable=false` path will kick in.
    return null;
  }

  final y = image.planes[0].bytes;
  final vu = image.planes[1].bytes;
  final expected = image.width * image.height * 3 ~/ 2;
  if (y.length + vu.length != expected) {
    // Plane bytes don't match the NV21 packing formula — bail.
    return null;
  }

  final buf = Uint8List(y.length + vu.length);
  buf.setRange(0, y.length, y);
  buf.setRange(y.length, y.length + vu.length, vu);

  return Nv21Frame(
    bytes: buf,
    width: image.width,
    height: image.height,
    orientationDegrees: _normalizeRotation(sensorOrientationDegrees),
  );
}

int _normalizeRotation(int degrees) {
  final r = degrees % 360;
  return r < 0 ? r + 360 : r;
}

/// JPEG-encode an NV21 frame for backend submission. Runs inside `compute()`
/// so the camera thread never stalls on the conversion. Quality 85 is a good
/// balance for face-matching (the backend auto-downscales to 1280px anyway).
///
/// The `rotation` argument is the same `orientationDegrees` value we send to
/// the liveness plugin — the encoded JPEG comes out upright so the backend's
/// `PIL.Image.open()` doesn't need to read EXIF.
Future<Uint8List> encodeNv21ToJpeg(Nv21Frame frame, {int quality = 85}) {
  return compute(_encodeNv21ToJpegInternal, _EncodeArgs(
    bytes: frame.bytes,
    width: frame.width,
    height: frame.height,
    rotation: frame.orientationDegrees,
    quality: quality,
  ));
}

class _EncodeArgs {
  const _EncodeArgs({
    required this.bytes,
    required this.width,
    required this.height,
    required this.rotation,
    required this.quality,
  });
  final Uint8List bytes;
  final int width;
  final int height;
  final int rotation;
  final int quality;
}

Uint8List _encodeNv21ToJpegInternal(_EncodeArgs args) {
  final image = _nv21ToImage(args.bytes, args.width, args.height);

  // Rotate to upright so backend sees the right way up. `image.copyRotate`
  // accepts an angle in degrees; positive = clockwise.
  final upright = args.rotation == 0
      ? image
      : img.copyRotate(image, angle: args.rotation);

  return Uint8List.fromList(img.encodeJpg(upright, quality: args.quality));
}

img.Image _nv21ToImage(Uint8List nv21, int width, int height) {
  final out = img.Image(width: width, height: height);
  final uvStart = width * height;

  // NV21 layout: width*height Y bytes, then interleaved V,U,V,U,... at half
  // resolution in both axes. Each (u, v) sample covers a 2×2 luma block.
  for (var j = 0; j < height; j++) {
    final yRow = j * width;
    final uvRow = (j >> 1) * width;
    for (var i = 0; i < width; i++) {
      final yVal = nv21[yRow + i] & 0xFF;
      final uvCol = (i >> 1) << 1;
      final vIdx = uvStart + uvRow + uvCol;
      final uIdx = vIdx + 1;
      final vVal = (nv21[vIdx] & 0xFF) - 128;
      final uVal = (nv21[uIdx] & 0xFF) - 128;

      // BT.601 full-range YUV → RGB. Integer math (12-bit shifts) is ~3×
      // faster than floating point and visually indistinguishable here.
      final r = yVal + ((1436 * vVal) >> 10);
      final g = yVal - ((352 * uVal + 731 * vVal) >> 10);
      final b = yVal + ((1814 * uVal) >> 10);

      out.setPixelRgb(
        i,
        j,
        r < 0 ? 0 : (r > 255 ? 255 : r),
        g < 0 ? 0 : (g > 255 ? 255 : g),
        b < 0 ? 0 : (b > 255 ? 255 : b),
      );
    }
  }
  return out;
}
