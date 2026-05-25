# Local Patches

This package is `liquid_glass_renderer` `0.2.0-dev.4` from pub.dev.

Local changes:
- Removed the `screenshots` pubspec metadata entry because this vendored copy
  does not include the upstream `doc/` assets.
- Updated the SDF shader helper so `uShapeData` is read as a global uniform
  instead of being passed through helper functions as a float array. This avoids
  SkSL compiler errors from generated array initializers while keeping the
  renderer API and app widget usage unchanged.
- Unrolled the SDF shape merge loop to avoid SkSL `min(int,int)` and dynamic
  loop issues.
- Replaced derivative intrinsics (`dFdx`/`dFdy`) with finite-difference normal
  sampling for runtime-effect compatibility.
- Removed loops from the experimental arbitrary shader's center sampler and
  gradient helper so the file compiles under SkSL.
- Removed `sampler2D` parameters from shared shader helper functions. Entry
  shaders now expose their background texture through a local sampling macro, so
  SkSL does not need to compile unsupported shader/sampler function parameters
  while each shader still samples the same texture it used before.
