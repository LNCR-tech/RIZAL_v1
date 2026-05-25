# Local Patches

This package is `liquid_glass_renderer` `0.2.0-dev.4` from pub.dev.

Local changes:
- Removed the `screenshots` pubspec metadata entry because this vendored copy
  does not include the upstream `doc/` assets.
- Updated the SDF shader helper so `uShapeData` is read as a global uniform
  instead of being passed through helper functions as a float array. This avoids
  SkSL compiler errors from generated array initializers while keeping the
  renderer API and app widget usage unchanged.
