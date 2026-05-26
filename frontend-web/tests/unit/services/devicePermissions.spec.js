import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: () => false,
  },
}));

function installSecureBrowserEnvironment(extraNavigator = {}) {
  Object.defineProperty(window, "isSecureContext", {
    value: true,
    configurable: true,
  });
  Object.defineProperty(globalThis, "navigator", {
    value: {
      ...globalThis.navigator,
      ...extraNavigator,
    },
    configurable: true,
  });
}

async function loadDevicePermissions() {
  vi.resetModules();
  return import("@/services/devicePermissions.js");
}

describe("device permission helpers", () => {
  beforeEach(() => {
    vi.useRealTimers();
    installSecureBrowserEnvironment();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("requests web camera access and stops acquired tracks", async () => {
    // This protects the happy path used before camera-based attendance flows.
    const stop = vi.fn();
    installSecureBrowserEnvironment({
      mediaDevices: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: () => [{ stop }],
        }),
      },
    });

    const { requestCameraPermission } = await loadDevicePermissions();
    await expect(requestCameraPermission()).resolves.toEqual({
      granted: true,
      denied: false,
      message: "",
    });
    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({ video: true });
    expect(stop).toHaveBeenCalledTimes(1);
  });

  it("returns a clear denial message when the browser blocks camera access", async () => {
    // This protects the UI message shown when users deny camera permission.
    installSecureBrowserEnvironment({
      mediaDevices: {
        getUserMedia: vi.fn().mockRejectedValue(
          Object.assign(new Error("blocked"), { name: "NotAllowedError" }),
        ),
      },
    });

    const { requestCameraPermission } = await loadDevicePermissions();
    await expect(requestCameraPermission()).resolves.toMatchObject({
      granted: false,
      denied: true,
      message: "Camera access was denied. Please allow camera access in your browser settings.",
    });
  });

  it("returns granted immediately when geolocation permission is already granted", async () => {
    // This protects flows that should not prompt again after the browser already granted location.
    installSecureBrowserEnvironment({
      geolocation: { getCurrentPosition: vi.fn() },
      permissions: {
        query: vi.fn().mockResolvedValue({ state: "granted" }),
      },
    });

    const { requestLocationPermission } = await loadDevicePermissions();
    await expect(requestLocationPermission()).resolves.toEqual({
      granted: true,
      denied: false,
      message: "",
    });
    expect(navigator.geolocation.getCurrentPosition).not.toHaveBeenCalled();
  });

  it("returns a clear denial message when geolocation permission is denied", async () => {
    // This protects attendance/location flows from continuing after browser-level denial.
    installSecureBrowserEnvironment({
      geolocation: { getCurrentPosition: vi.fn() },
      permissions: {
        query: vi.fn().mockResolvedValue({ state: "denied" }),
      },
    });

    const { requestLocationPermission } = await loadDevicePermissions();
    await expect(requestLocationPermission()).resolves.toEqual({
      granted: false,
      denied: true,
      message: "Location access was denied. Please allow location access in your browser settings.",
    });
  });

  it("normalizes browser geolocation coordinates when position lookup succeeds", async () => {
    // This protects the coordinate payload consumed by map pins and attendance scans.
    installSecureBrowserEnvironment({
      geolocation: {
        getCurrentPosition: vi.fn((resolve) => {
          resolve({
            coords: {
              latitude: 8.1552,
              longitude: 123.8421,
              accuracy: 21,
            },
          });
        }),
      },
      permissions: {
        query: vi.fn().mockResolvedValue({ state: "prompt" }),
      },
    });

    const { getCurrentPositionOrThrow } = await loadDevicePermissions();
    await expect(getCurrentPositionOrThrow({ maximumAge: 0 })).resolves.toMatchObject({
      latitude: 8.1552,
      longitude: 123.8421,
      accuracy: 21,
    });
  });

  it("throws a helpful message when the browser lacks geolocation support", async () => {
    // This protects older/locked-down browsers from failing with a vague exception.
    installSecureBrowserEnvironment({
      geolocation: undefined,
      permissions: {
        query: vi.fn().mockResolvedValue({ state: "prompt" }),
      },
    });

    const { getCurrentPositionOrThrow } = await loadDevicePermissions();
    await expect(getCurrentPositionOrThrow()).rejects.toThrow(
      "Geolocation is not supported by your browser.",
    );
  });

  it("rejects precise location when accuracy never reaches the accepted threshold", async () => {
    // This protects high-accuracy attendance scans from accepting approximate browser locations.
    vi.useFakeTimers();
    installSecureBrowserEnvironment({
      geolocation: {
        clearWatch: vi.fn(),
        watchPosition: vi.fn((success) => {
          success({
            coords: {
              latitude: 8.1552,
              longitude: 123.8421,
              accuracy: 6000,
            },
          });
          return 91;
        }),
      },
      permissions: {
        query: vi.fn().mockResolvedValue({ state: "prompt" }),
      },
    });

    const { getCurrentPositionWithinAccuracyOrThrow } = await loadDevicePermissions();
    const result = getCurrentPositionWithinAccuracyOrThrow({
      desiredAccuracy: 30,
      timeout: 100,
    });
    const assertion = expect(result).rejects.toThrow(
      "The device is only providing an approximate location right now.",
    );
    await vi.advanceTimersByTimeAsync(18_100);

    await assertion;
    expect(navigator.geolocation.clearWatch).toHaveBeenCalledWith(91);
  });
});
