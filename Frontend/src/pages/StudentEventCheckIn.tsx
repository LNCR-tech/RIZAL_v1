import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import {
  FaCalendarAlt,
  FaCheckCircle,
  FaCompass,
  FaExclamationTriangle,
  FaMapMarkerAlt,
  FaShieldAlt,
} from "react-icons/fa";

import type { Event } from "../api/eventsApi";
import { fetchAllEvents } from "../api/eventsApi";
import {
  describeStudentEventCheckInError,
  type EventLocationVerificationResponse,
  submitStudentEventAttendanceScan,
  type StudentEventAttendanceScanResponse,
  type StudentEventLocationPayload,
  verifyStudentEventLocation,
  StudentEventCheckInApiError,
} from "../api/studentEventCheckInApi";
import {
  fetchStudentFaceEnrollmentStatus,
  setStudentFaceEnrollmentRequired,
} from "../api/studentFaceEnrollmentApi";
import { resolveDashboardPath } from "../authFlow";
import CameraFeed from "../components/CameraFeed";
import "../css/FacialVerification.css";
import "../css/StudentEventCheckIn.css";

type StoredUser = {
  id?: number;
  roles?: string[];
};

type ScanPhase =
  | "loading"
  | "empty"
  | "scanning"
  | "submitting"
  | "success"
  | "error";
type LocationPhase = "checking" | "ready" | "error";

const VERIFY_PROGRESS_FRAMES = 10;
const RESULT_REVEAL_DELAY_MS = 700;
const GEOLOCATION_TIMEOUT_MS = 18000;
const GEOLOCATION_MAX_INPUT_ACCURACY_M = 5000;

const normalizeRole = (role: string) =>
  role.trim().toLowerCase().replace(/_/g, "-");

const parseStoredUser = (): StoredUser | null => {
  const raw = localStorage.getItem("user");
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
};

const hasGeofence = (event: Event) =>
  event.geo_latitude != null &&
  event.geo_longitude != null &&
  event.geo_radius_m != null;

const formatEventDateTime = (value: string) =>
  new Date(value).toLocaleString("en-PH", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

const toProgressPercent = (value: number, target: number) =>
  Math.max(0, Math.min(100, Math.round((value / target) * 100)));

const wait = (durationMs: number) =>
  new Promise<void>((resolve) => {
    window.setTimeout(resolve, durationMs);
  });

const buildLocationErrorMessage = (detail: unknown) => {
  if (!detail || typeof detail !== "object") {
    return "Location verification failed.";
  }

  const accuracy = (detail as { accuracy_m?: unknown }).accuracy_m;
  const formattedAccuracy =
    typeof accuracy === "number" && Number.isFinite(accuracy)
      ? `${Math.round(accuracy)}m`
      : "too low";
  const reason = (detail as { reason?: unknown }).reason;
  if (typeof reason === "string" && reason.trim()) {
    if (reason.startsWith("gps_accuracy_too_low:")) {
      return `GPS accuracy is ${formattedAccuracy}. Enable precise location and wait for a stronger GPS signal before signing in.`;
    }

    if (reason === "gps_accuracy_missing" || reason === "accuracy_missing") {
      return "This event requires a precise GPS reading, but the browser did not provide one.";
    }

    if (reason === "gps_accuracy_invalid" || reason === "invalid_accuracy") {
      return "The device returned an invalid GPS accuracy reading. Try again after refreshing location services.";
    }

    if (
      reason === "gps_accuracy_too_low" ||
      reason === "accuracy_exceeds_limit"
    ) {
      return `GPS accuracy is ${formattedAccuracy}. Enable precise location and wait for a stronger GPS signal before signing in.`;
    }

    if (
      reason === "outside_geofence_with_uncertainty" ||
      reason === "outside_geofence_buffered"
    ) {
      return "Your current GPS signal is too weak to confirm that you are inside the event area.";
    }

    if (reason === "outside_geofence") {
      return "You are outside the allowed event location.";
    }

    if (reason === "invalid_user_coordinates") {
      return "The device returned an invalid location reading. Refresh location services and try again.";
    }

    if (reason === "invalid_event_coordinates") {
      return "This event has an invalid location setup. Ask the organizer to update the event map marker.";
    }

    if (
      reason === "invalid_geofence_radius" ||
      reason === "geofence_radius_out_of_range"
    ) {
      return "This event geofence is not configured correctly. Ask the organizer to update the event radius.";
    }

    return reason;
  }

  const distance = (detail as { distance_m?: unknown }).distance_m;
  const radius = (detail as { radius_m?: unknown }).radius_m;
  if (typeof distance === "number" && typeof radius === "number") {
    return `You are ${distance.toFixed(1)}m away. Stay within ${radius.toFixed(
      0
    )}m of the event location.`;
  }

  return "Location verification failed.";
};

const getCurrentLocation = (
  maxAllowedAccuracyM: number,
  onAccuracyUpdate?: (accuracyM: number) => void
) =>
  new Promise<StudentEventLocationPayload>((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation is not supported on this device."));
      return;
    }

    const accuracyTarget = Math.max(1, Math.min(maxAllowedAccuracyM, 1000));
    let settled = false;
    let watchId: number | null = null;
    let timeoutId: number | null = null;
    let bestPosition: GeolocationPosition | null = null;
    let bestAccuracy = Number.POSITIVE_INFINITY;

    const cleanup = () => {
      if (watchId != null) {
        navigator.geolocation.clearWatch(watchId);
      }

      if (timeoutId != null) {
        window.clearTimeout(timeoutId);
      }
    };

    const finishSuccess = (position: GeolocationPosition) => {
      if (settled) {
        return;
      }

      settled = true;
      cleanup();
      resolve({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracyM: position.coords.accuracy,
      });
    };

    const finishError = (message: string) => {
      if (settled) {
        return;
      }

      settled = true;
      cleanup();
      reject(new Error(message));
    };

    const handlePosition = (position: GeolocationPosition) => {
      const accuracy = position.coords.accuracy;
      if (!Number.isFinite(accuracy) || accuracy <= 0) {
        return;
      }

      onAccuracyUpdate?.(accuracy);

      if (accuracy < bestAccuracy) {
        bestAccuracy = accuracy;
        bestPosition = position;
      }

      if (accuracy <= accuracyTarget) {
        finishSuccess(position);
      }
    };

    const handleError = (error: GeolocationPositionError) => {
      switch (error.code) {
        case error.PERMISSION_DENIED:
          finishError(
            "Location permission was denied. Allow location access to continue."
          );
          return;
        case error.POSITION_UNAVAILABLE:
          finishError("Current location is unavailable on this device.");
          return;
        case error.TIMEOUT:
          finishError("Location lookup timed out. Try again.");
          return;
        default:
          finishError("Failed to read the current device location.");
      }
    };

    watchId = navigator.geolocation.watchPosition(handlePosition, handleError, {
      enableHighAccuracy: true,
      timeout: GEOLOCATION_TIMEOUT_MS,
      maximumAge: 0,
    });

    timeoutId = window.setTimeout(() => {
      if (bestPosition && bestAccuracy <= GEOLOCATION_MAX_INPUT_ACCURACY_M) {
        finishError(
          `GPS accuracy is still ${Math.round(
            bestAccuracy
          )}m. Enable precise location and wait for a stronger GPS signal before signing in.`
        );
        return;
      }

      if (bestPosition) {
        finishError(
          `GPS accuracy is ${Math.round(
            bestAccuracy
          )}m. The device is only providing an approximate location right now.`
        );
        return;
      }

      finishError("Location lookup timed out. Try again.");
    }, GEOLOCATION_TIMEOUT_MS);
  });

const normalizeGeoFailure = (detail: unknown) => {
  if (!detail || typeof detail !== "object") {
    return null;
  }

  const distance = (detail as { distance_m?: unknown }).distance_m;
  const radius = (detail as { radius_m?: unknown }).radius_m;
  if (typeof distance !== "number" || typeof radius !== "number") {
    return null;
  }

  return {
    ok: false,
    reason:
      typeof (detail as { reason?: unknown }).reason === "string"
        ? ((detail as { reason?: string }).reason ?? null)
        : null,
    distance_m: distance,
    effective_distance_m:
      typeof (detail as { effective_distance_m?: unknown }).effective_distance_m ===
      "number"
        ? ((detail as { effective_distance_m?: number }).effective_distance_m ??
          null)
        : null,
    radius_m: radius,
    accuracy_m:
      typeof (detail as { accuracy_m?: unknown }).accuracy_m === "number"
        ? ((detail as { accuracy_m?: number }).accuracy_m ?? null)
        : null,
  } satisfies EventLocationVerificationResponse;
};

const buildAttendanceMessage = (
  result: StudentEventAttendanceScanResponse
) => {
  if (result.message && result.message.trim()) {
    return result.message;
  }

  if (result.action === "time_in") {
    if (result.geo?.distance_m != null) {
      return `Signed in successfully. You were ${result.geo.distance_m.toFixed(
        1
      )}m from the event venue.`;
    }
    return "Signed in successfully.";
  }

  return result.duration_minutes != null
    ? `Signed out successfully. Duration: ${result.duration_minutes} minutes.`
    : "Signed out successfully.";
};

const StudentEventCheckIn = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const storedUser = useMemo(parseStoredUser, []);
  const normalizedRoles = useMemo(
    () => (storedUser?.roles || []).map(normalizeRole),
    [storedUser]
  );
  const requestedEventId = useMemo(() => {
    const rawValue = searchParams.get("eventId");
    if (!rawValue) {
      return null;
    }

    const parsedValue = Number(rawValue);
    return Number.isFinite(parsedValue) && parsedValue > 0 ? parsedValue : null;
  }, [searchParams]);

  const latestFrameRef = useRef<Blob | null>(null);
  const scanSessionRef = useRef(0);
  const locationPromiseRef = useRef<Promise<StudentEventLocationPayload> | null>(
    null
  );
  const progressAnimationRef = useRef<number | null>(null);
  const displayedProgressRef = useRef(0);
  const scanProgressFramesRef = useRef(0);
  const processingFrameRef = useRef(false);
  const scanFinalizedRef = useRef(false);

  const [loadingMessage, setLoadingMessage] = useState(
    "Preparing event sign-in..."
  );
  const [pageReady, setPageReady] = useState(false);
  const [phase, setPhase] = useState<ScanPhase>("loading");
  const [streamEnabled, setStreamEnabled] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [scanProgressFrames, setScanProgressFrames] = useState(0);
  const [displayedProgress, setDisplayedProgress] = useState(0);
  const [statusText, setStatusText] = useState(
    "Align your face inside the circle."
  );
  const [studentLabel, setStudentLabel] = useState("Student");
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [locationPhase, setLocationPhase] = useState<LocationPhase>("checking");
  const [locationMessage, setLocationMessage] = useState(
    "Checking event location..."
  );
  const [locationInfo, setLocationInfo] =
    useState<StudentEventLocationPayload | null>(null);
  const [locationCheck, setLocationCheck] =
    useState<EventLocationVerificationResponse | null>(null);

  const availableEvents = useMemo(
    () =>
      events
        .filter((event) => event.status === "ongoing" && hasGeofence(event))
        .sort(
          (left, right) =>
            new Date(left.start_datetime).getTime() -
            new Date(right.start_datetime).getTime()
        ),
    [events]
  );

  const selectedEvent = useMemo(
    () =>
      availableEvents.find((event) => event.id === selectedEventId) ??
      availableEvents[0] ??
      null,
    [availableEvents, selectedEventId]
  );

  const progressPercent = toProgressPercent(
    scanProgressFrames,
    VERIFY_PROGRESS_FRAMES
  );
  const scanLabel =
    phase === "submitting" ? "Finalizing sign in..." : "Verifying face...";
  const subjectLabel = selectedEvent
    ? `${studentLabel} • ${selectedEvent.name}`
    : studentLabel;

  const clearProgressAnimation = () => {
    if (progressAnimationRef.current) {
      window.cancelAnimationFrame(progressAnimationRef.current);
      progressAnimationRef.current = null;
    }
  };

  const stopScanner = useCallback(() => {
    setStreamEnabled(false);
    setCameraActive(false);
  }, []);

  const resetScanProgress = useCallback(() => {
    scanProgressFramesRef.current = 0;
    setScanProgressFrames(0);
  }, []);

  const cancelScanSession = useCallback(() => {
    scanSessionRef.current += 1;
    locationPromiseRef.current = null;
    latestFrameRef.current = null;
    processingFrameRef.current = false;
    scanFinalizedRef.current = false;
    resetScanProgress();
    stopScanner();
  }, [resetScanProgress, stopScanner]);

  useEffect(
    () => () => {
      cancelScanSession();
      clearProgressAnimation();
    },
    [cancelScanSession]
  );

  useEffect(() => {
    clearProgressAnimation();

    const startValue = displayedProgressRef.current;
    const targetValue = progressPercent;

    if (startValue === targetValue) {
      return;
    }

    const animationStart = window.performance.now();
    const animationDuration = targetValue < startValue ? 160 : 260;

    const tick = (timestamp: number) => {
      const elapsed = timestamp - animationStart;
      const progress = Math.min(1, elapsed / animationDuration);
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      const nextValue =
        startValue + (targetValue - startValue) * easedProgress;

      displayedProgressRef.current = nextValue;
      setDisplayedProgress(nextValue);

      if (progress < 1) {
        progressAnimationRef.current = window.requestAnimationFrame(tick);
        return;
      }

      progressAnimationRef.current = null;
    };

    progressAnimationRef.current = window.requestAnimationFrame(tick);

    return () => {
      clearProgressAnimation();
    };
  }, [progressPercent]);

  useEffect(() => {
    if (
      requestedEventId != null &&
      availableEvents.some((event) => event.id === requestedEventId)
    ) {
      setSelectedEventId(requestedEventId);
      return;
    }

    if (!selectedEvent && availableEvents.length > 0) {
      setSelectedEventId(availableEvents[0].id);
    }
  }, [availableEvents, requestedEventId, selectedEvent]);

  useEffect(() => {
    if (!storedUser?.roles?.length) {
      navigate("/", { replace: true });
      return;
    }

    const loadPage = async () => {
      setPageReady(false);
      setPhase("loading");
      setLoadingMessage("Checking student face registration...");

      try {
        const faceStatus = await fetchStudentFaceEnrollmentStatus();
        const nextDashboardPath = resolveDashboardPath(
          faceStatus.roles.length > 0 ? faceStatus.roles : normalizedRoles
        );

        if (!faceStatus.hasStudentRole || !faceStatus.hasStudentProfile) {
          navigate(nextDashboardPath, { replace: true });
          return;
        }

        if (!faceStatus.faceRegistered) {
          if (faceStatus.userId != null) {
            setStudentFaceEnrollmentRequired(faceStatus.userId, true);
          }
          navigate("/student_face_registration", { replace: true });
          return;
        }

        setStudentLabel(faceStatus.studentId || "Student");

        setLoadingMessage("Loading ongoing events...");
        const allEvents = await fetchAllEvents(true);
        setEvents(allEvents);
        setPageReady(true);
      } catch (error) {
        setPageReady(false);
        setPhase("error");
        setResultMessage(
          error instanceof Error
            ? error.message
            : "Failed to load event sign-in."
        );
      }
    };

    void loadPage();
  }, [navigate, normalizedRoles, storedUser]);

  const finalizeScan = useCallback(
    async (
      sessionId: number,
      event: Event,
      frameBlob: Blob
    ) => {
      if (scanSessionRef.current !== sessionId || scanFinalizedRef.current) {
        return;
      }

      scanFinalizedRef.current = true;
      processingFrameRef.current = false;
      setScanProgressFrames(VERIFY_PROGRESS_FRAMES);
      scanProgressFramesRef.current = VERIFY_PROGRESS_FRAMES;
      stopScanner();
      setPhase("submitting");
      setStatusText("Finalizing face and location verification...");

      await wait(RESULT_REVEAL_DELAY_MS);

      if (scanSessionRef.current !== sessionId) {
        return;
      }

      let location: StudentEventLocationPayload;
      try {
        location = await (locationPromiseRef.current ??
          Promise.reject(
            new Error("Location verification did not complete in time.")
          ));
      } catch (error) {
        if (scanSessionRef.current !== sessionId) {
          return;
        }

        if (error instanceof StudentEventCheckInApiError) {
          const geoDetail = normalizeGeoFailure(error.detail);
          if (geoDetail) {
            setLocationCheck(geoDetail);
            setPhase("error");
            setResultMessage(buildLocationErrorMessage(geoDetail));
            return;
          }
        }

        setPhase("error");
        setResultMessage(
          error instanceof Error
            ? error.message
            : "Location verification failed."
        );
        return;
      }

      try {
        const result = await submitStudentEventAttendanceScan({
          eventId: event.id,
          imageBlob: frameBlob,
          location,
        });

        if (scanSessionRef.current !== sessionId) {
          return;
        }

        if (result.geo) {
          setLocationCheck(result.geo);
        }

        setPhase("success");
        setStatusText(
          result.action === "time_in"
            ? "Face and location verified."
            : "Face and location verified for sign-out."
        );
        setResultMessage(buildAttendanceMessage(result));
      } catch (error) {
        if (scanSessionRef.current !== sessionId) {
          return;
        }

        if (error instanceof StudentEventCheckInApiError) {
          const geoDetail = normalizeGeoFailure(error.detail);
          if (geoDetail) {
            setLocationCheck(geoDetail);
            setResultMessage(buildLocationErrorMessage(geoDetail));
            setPhase("error");
            return;
          }
        }

        setPhase("error");
        setResultMessage(describeStudentEventCheckInError(error));
      }
    },
    [stopScanner]
  );

  useEffect(() => {
    if (!pageReady) {
      return;
    }

    if (availableEvents.length > 0 && !selectedEvent) {
      return;
    }

    if (!selectedEvent) {
      cancelScanSession();
      setPhase("empty");
      setStatusText("No ongoing geofenced event is available for sign-in.");
      setResultMessage(null);
      return;
    }

    cancelScanSession();
    const sessionId = scanSessionRef.current;

    setPhase("scanning");
    setStreamEnabled(true);
    setStatusText("Starting camera and checking event location...");
    setResultMessage(null);
    setLocationPhase("checking");
    setLocationMessage("Checking event location...");
    setLocationInfo(null);
    setLocationCheck(null);

    locationPromiseRef.current = (async () => {
      try {
        const currentLocation = await getCurrentLocation(
          selectedEvent.geo_max_accuracy_m ?? 50,
          (accuracyM) => {
            if (scanSessionRef.current !== sessionId) {
              return;
            }

            if (accuracyM > (selectedEvent.geo_max_accuracy_m ?? 50)) {
              setLocationMessage(
                `Waiting for a precise GPS fix... current accuracy ${Math.round(
                  accuracyM
                )}m.`
              );
              return;
            }

            setLocationMessage(
              `GPS locked at ${Math.round(accuracyM)}m accuracy.`
            );
          }
        );
        if (scanSessionRef.current !== sessionId) {
          throw new Error("Session changed.");
        }

        setLocationInfo(currentLocation);
        const locationResult = await verifyStudentEventLocation(
          selectedEvent.id,
          currentLocation
        );

        if (scanSessionRef.current !== sessionId) {
          throw new Error("Session changed.");
        }

        setLocationCheck(locationResult);
        if (!locationResult.ok) {
          const message = buildLocationErrorMessage(locationResult);
          setLocationPhase("error");
          setLocationMessage(message);
          throw new Error(message);
        }

        setLocationPhase("ready");
        setLocationMessage("Location verified.");
        return currentLocation;
      } catch (error) {
        if (scanSessionRef.current === sessionId) {
          const message =
            error instanceof StudentEventCheckInApiError
              ? buildLocationErrorMessage(error.detail)
              : error instanceof Error
                ? error.message
                : "Location verification failed.";
          setLocationPhase("error");
          setLocationMessage(message);
        }
        throw error;
      }
    })();
  }, [availableEvents.length, cancelScanSession, pageReady, selectedEvent]);

  const handleFrame = useCallback(
    async (blob: Blob) => {
      if (
        phase !== "scanning" ||
        !selectedEvent ||
        processingFrameRef.current ||
        scanFinalizedRef.current
      ) {
        return;
      }

      processingFrameRef.current = true;
      latestFrameRef.current = blob;

      try {
        const nextFrameCount = Math.min(
          VERIFY_PROGRESS_FRAMES,
          scanProgressFramesRef.current + 1
        );
        scanProgressFramesRef.current = nextFrameCount;
        setScanProgressFrames(nextFrameCount);

        if (nextFrameCount < VERIFY_PROGRESS_FRAMES) {
          return;
        }

        await finalizeScan(scanSessionRef.current, selectedEvent, blob);
      } finally {
        if (!scanFinalizedRef.current) {
          processingFrameRef.current = false;
        }
      }
    },
    [finalizeScan, phase, selectedEvent]
  );

  const eventSubtitle = selectedEvent
    ? `${formatEventDateTime(selectedEvent.start_datetime)} • ${selectedEvent.location}`
    : "Select an ongoing event from the event list.";

  if (!storedUser) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="student-event-checkin-page">
      <main className="student-event-checkin-shell">
        {phase === "loading" ? (
          <section className="face-flow-shell student-event-checkin-flow">
            <article className="face-flow-card student-event-checkin-card">
              <div className="student-event-checkin-state">
                <div className="student-event-checkin-spinner" />
                <p>{loadingMessage}</p>
              </div>
            </article>
          </section>
        ) : phase === "empty" ? (
          <section className="face-flow-shell student-event-checkin-flow">
            <article className="face-flow-card student-event-checkin-card">
              <div className="face-flow-intro">
                <div className="face-flow-intro__icon face-flow-intro__icon--error">
                  <FaExclamationTriangle />
                </div>
                <p>{statusText}</p>
              </div>
            </article>
          </section>
        ) : (
          <section className="face-flow-shell student-event-checkin-flow">
            <article className="face-flow-card student-event-checkin-card">
              <div className="student-event-checkin-header">
                <span className="student-event-checkin-badge">
                  <FaShieldAlt />
                  Event Sign In
                </span>
                <h1>{selectedEvent?.name || "Ongoing Event"}</h1>
                <div className="student-event-checkin-meta">
                  <span>
                    <FaCalendarAlt />
                    {eventSubtitle}
                  </span>
                  {selectedEvent?.geo_radius_m != null ? (
                    <span>
                      <FaMapMarkerAlt />
                      {Math.round(selectedEvent.geo_radius_m)}m allowed radius
                    </span>
                  ) : null}
                </div>
              </div>

              {phase === "scanning" || phase === "submitting" ? (
                <div className="face-flow-scanner">
                  <div
                    className="face-flow-ring student-event-checkin-ring"
                    style={
                      {
                        ["--face-progress" as string]: `${displayedProgress}%`,
                      } as CSSProperties
                    }
                  >
                    <div className="face-flow-ring__inner">
                      <CameraFeed
                        streamEnabled={streamEnabled}
                        scanEnabled={phase === "scanning"}
                        showControls={false}
                        circleMask
                        placeholderText=""
                        onFrame={handleFrame}
                        onCameraStateChange={(isOn) => {
                          setCameraActive(isOn);
                          if (phase === "scanning") {
                            setStatusText(
                              isOn
                                ? "Verifying face and location..."
                                : "Starting camera and checking event location..."
                            );
                          }
                        }}
                        onScanError={(error) => {
                          stopScanner();
                          setPhase("error");
                          setResultMessage(describeStudentEventCheckInError(error));
                        }}
                      />
                    </div>
                  </div>

                  <div className="face-flow-progress">
                    <div className="face-flow-progress__value">
                      {Math.round(displayedProgress)}%
                    </div>
                    <div className="face-flow-progress__label">{scanLabel}</div>
                  </div>

                  <div className="student-event-checkin-statuses">
                    <span
                      className={`student-event-checkin-status student-event-checkin-status--${
                        cameraActive ? "ready" : "pending"
                      }`}
                    >
                      <FaShieldAlt />
                      {statusText}
                    </span>
                    <span
                      className={`student-event-checkin-status student-event-checkin-status--${locationPhase}`}
                    >
                      <FaCompass />
                      {locationMessage}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="face-flow-intro">
                  <div
                    className={`face-flow-intro__icon ${
                      phase === "success"
                        ? "face-flow-intro__icon--success"
                        : "face-flow-intro__icon--error"
                    }`}
                  >
                    {phase === "success" ? (
                      <FaCheckCircle />
                    ) : (
                      <FaExclamationTriangle />
                    )}
                  </div>
                  <p>{resultMessage || statusText}</p>
                  {locationCheck ? (
                    <div className="student-event-checkin-detail">
                      {locationCheck.ok
                        ? `Location confirmed at ${locationCheck.distance_m.toFixed(
                            1
                          )}m from the event marker.`
                        : buildLocationErrorMessage(locationCheck)}
                    </div>
                  ) : locationInfo ? (
                    <div className="student-event-checkin-detail">
                      GPS accuracy {Math.round(locationInfo.accuracyM || 0)}m
                    </div>
                  ) : null}
                </div>
              )}
            </article>

            <div className="face-flow-subject">{subjectLabel}</div>
          </section>
        )}
      </main>
    </div>
  );
};

export default StudentEventCheckIn;
