from __future__ import annotations

import math
from dataclasses import dataclass


EARTH_RADIUS_M = 6_371_000.0
MAX_COORDINATE_LAT = 90.0
MAX_COORDINATE_LNG = 180.0
MIN_GEOFENCE_RADIUS_M = 0.1
MAX_GEOFENCE_RADIUS_M = 5_000.0
DEFAULT_MAX_ALLOWED_ACCURACY_M = 30.0

REASON_INVALID_USER_COORDINATES = "invalid_user_coordinates"
REASON_INVALID_EVENT_COORDINATES = "invalid_event_coordinates"
REASON_INVALID_GEOFENCE_RADIUS = "invalid_geofence_radius"
REASON_GEOFENCE_RADIUS_OUT_OF_RANGE = "geofence_radius_out_of_range"
REASON_ACCURACY_MISSING = "accuracy_missing"
REASON_INVALID_ACCURACY = "invalid_accuracy"
REASON_ACCURACY_EXCEEDS_LIMIT = "accuracy_exceeds_limit"
REASON_OUTSIDE_GEOFENCE = "outside_geofence"
REASON_OUTSIDE_GEOFENCE_BUFFERED = "outside_geofence_buffered"


@dataclass(frozen=True)
class GeoCheckResult:
    ok: bool
    distance_m: float
    radius_m: float
    effective_distance_m: float | None = None
    reason: str | None = None


def _to_finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def normalize_coordinates(
    latitude: object,
    longitude: object,
    *,
    actor: str,
) -> tuple[float | None, float | None, str | None]:
    normalized_latitude = _to_finite_float(latitude)
    normalized_longitude = _to_finite_float(longitude)

    if normalized_latitude is None or normalized_longitude is None:
        return None, None, f"invalid_{actor}_coordinates"

    if not -MAX_COORDINATE_LAT <= normalized_latitude <= MAX_COORDINATE_LAT:
        return None, None, f"invalid_{actor}_coordinates"

    if not -MAX_COORDINATE_LNG <= normalized_longitude <= MAX_COORDINATE_LNG:
        return None, None, f"invalid_{actor}_coordinates"

    return normalized_latitude, normalized_longitude, None


def normalize_radius_m(
    radius_m: object,
    *,
    min_radius_m: float = MIN_GEOFENCE_RADIUS_M,
    max_radius_m: float = MAX_GEOFENCE_RADIUS_M,
) -> tuple[float | None, str | None]:
    normalized_radius = _to_finite_float(radius_m)
    if normalized_radius is None:
        return None, REASON_INVALID_GEOFENCE_RADIUS

    if normalized_radius <= 0:
        return None, REASON_INVALID_GEOFENCE_RADIUS

    if normalized_radius < min_radius_m or normalized_radius > max_radius_m:
        return None, REASON_GEOFENCE_RADIUS_OUT_OF_RANGE

    return normalized_radius, None


def normalize_accuracy_m(accuracy_m: object) -> tuple[float | None, str | None]:
    if accuracy_m is None:
        return None, None

    normalized_accuracy = _to_finite_float(accuracy_m)
    if normalized_accuracy is None or normalized_accuracy <= 0:
        return None, REASON_INVALID_ACCURACY

    return normalized_accuracy, None


def normalize_accuracy_limit_m(max_allowed_accuracy_m: object) -> float:
    normalized_limit = _to_finite_float(max_allowed_accuracy_m)
    if normalized_limit is None or normalized_limit <= 0:
        return DEFAULT_MAX_ALLOWED_ACCURACY_M
    return normalized_limit


def recommended_accuracy_limit_m(radius_m: float) -> float:
    """
    Practical default for school attendance geofences.

    Small geofences need tighter GPS accuracy; larger geofences can tolerate more.
    """
    normalized_radius, reason = normalize_radius_m(radius_m)
    if normalized_radius is None:
        raise ValueError(reason or REASON_INVALID_GEOFENCE_RADIUS)

    if normalized_radius <= 30:
        return 10.0
    if normalized_radius <= 75:
        return 20.0
    if normalized_radius <= 150:
        return 35.0
    if normalized_radius <= 300:
        return 50.0
    return min(100.0, max(60.0, normalized_radius * 0.25))


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2) ** 2)
    )
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_M * c


def is_accuracy_ok(
    accuracy_m: float,
    max_allowed_accuracy_m: float = DEFAULT_MAX_ALLOWED_ACCURACY_M,
) -> bool:
    normalized_accuracy, reason = normalize_accuracy_m(accuracy_m)
    if reason is not None or normalized_accuracy is None:
        return False

    return normalized_accuracy <= normalize_accuracy_limit_m(max_allowed_accuracy_m)


def geofence_check(
    user_lat: float,
    user_lng: float,
    event_lat: float,
    event_lng: float,
    radius_m: float,
    accuracy_m: float | None = None,
    max_allowed_accuracy_m: float = DEFAULT_MAX_ALLOWED_ACCURACY_M,
    require_accuracy: bool = False,
    use_accuracy_buffer: bool = True,
) -> GeoCheckResult:
    """
    Check whether a student is inside the event geofence.

    Beginner-friendly rules:
    - Invalid coordinates or radius return a failure result instead of raising.
    - Accuracy is optional unless require_accuracy=True.
    - When use_accuracy_buffer=True, the GPS uncertainty is added to the distance
      so attendance is only accepted when the device is confidently inside.
    """
    normalized_user_lat, normalized_user_lng, user_reason = normalize_coordinates(
        user_lat,
        user_lng,
        actor="user",
    )
    if user_reason is not None:
        return GeoCheckResult(
            ok=False,
            distance_m=0.0,
            radius_m=0.0,
            reason=user_reason,
        )

    normalized_event_lat, normalized_event_lng, event_reason = normalize_coordinates(
        event_lat,
        event_lng,
        actor="event",
    )
    if event_reason is not None:
        return GeoCheckResult(
            ok=False,
            distance_m=0.0,
            radius_m=0.0,
            reason=event_reason,
        )

    normalized_radius, radius_reason = normalize_radius_m(radius_m)
    if radius_reason is not None or normalized_radius is None:
        return GeoCheckResult(
            ok=False,
            distance_m=0.0,
            radius_m=0.0,
            reason=radius_reason,
        )

    if require_accuracy and accuracy_m is None:
        return GeoCheckResult(
            ok=False,
            distance_m=0.0,
            radius_m=normalized_radius,
            reason=REASON_ACCURACY_MISSING,
        )

    normalized_accuracy, accuracy_reason = normalize_accuracy_m(accuracy_m)
    if accuracy_reason is not None:
        return GeoCheckResult(
            ok=False,
            distance_m=0.0,
            radius_m=normalized_radius,
            reason=accuracy_reason,
        )

    accuracy_limit = normalize_accuracy_limit_m(max_allowed_accuracy_m)
    if normalized_accuracy is not None and normalized_accuracy > accuracy_limit:
        return GeoCheckResult(
            ok=False,
            distance_m=0.0,
            radius_m=normalized_radius,
            reason=REASON_ACCURACY_EXCEEDS_LIMIT,
        )

    distance = haversine_m(
        normalized_user_lat,
        normalized_user_lng,
        normalized_event_lat,
        normalized_event_lng,
    )

    if use_accuracy_buffer and normalized_accuracy is not None:
        effective_distance = distance + normalized_accuracy
    else:
        effective_distance = distance

    if effective_distance <= normalized_radius:
        return GeoCheckResult(
            ok=True,
            distance_m=float(distance),
            radius_m=float(normalized_radius),
            effective_distance_m=float(effective_distance),
            reason=None,
        )

    return GeoCheckResult(
        ok=False,
        distance_m=float(distance),
        radius_m=float(normalized_radius),
        effective_distance_m=float(effective_distance),
        reason=(
            REASON_OUTSIDE_GEOFENCE_BUFFERED
            if use_accuracy_buffer and normalized_accuracy is not None
            else REASON_OUTSIDE_GEOFENCE
        ),
    )
