import { useCallback, useEffect, useRef, useState } from "react";
import { FaCamera, FaExchangeAlt, FaStop } from "react-icons/fa";

export type CameraFeedStats = {
  requestsPerSecond: number;
  pageVisible: boolean;
  networkBackoffMs: number;
};

type CameraFeedProps = {
  streamEnabled?: boolean;
  scanEnabled: boolean;
  scanIntervalMs?: number;
  jpegQuality?: number;
  autoStart?: boolean;
  showControls?: boolean;
  circleMask?: boolean;
  placeholderText?: string;
  onFrame: (blob: Blob) => Promise<void>;
  onStatsChange?: (stats: CameraFeedStats) => void;
  onCameraStateChange?: (isOn: boolean) => void;
  onScanError?: (error: unknown) => void;
};

const humanCameraError = (error: unknown) => {
  if (error instanceof DOMException) {
    if (error.name === "NotAllowedError") {
      return "Camera permission was denied. Enable camera access in the browser and reload.";
    }
    if (error.name === "NotFoundError") {
      return "No camera device was found on this device.";
    }
    if (error.name === "NotReadableError") {
      return "Camera is already in use by another app or browser tab.";
    }
  }

  return error instanceof Error ? error.message : "Unable to access the camera.";
};

const isSecureCameraContext = () => {
  if (typeof window === "undefined") {
    return true;
  }

  if (window.isSecureContext) {
    return true;
  }

  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1";
};

const waitForVideoMetadata = (video: HTMLVideoElement) => {
  if (video.readyState >= HTMLMediaElement.HAVE_METADATA) {
    return Promise.resolve();
  }

  return new Promise<void>((resolve, reject) => {
    const onLoaded = () => {
      cleanup();
      resolve();
    };
    const onError = () => {
      cleanup();
      reject(new Error("Camera stream metadata failed to load."));
    };
    const cleanup = () => {
      video.removeEventListener("loadedmetadata", onLoaded);
      video.removeEventListener("error", onError);
    };

    video.addEventListener("loadedmetadata", onLoaded);
    video.addEventListener("error", onError);
  });
};

const computeBackoffDelay = (failureCount: number, baseDelayMs: number) =>
  Math.min(4000, baseDelayMs * Math.max(1, 2 ** Math.max(0, failureCount - 1)));

const captureFrameAsBlob = (
  video: HTMLVideoElement,
  canvas: HTMLCanvasElement,
  jpegQuality: number
) =>
  new Promise<Blob>((resolve, reject) => {
    const context = canvas.getContext("2d");
    if (!context) {
      reject(new Error("Failed to prepare the camera canvas."));
      return;
    }

    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error("Failed to capture a camera frame."));
          return;
        }
        resolve(blob);
      },
      "image/jpeg",
      jpegQuality
    );
  });

const CameraFeed = ({
  streamEnabled,
  scanEnabled,
  scanIntervalMs = 400,
  jpegQuality = 0.82,
  autoStart = true,
  showControls = true,
  circleMask = false,
  placeholderText = "Live camera is required for face registration and verification.",
  onFrame,
  onStatsChange,
  onCameraStateChange,
  onScanError,
}: CameraFeedProps) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const isProcessingRef = useRef(false);
  const isMountedRef = useRef(true);
  const networkFailuresRef = useRef(0);
  const requestTimesRef = useRef<number[]>([]);
  const onFrameRef = useRef(onFrame);
  const onStatsChangeRef = useRef(onStatsChange);
  const onCameraStateChangeRef = useRef(onCameraStateChange);
  const onScanErrorRef = useRef(onScanError);
  const facingModeRef = useRef<"user" | "environment">("user");
  const startRequestIdRef = useRef(0);
  const visibleRef = useRef(
    typeof document === "undefined" || document.visibilityState === "visible"
  );

  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"user" | "environment">("user");

  useEffect(() => {
    onFrameRef.current = onFrame;
  }, [onFrame]);

  useEffect(() => {
    onStatsChangeRef.current = onStatsChange;
  }, [onStatsChange]);

  useEffect(() => {
    onCameraStateChangeRef.current = onCameraStateChange;
  }, [onCameraStateChange]);

  useEffect(() => {
    onScanErrorRef.current = onScanError;
  }, [onScanError]);

  useEffect(() => {
    facingModeRef.current = facingMode;
  }, [facingMode]);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      startRequestIdRef.current += 1;
    };
  }, []);

  const emitStats = useCallback(
    (networkBackoffMs = 0) => {
      const now = Date.now();
      requestTimesRef.current = requestTimesRef.current.filter(
        (timestamp) => now - timestamp <= 1000
      );
      onStatsChangeRef.current?.({
        requestsPerSecond: requestTimesRef.current.length,
        pageVisible: visibleRef.current,
        networkBackoffMs,
      });
    },
    []
  );

  const stopCamera = useCallback(() => {
    startRequestIdRef.current += 1;

    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraOn(false);
    onCameraStateChangeRef.current?.(false);
  }, []);

  const startCamera = useCallback(
    async (
      requestedFacingMode: "user" | "environment" = facingModeRef.current
    ) => {
      setCameraError(null);
      stopCamera();

      const requestId = startRequestIdRef.current;

      const ensureActiveRequest = (stream?: MediaStream) => {
        if (
          !isMountedRef.current ||
          requestId !== startRequestIdRef.current
        ) {
          stream?.getTracks().forEach((track) => track.stop());
          return false;
        }
        return true;
      };

      try {
        if (!isSecureCameraContext()) {
          throw new Error(
            "Camera access requires HTTPS on mobile or remote devices. Use HTTPS or open the app from localhost."
          );
        }

        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error("This browser does not support live camera access.");
        }

        let stream: MediaStream;
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: { ideal: requestedFacingMode },
              width: { ideal: 1280 },
              height: { ideal: 720 },
            },
            audio: false,
          });
        } catch {
          stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false,
          });
        }

        if (!ensureActiveRequest(stream)) {
          return;
        }

        streamRef.current = stream;
        if (!videoRef.current) {
          stream.getTracks().forEach((track) => track.stop());
          throw new Error("Camera preview could not be initialized.");
        }

        videoRef.current.srcObject = stream;
        await waitForVideoMetadata(videoRef.current);
        if (!ensureActiveRequest(stream) || !videoRef.current) {
          if (videoRef.current) {
            videoRef.current.srcObject = null;
          }
          return;
        }

        await videoRef.current.play();
        if (!ensureActiveRequest(stream)) {
          if (videoRef.current) {
            videoRef.current.srcObject = null;
          }
          return;
        }

        setCameraOn(true);
        onCameraStateChangeRef.current?.(true);
      } catch (error) {
        if (!isMountedRef.current || requestId !== startRequestIdRef.current) {
          return;
        }

        setCameraOn(false);
        const message = humanCameraError(error);
        setCameraError(message);
        onScanErrorRef.current?.(new Error(message));
      }
    },
    [stopCamera]
  );

  const switchCamera = useCallback(() => {
    const nextFacingMode = facingMode === "user" ? "environment" : "user";
    setFacingMode(nextFacingMode);
    if (cameraOn) {
      void startCamera(nextFacingMode);
    }
  }, [cameraOn, facingMode, startCamera]);

  useEffect(() => {
    const shouldStream = streamEnabled ?? autoStart;
    if (shouldStream) {
      void startCamera();
    } else {
      stopCamera();
    }

    return () => {
      stopCamera();
    };
  }, [autoStart, startCamera, stopCamera, streamEnabled]);

  useEffect(() => {
    const onVisibilityChange = () => {
      visibleRef.current = document.visibilityState === "visible";
      emitStats();
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [emitStats]);

  useEffect(() => {
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    const schedule = (delayMs: number) => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
      timerRef.current = window.setTimeout(loop, delayMs);
    };

    const loop = async () => {
      if (!scanEnabled || !cameraOn || !visibleRef.current) {
        emitStats();
        schedule(scanIntervalMs);
        return;
      }

      if (isProcessingRef.current) {
        schedule(scanIntervalMs);
        return;
      }

      if (
        !videoRef.current ||
        !canvasRef.current ||
        videoRef.current.readyState < HTMLMediaElement.HAVE_CURRENT_DATA
      ) {
        schedule(scanIntervalMs);
        return;
      }

      isProcessingRef.current = true;
      let backoffMs = 0;

      try {
        const blob = await captureFrameAsBlob(
          videoRef.current,
          canvasRef.current,
          jpegQuality
        );
        requestTimesRef.current.push(Date.now());
        await onFrameRef.current(blob);
        networkFailuresRef.current = 0;
      } catch (error) {
        onScanErrorRef.current?.(error);
        networkFailuresRef.current += 1;
        backoffMs = computeBackoffDelay(
          networkFailuresRef.current,
          scanIntervalMs
        );
      } finally {
        isProcessingRef.current = false;
        emitStats(backoffMs);
      }

      schedule(scanIntervalMs + backoffMs);
    };

    schedule(scanIntervalMs);

    return () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [
    cameraOn,
    emitStats,
    jpegQuality,
    scanEnabled,
    scanIntervalMs,
  ]);

  return (
    <div className="camera-preview camera-preview--live">
      <div className={`camera-stage${circleMask ? " camera-stage--circle" : ""}`}>
        <video
          ref={videoRef}
          className={`camera-stage__video${
            cameraOn ? " camera-stage__video--active" : ""
          } camera-stage__video--mirror`}
          autoPlay
          muted
          playsInline
        />
        {!cameraOn ? (
          <div className="camera-stage--placeholder">
            <div>
              <FaCamera size={28} />
              {placeholderText ? (
                <p style={{ margin: "0.85rem 0 0" }}>{placeholderText}</p>
              ) : null}
            </div>
          </div>
        ) : (
          <>
            <div className="camera-stage__overlay" />
            {!circleMask ? (
              <div className="camera-stage__status">Camera ON</div>
            ) : null}
          </>
        )}
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>

      {showControls ? (
        <div className="camera-actions">
          {!cameraOn ? (
            <button
              type="button"
              className="verification-button verification-button--primary"
              onClick={() => void startCamera()}
            >
              <FaCamera />
              Start Camera
            </button>
          ) : (
            <button
              type="button"
              className="verification-button verification-button--danger"
              onClick={stopCamera}
            >
              <FaStop />
              Stop Camera
            </button>
          )}

          <button
            type="button"
            className="verification-button verification-button--neutral"
            onClick={switchCamera}
          >
            <FaExchangeAlt />
            Switch Camera
          </button>
        </div>
      ) : null}

      {cameraError ? (
        <div className="status-message status-message--error">
          <span>{cameraError}</span>
        </div>
      ) : null}
    </div>
  );
};

export default CameraFeed;
