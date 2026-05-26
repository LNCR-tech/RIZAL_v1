// Shape array uniforms - 6 floats per shape (type, centerX, centerY, sizeW, sizeH, cornerRadius)
// Reduced from 64 to 16 shapes to fit Impeller's uniform buffer limit (16 * 6 = 96 floats vs 384)
#define MAX_SHAPES 16

layout(location = SHAPE_DATA_LOCATION) uniform float uShapeData[MAX_SHAPES * 6];

float sdfRRect( in vec2 p, in vec2 b, in float r ) {
    float shortest = min(b.x, b.y);
    r = min(r, shortest);
    vec2 q = abs(p)-b+r;
    return min(max(q.x,q.y),0.0) + length(max(q,0.0)) - r;
}

float sdfRect(vec2 p, vec2 b) {
    vec2 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

float sdfSquircle(vec2 p, vec2 b, float r) {
    float shortest = min(b.x, b.y);
    r = min(r, shortest);

    vec2 q = abs(p) - b + r;

    vec2 maxQ = max(q, 0.0);
    return min(max(q.x, q.y), 0.0) + sqrt(maxQ.x * maxQ.x + maxQ.y * maxQ.y) - r;
}

float sdfEllipse(vec2 p, vec2 r) {
    r = max(r, 1e-4);

    vec2 invR = 1.0 / r;
    vec2 invR2 = invR * invR;

    vec2 pInvR = p * invR;
    float k1 = length(pInvR);

    vec2 pInvR2 = p * invR2;
    float k2 = length(pInvR2);

    return (k1 * (k1 - 1.0)) / max(k2, 1e-4);
}

float smoothUnion(float d1, float d2, float k) {
    if (k <= 0.0) {
        return min(d1, d2);
    }
    float e = max(k - abs(d1 - d2), 0.0);
    return min(d1, d2) - e * e * 0.25 / k;
}

float getShapeSDF(float type, vec2 p, vec2 center, vec2 size, float r) {
    if (type == 1.0) { // squircle
        return sdfSquircle(p - center, size / 2.0, r);
    }
    if (type == 2.0) { // ellipse
        return sdfEllipse(p - center, size / 2.0);
    }
    if (type == 3.0) { // rounded rectangle
        return sdfRRect(p - center, size / 2.0, r);
    }
    return 1e9; // none
}

float getShapeSDFFromValues(
    float type,
    float centerX,
    float centerY,
    float sizeW,
    float sizeH,
    float cornerRadius,
    vec2 p
) {
    return getShapeSDF(
        type,
        p,
        vec2(centerX, centerY),
        vec2(sizeW, sizeH),
        cornerRadius
    );
}

float sceneSDF(vec2 p, int numShapes, float blend) {
    if (numShapes == 0) {
        return 1e9;
    }

    float result = getShapeSDFFromValues(uShapeData[0], uShapeData[1], uShapeData[2], uShapeData[3], uShapeData[4], uShapeData[5], p);

    // Fully unrolled with literal uniform-array indices. Flutter's SkSL
    // compiler rejects dynamic uniform-array indexing in Impeller shaders.
    if (numShapes >= 2) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[6], uShapeData[7], uShapeData[8], uShapeData[9], uShapeData[10], uShapeData[11], p), blend);
    if (numShapes >= 3) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[12], uShapeData[13], uShapeData[14], uShapeData[15], uShapeData[16], uShapeData[17], p), blend);
    if (numShapes >= 4) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[18], uShapeData[19], uShapeData[20], uShapeData[21], uShapeData[22], uShapeData[23], p), blend);
    if (numShapes >= 5) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[24], uShapeData[25], uShapeData[26], uShapeData[27], uShapeData[28], uShapeData[29], p), blend);
    if (numShapes >= 6) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[30], uShapeData[31], uShapeData[32], uShapeData[33], uShapeData[34], uShapeData[35], p), blend);
    if (numShapes >= 7) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[36], uShapeData[37], uShapeData[38], uShapeData[39], uShapeData[40], uShapeData[41], p), blend);
    if (numShapes >= 8) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[42], uShapeData[43], uShapeData[44], uShapeData[45], uShapeData[46], uShapeData[47], p), blend);
    if (numShapes >= 9) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[48], uShapeData[49], uShapeData[50], uShapeData[51], uShapeData[52], uShapeData[53], p), blend);
    if (numShapes >= 10) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[54], uShapeData[55], uShapeData[56], uShapeData[57], uShapeData[58], uShapeData[59], p), blend);
    if (numShapes >= 11) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[60], uShapeData[61], uShapeData[62], uShapeData[63], uShapeData[64], uShapeData[65], p), blend);
    if (numShapes >= 12) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[66], uShapeData[67], uShapeData[68], uShapeData[69], uShapeData[70], uShapeData[71], p), blend);
    if (numShapes >= 13) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[72], uShapeData[73], uShapeData[74], uShapeData[75], uShapeData[76], uShapeData[77], p), blend);
    if (numShapes >= 14) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[78], uShapeData[79], uShapeData[80], uShapeData[81], uShapeData[82], uShapeData[83], p), blend);
    if (numShapes >= 15) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[84], uShapeData[85], uShapeData[86], uShapeData[87], uShapeData[88], uShapeData[89], p), blend);
    if (numShapes >= 16) result = smoothUnion(result, getShapeSDFFromValues(uShapeData[90], uShapeData[91], uShapeData[92], uShapeData[93], uShapeData[94], uShapeData[95], p), blend);

    return result;
}

// Calculate 3D normal with finite differences. Flutter's SkSL compiler rejects
// derivative intrinsics in these runtime effects on some targets.
vec3 getNormal(vec2 p, float thickness, int numShapes, float blend) {
    float sd = sceneSDF(p, numShapes, blend);
    float sampleOffset = 1.0;
    float dx = sceneSDF(p + vec2(sampleOffset, 0.0), numShapes, blend) -
        sceneSDF(p - vec2(sampleOffset, 0.0), numShapes, blend);
    float dy = sceneSDF(p + vec2(0.0, sampleOffset), numShapes, blend) -
        sceneSDF(p - vec2(0.0, sampleOffset), numShapes, blend);

    // The cosine and sine between normal and the xy plane
    float safeThickness = max(thickness, 0.001);
    float n_cos = max(safeThickness + sd, 0.0) / safeThickness;
    float n_sin = sqrt(max(0.0, 1.0 - n_cos * n_cos));

    return normalize(vec3(dx * n_cos, dy * n_cos, n_sin));
}
