import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: () => false,
  },
}));

import {
  resolveAbsoluteApiBaseUrl,
  resolveApiBaseUrl,
  resolveImportApiTimeoutMs,
} from "@/services/backendBaseUrl.js";
import {
  resolveAbsoluteAssistantBaseUrl,
  resolveAssistantBaseUrl,
} from "@/services/assistantBaseUrl.js";

describe("frontend URL resolution", () => {
  beforeEach(() => {
    delete window.__AURA_RUNTIME_CONFIG__;
    // These fallback tests must simulate a build with no configured Vite env
    // override, even if local .env files define localhost development URLs.
    vi.stubEnv("VITE_API_BASE_URL", "");
    vi.stubEnv("VITE_ASSISTANT_BASE_URL", "");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("falls back to the proxied backend path for web builds", () => {
    expect(resolveApiBaseUrl()).toBe("/__backend__");
  });

  it("normalizes runtime backend origins that still include /api", () => {
    window.__AURA_RUNTIME_CONFIG__ = {
      backendBaseUrl: "https://api.example.com/api/",
    };

    expect(resolveApiBaseUrl()).toBe("https://api.example.com");
  });

  it("converts relative API paths into absolute browser URLs", () => {
    window.__AURA_RUNTIME_CONFIG__ = {
      apiBaseUrl: "/custom-api/",
    };

    const resolvedUrl = new URL(resolveAbsoluteApiBaseUrl());
    expect(resolvedUrl.pathname).toBe("/custom-api");
  });

  it("keeps import timeouts at or above the import fallback minimum", () => {
    window.__AURA_RUNTIME_CONFIG__ = {
      importApiTimeoutMs: 5000,
    };

    expect(resolveImportApiTimeoutMs()).toBe(60000);
  });

  it("falls back to the proxied assistant path when no override exists", () => {
    expect(resolveAssistantBaseUrl()).toBe("/__assistant__");
  });

  it("converts relative assistant paths into absolute browser URLs", () => {
    window.__AURA_RUNTIME_CONFIG__ = {
      assistantBaseUrl: "/assistant-api/",
    };

    const resolvedUrl = new URL(resolveAbsoluteAssistantBaseUrl());
    expect(resolvedUrl.pathname).toBe("/assistant-api");
  });
});
