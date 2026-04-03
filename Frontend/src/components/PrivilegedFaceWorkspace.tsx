import { useCallback, useEffect, useRef, useState } from "react";
import {
  FaArrowRight,
  FaCheckCircle,
  FaFingerprint,
  FaShieldAlt,
  FaTrashAlt,
} from "react-icons/fa";

import CameraFeed from "./CameraFeed";
import {
  checkFacialLiveness,
  clearFacialReferenceProfile,
  type FacialVerificationApiError,
  type FacialVerificationRole,
  type FacialVerificationStatus,
  fetchFacialVerificationStatus,
  saveFacialReferenceProfile,
  type VerificationResult,
  verifyFacialIdentity,
} from "../api/facialVerificationApi";

type WorkspaceVariant = "login" | "manage";
type ScanMode = "register" | "verify";
type FlowStage =
  | "intro"
  | "scan"
  | "retry"
  | "ready_to_verify"
  | "complete"
  | "blocked";
type BusyState = "reference" | "verify" | "delete" | null;

const MIN_LIVENESS_SCORE = 0.85;
const SCAN_DURATION_MS = 8000;
const LOGIN_MAX_SCAN_ATTEMPTS = 3;
const COMPLETE_REDIRECT_DELAY_MS = 700;
const STATUS_RETRY_DELAY_MS = 4000;

type ScanCaptureState = {
  bestLiveBlob: Blob | null;
  bestLiveScore: number;
  lastIssue: string | null;
};

interface PrivilegedFaceWorkspaceProps {
  role: FacialVerificationRole;
  subjectId: string;
  subjectLabel: string;
  authToken?: string | null;
  variant: WorkspaceVariant;
  onVerified?: (result: VerificationResult) => void | Promise<void>;
  onCancel?: () => void;
}

const isMultipleFaceError = (detail: string) => {
  const normalized = detail.toLowerCase();
  return (
    normalized.includes("exactly one face") ||
    normalized.includes("exactly 1 face") ||
    normalized.includes("multiple faces")
  );
};

const isNoFaceError = (detail: string) =>
  detail.toLowerCase().includes("no face");

const describeAntiSpoofReason = (reason: string | null) => {
  switch (reason) {
    case "opencv_unavailable":
      return "Backend camera verification is not ready yet.";
    case "onnxruntime_unavailable":
      return "Backend camera verification is not ready yet.";
    case "model_missing":
      return "Anti-spoof model is missing on the backend.";
    case "session_unavailable":
      return "Anti-spoof service could not start.";
    default:
      return "Live anti-spoofing is not ready on the backend.";
  }
};

const describeFaceRuntimeReason = (reason: string | null) => {
  switch (reason) {
    case "insightface_model_download_pending":
      return "InsightFace is downloading its backend model package. This can take a few minutes the first time.";
    case "insightface_warming_up":
      return "InsightFace is starting on the backend. Please wait a moment.";
    case "insightface_initialization_failed":
      return "InsightFace could not finish starting on the backend.";
    case "deepface_unavailable":
      return "DeepFace is not installed or not ready on the backend.";
    case "insightface_unavailable":
      return "InsightFace is not installed or not ready on the backend.";
    case "unsupported_mode":
      return "The backend face verification mode is not supported.";
    default:
      return "Live face verification is not ready on the backend.";
  }
};

const isRetryableFaceRuntimeReason = (reason: string | null) =>
  reason === "insightface_model_download_pending" ||
  reason === "insightface_warming_up";

const toErrorDetail = (error: unknown) =>
  error instanceof Error ? error.message : "Face verification failed.";

const createEmptyScanCapture = (): ScanCaptureState => ({
  bestLiveBlob: null,
  bestLiveScore: 0,
  lastIssue: null,
});

const PrivilegedFaceWorkspace = ({
  role,
  subjectId,
  subjectLabel,
  authToken,
  variant,
  onVerified,
  onCancel,
}: PrivilegedFaceWorkspaceProps) => {
  const allowManagementActions = variant === "manage";
  const completionTimerRef = useRef<number | null>(null);
  const statusRetryTimerRef = useRef<number | null>(null);
  const scanAnimationRef = useRef<number | null>(null);
  const scanTimeoutRef = useRef<number | null>(null);
  const scanStartedAtRef = useRef<number | null>(null);
  const scanRunIdRef = useRef(0);
  const scanCaptureRef = useRef<ScanCaptureState>(createEmptyScanCapture());
  const failedAttemptsRef = useRef(0);

  const [referenceStatus, setReferenceStatus] =
    useState<FacialVerificationStatus | null>(null);
  const [flowStage, setFlowStage] = useState<FlowStage>("intro");
  const [scanMode, setScanMode] = useState<ScanMode>("register");
  const [statusLoading, setStatusLoading] = useState(true);
  const [busyState, setBusyState] = useState<BusyState>(null);
  const [streamEnabled, setStreamEnabled] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [statusText, setStatusText] = useState("Loading face verification.");
  const [errorText, setErrorText] = useState<string | null>(null);
  const [failedAttempts, setFailedAttempts] = useState(0);

  const referenceEnrolled = Boolean(referenceStatus?.faceReferenceEnrolled);
  const faceRuntimeReady = Boolean(referenceStatus?.faceRuntimeReady);
  const antiSpoofReady = Boolean(referenceStatus?.antiSpoofReady);
  const maxAttempts = variant === "login" ? LOGIN_MAX_SCAN_ATTEMPTS : null;
  const attemptsRemaining =
    maxAttempts !== null ? Math.max(0, maxAttempts - failedAttempts) : null;
  const scanLabel = !cameraReady
    ? "Starting camera..."
    : scanMode === "register"
      ? "Registering face..."
      : "Verifying face...";

  const clearCompletionTimer = useCallback(() => {
    if (completionTimerRef.current) {
      window.clearTimeout(completionTimerRef.current);
      completionTimerRef.current = null;
    }
  }, []);

  const clearStatusRetryTimer = useCallback(() => {
    if (statusRetryTimerRef.current) {
      window.clearTimeout(statusRetryTimerRef.current);
      statusRetryTimerRef.current = null;
    }
  }, []);

  const clearScanAnimation = useCallback(() => {
    if (scanAnimationRef.current) {
      window.cancelAnimationFrame(scanAnimationRef.current);
      scanAnimationRef.current = null;
    }
  }, []);

  const clearScanTimeout = useCallback(() => {
    if (scanTimeoutRef.current) {
      window.clearTimeout(scanTimeoutRef.current);
      scanTimeoutRef.current = null;
    }
  }, []);

  const clearScanRuntime = useCallback(() => {
    clearScanAnimation();
    clearScanTimeout();
    scanStartedAtRef.current = null;
  }, [clearScanAnimation, clearScanTimeout]);

  const stopScanner = useCallback(() => {
    clearScanRuntime();
    setStreamEnabled(false);
    setCameraReady(false);
  }, [clearScanRuntime]);

  const resetAttemptCounter = useCallback(() => {
    failedAttemptsRef.current = 0;
    setFailedAttempts(0);
  }, []);

  const resetScanCapture = useCallback(() => {
    scanCaptureRef.current = createEmptyScanCapture();
    setProgressPercent(0);
  }, []);

  const handleScanFailure = useCallback(
    (message: string) => {
      stopScanner();
      resetScanCapture();
      setBusyState(null);

      if (variant === "login") {
        const nextFailedAttempts = failedAttemptsRef.current + 1;
        failedAttemptsRef.current = nextFailedAttempts;
        setFailedAttempts(nextFailedAttempts);

        if (nextFailedAttempts >= LOGIN_MAX_SCAN_ATTEMPTS) {
          setFlowStage("blocked");
          setStatusText(`${message} Maximum attempts reached. Returning to login.`);
          setErrorText(null);
          if (onCancel) {
            clearCompletionTimer();
            completionTimerRef.current = window.setTimeout(() => {
              onCancel();
            }, COMPLETE_REDIRECT_DELAY_MS);
          }
          return;
        }
      }

      setFlowStage("retry");
      setStatusText(message);
      setErrorText(null);
    },
    [clearCompletionTimer, onCancel, resetScanCapture, stopScanner, variant]
  );

  const finalizeRegistration = useCallback(
    async (blob: Blob) => {
      setBusyState("reference");

      try {
        await saveFacialReferenceProfile({
          role,
          subjectId,
          imageSource: blob,
          authToken,
        });

        setReferenceStatus((currentStatus) =>
          currentStatus
            ? {
                ...currentStatus,
                faceReferenceEnrolled: true,
              }
            : currentStatus
        );
        resetAttemptCounter();
        setStatusText("Face registered.");
        setErrorText(null);
        setFlowStage("ready_to_verify");
      } catch (error) {
        handleScanFailure(toErrorDetail(error));
      } finally {
        setBusyState(null);
      }
    },
    [authToken, handleScanFailure, resetAttemptCounter, role, subjectId]
  );

  const finalizeVerification = useCallback(
    async (blob: Blob) => {
      setBusyState("verify");

      try {
        const result = await verifyFacialIdentity({
          role,
          subjectId,
          probeImageSource: blob,
          authToken,
          persistAttemptMode: allowManagementActions ? "matched" : "never",
        });

        if (!result.attempt.matched) {
          handleScanFailure("Face not matched.");
          return;
        }

        resetAttemptCounter();
        setErrorText(null);
        setStatusText("Face verified.");
        setFlowStage("complete");

        if (onVerified) {
          completionTimerRef.current = window.setTimeout(() => {
            void onVerified(result);
          }, COMPLETE_REDIRECT_DELAY_MS);
        }
      } catch (error) {
        handleScanFailure(toErrorDetail(error));
      } finally {
        setBusyState(null);
      }
    },
    [
      allowManagementActions,
      authToken,
      handleScanFailure,
      onVerified,
      resetAttemptCounter,
      role,
      subjectId,
    ]
  );

  const finishTimedScan = useCallback(
    async (runId: number, mode: ScanMode) => {
      if (runId !== scanRunIdRef.current) {
        return;
      }

      clearScanRuntime();
      stopScanner();
      setProgressPercent(100);

      const bestLiveBlob = scanCaptureRef.current.bestLiveBlob;
      if (!bestLiveBlob) {
        handleScanFailure(
          scanCaptureRef.current.lastIssue ||
            "No live face was captured during the 8-second scan."
        );
        return;
      }

      if (mode === "register") {
        await finalizeRegistration(bestLiveBlob);
        return;
      }

      await finalizeVerification(bestLiveBlob);
    },
    [
      clearScanRuntime,
      finalizeRegistration,
      finalizeVerification,
      handleScanFailure,
      stopScanner,
    ]
  );

  const startScanner = useCallback(
    (mode: ScanMode) => {
      clearCompletionTimer();
      clearScanRuntime();
      scanRunIdRef.current += 1;
      setScanMode(mode);
      resetScanCapture();
      setErrorText(null);
      setStatusText(
        mode === "register" ? "Registering face..." : "Verifying face..."
      );
      setFlowStage("scan");
      setBusyState(null);
      setStreamEnabled(true);
    },
    [clearCompletionTimer, clearScanRuntime, resetScanCapture]
  );

  const refreshState = useCallback(async () => {
    setStatusLoading(true);
    setErrorText(null);
    resetAttemptCounter();
    clearStatusRetryTimer();

    try {
      const nextStatus = await fetchFacialVerificationStatus({ authToken });
      setReferenceStatus(nextStatus);
      resetScanCapture();

      if (!nextStatus.faceRuntimeReady) {
        setFlowStage("blocked");
        stopScanner();
        if (isRetryableFaceRuntimeReason(nextStatus.faceRuntimeReason)) {
          setStatusText(
            `${describeFaceRuntimeReason(
              nextStatus.faceRuntimeReason
            )} Retrying automatically.`
          );
          statusRetryTimerRef.current = window.setTimeout(() => {
            void refreshState();
          }, STATUS_RETRY_DELAY_MS);
          return;
        }
        setStatusText(describeFaceRuntimeReason(nextStatus.faceRuntimeReason));
        return;
      }

      if (!nextStatus.antiSpoofReady) {
        setFlowStage("blocked");
        setStatusText(describeAntiSpoofReason(nextStatus.antiSpoofReason));
        stopScanner();
        return;
      }

      if (!nextStatus.faceReferenceEnrolled) {
        setFlowStage("intro");
        setScanMode("register");
        setStatusText("No registered face in this account. Register first.");
        stopScanner();
        return;
      }

      startScanner("verify");
    } catch (error) {
      setFlowStage("blocked");
      setStatusText(toErrorDetail(error));
      stopScanner();
    } finally {
      setStatusLoading(false);
    }
  }, [
    authToken,
    clearStatusRetryTimer,
    resetAttemptCounter,
    resetScanCapture,
    startScanner,
    stopScanner,
  ]);

  useEffect(() => {
    void refreshState();
  }, [refreshState]);

  useEffect(
    () => () => {
      clearCompletionTimer();
      clearStatusRetryTimer();
      clearScanRuntime();
    },
    [clearCompletionTimer, clearScanRuntime, clearStatusRetryTimer]
  );

  useEffect(() => {
    if (
      flowStage !== "scan" ||
      !streamEnabled ||
      !cameraReady ||
      statusLoading ||
      busyState !== null ||
      !faceRuntimeReady ||
      !antiSpoofReady ||
      scanStartedAtRef.current !== null
    ) {
      return;
    }

    const runId = scanRunIdRef.current;
    const currentMode = scanMode;
    const startedAt = window.performance.now();
    scanStartedAtRef.current = startedAt;

    const tick = () => {
      if (
        scanRunIdRef.current !== runId ||
        scanStartedAtRef.current !== startedAt
      ) {
        return;
      }

      const elapsed = window.performance.now() - startedAt;
      setProgressPercent(Math.min(100, (elapsed / SCAN_DURATION_MS) * 100));

      if (elapsed < SCAN_DURATION_MS) {
        scanAnimationRef.current = window.requestAnimationFrame(tick);
      }
    };

    tick();
    scanTimeoutRef.current = window.setTimeout(() => {
      void finishTimedScan(runId, currentMode);
    }, SCAN_DURATION_MS);

    return () => {
      if (scanRunIdRef.current === runId) {
        clearScanRuntime();
      }
    };
  }, [
    faceRuntimeReady,
    antiSpoofReady,
    busyState,
    cameraReady,
    clearScanRuntime,
    finishTimedScan,
    flowStage,
    scanMode,
    statusLoading,
    streamEnabled,
  ]);

  const handleFrameError = (error: unknown) => {
    const apiError = error as FacialVerificationApiError | undefined;
    const detail = apiError?.detail || toErrorDetail(error);

    if (isMultipleFaceError(detail)) {
      scanCaptureRef.current.lastIssue = "One face only.";
      return;
    }

    if (isNoFaceError(detail)) {
      scanCaptureRef.current.lastIssue = "Face not found.";
      return;
    }

    if (detail.toLowerCase().includes("spoof")) {
      scanCaptureRef.current.lastIssue = "Spoof detected.";
      return;
    }

    if (detail.toLowerCase().includes("liveness model is not available")) {
      setFlowStage("blocked");
      stopScanner();
      setStatusText(detail);
      return;
    }

    if (
      detail.toLowerCase().includes("deepface retinaface requires") ||
      detail.toLowerCase().includes("deepface runtime is unavailable")
    ) {
      setFlowStage("blocked");
      stopScanner();
      setStatusText(detail);
      return;
    }

    scanCaptureRef.current.lastIssue = detail;
  };

  const handleFrame = async (blob: Blob) => {
    if (
      statusLoading ||
      busyState !== null ||
      !faceRuntimeReady ||
      !antiSpoofReady ||
      flowStage !== "scan"
    ) {
      return;
    }

    try {
      const liveness = await checkFacialLiveness({
        imageSource: blob,
        authToken,
      });

      if (liveness.label !== "Real" || liveness.score < MIN_LIVENESS_SCORE) {
        scanCaptureRef.current.lastIssue = "Spoof detected.";
        return;
      }

      setErrorText(null);
      if (liveness.score >= scanCaptureRef.current.bestLiveScore) {
        scanCaptureRef.current.bestLiveBlob = blob;
        scanCaptureRef.current.bestLiveScore = liveness.score;
        scanCaptureRef.current.lastIssue = null;
      }
    } catch (error) {
      handleFrameError(error);
    }
  };

  const handleNext = () => {
    if (flowStage === "intro") {
      startScanner("register");
      return;
    }

    if (flowStage === "ready_to_verify") {
      startScanner("verify");
    }
  };

  const handleRetry = () => {
    startScanner(scanMode);
  };

  const handleRegisterAgain = () => {
    clearCompletionTimer();
    resetAttemptCounter();
    setStatusText("No registered face in this account. Register first.");
    setFlowStage("intro");
    setScanMode("register");
    resetScanCapture();
    setErrorText(null);
    stopScanner();
  };

  const handleClearReference = async () => {
    setBusyState("delete");
    clearCompletionTimer();
    stopScanner();

    try {
      await clearFacialReferenceProfile({
        role,
        subjectId,
        authToken,
      });
      setReferenceStatus((currentStatus) =>
        currentStatus
          ? {
              ...currentStatus,
              faceReferenceEnrolled: false,
            }
          : currentStatus
      );
      setFlowStage("intro");
      setScanMode("register");
      setStatusText("No registered face in this account. Register first.");
      setErrorText(null);
      resetAttemptCounter();
      resetScanCapture();
    } catch (error) {
      setErrorText(toErrorDetail(error));
    } finally {
      setBusyState(null);
    }
  };

  return (
    <section className="face-flow-shell">
      <article className="face-flow-card">
        {flowStage === "intro" ? (
          <div className="face-flow-intro">
            <div className="face-flow-intro__icon">
              <FaFingerprint />
            </div>
            <p>{statusText}</p>
            <button
              type="button"
              className="verification-button verification-button--primary face-flow-button"
              onClick={handleNext}
              disabled={statusLoading || busyState !== null}
            >
              <FaArrowRight />
              Next
            </button>
          </div>
        ) : null}

        {flowStage === "scan" ? (
          <div className="face-flow-scanner">
            <div
              className="face-flow-ring"
              style={{
                ["--face-progress" as string]: `${progressPercent}%`,
              }}
            >
              <div className="face-flow-ring__inner">
                <CameraFeed
                  streamEnabled={streamEnabled}
                  scanEnabled={streamEnabled}
                  showControls={false}
                  circleMask
                  placeholderText=""
                  onFrame={handleFrame}
                  onCameraStateChange={(isOn) => {
                    setCameraReady(isOn);
                  }}
                  onScanError={(error) => {
                    if (busyState === null) {
                      stopScanner();
                      resetScanCapture();
                      setStatusText(toErrorDetail(error));
                      setErrorText(null);
                      setFlowStage("retry");
                    }
                  }}
                />
              </div>
            </div>

            <div className="face-flow-progress">
              <div className="face-flow-progress__value">
                {Math.round(progressPercent)}%
              </div>
              <div className="face-flow-progress__label">{scanLabel}</div>
              {maxAttempts !== null ? (
                <div className="face-flow-progress__meta">
                  Attempt {Math.min(failedAttempts + 1, maxAttempts)} of {maxAttempts}
                </div>
              ) : null}
            </div>

            {errorText ? (
              <div className="face-flow-feedback">{errorText}</div>
            ) : null}
          </div>
        ) : null}

        {flowStage === "retry" ? (
          <div className="face-flow-intro">
            <div className="face-flow-intro__icon face-flow-intro__icon--error">
              <FaShieldAlt />
            </div>
            <p>{statusText}</p>
            {attemptsRemaining !== null ? (
              <div className="face-flow-intro__meta">
                {attemptsRemaining} tries remaining
              </div>
            ) : null}
            <button
              type="button"
              className="verification-button verification-button--primary face-flow-button"
              onClick={handleRetry}
              disabled={busyState !== null}
            >
              <FaArrowRight />
              Try Again
            </button>
          </div>
        ) : null}

        {flowStage === "ready_to_verify" ? (
          <div className="face-flow-intro">
            <div className="face-flow-intro__icon face-flow-intro__icon--success">
              <FaCheckCircle />
            </div>
            <p>Face registered.</p>
            <button
              type="button"
              className="verification-button verification-button--primary face-flow-button"
              onClick={handleNext}
              disabled={busyState !== null}
            >
              <FaShieldAlt />
              Next
            </button>
          </div>
        ) : null}

        {flowStage === "complete" ? (
          <div className="face-flow-intro">
            <div className="face-flow-intro__icon face-flow-intro__icon--success">
              <FaCheckCircle />
            </div>
            <p>{statusText}</p>
          </div>
        ) : null}

        {flowStage === "blocked" ? (
          <div className="face-flow-intro">
            <div className="face-flow-intro__icon face-flow-intro__icon--error">
              <FaShieldAlt />
            </div>
            <p>{statusText}</p>
          </div>
        ) : null}
      </article>

      {allowManagementActions ? (
        <div className="face-flow-actions">
          {referenceEnrolled ? (
            <button
              type="button"
              className="verification-button verification-button--neutral face-flow-button"
              onClick={handleRegisterAgain}
              disabled={busyState !== null}
            >
              <FaFingerprint />
              Register Again
            </button>
          ) : null}

          {referenceEnrolled ? (
            <button
              type="button"
              className="verification-button verification-button--danger face-flow-button"
              onClick={() => void handleClearReference()}
              disabled={busyState !== null}
            >
              <FaTrashAlt />
              Clear Face
            </button>
          ) : null}
        </div>
      ) : null}

      <div className="face-flow-subject">{subjectLabel}</div>
    </section>
  );
};

export default PrivilegedFaceWorkspace;
