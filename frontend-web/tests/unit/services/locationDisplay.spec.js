import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  formatCoordinateLocationLabel,
  formatVenueDistance,
  measureDistanceMeters,
  resolveLocationLabel,
  searchLocationSuggestions,
} from "@/services/locationDisplay.js";

describe("location display helpers", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_REVERSE_GEOCODE_URL", "https://geo.test/reverse");
    vi.stubEnv("VITE_FORWARD_GEOCODE_URL", "https://geo.test/search");
    vi.stubEnv("VITE_LOCATION_SEARCH_COUNTRY_CODE", "ph");
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("formats valid coordinates and reports invalid coordinates clearly", () => {
    // This protects the fallback label shown when reverse geocoding is unavailable.
    expect(formatCoordinateLocationLabel({ latitude: 8.155234, longitude: 123.842145 })).toBe(
      "8.1552, 123.8421",
    );
    expect(formatCoordinateLocationLabel({ latitude: "bad", longitude: 123.842145 })).toBe(
      "Current location unavailable",
    );
  });

  it("uses a preferred label before making a reverse-geocode request", async () => {
    // This protects manual/event-provided location labels from being overwritten by the network.
    await expect(
      resolveLocationLabel({
        latitude: 8.155234,
        longitude: 123.842145,
        preferredLabel: "Main Gate",
      }),
    ).resolves.toBe("Main Gate");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("reverse-geocodes a readable city and region label", async () => {
    // This protects the short human-readable location label used by maps and event cards.
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        address: {
          city: "Oroquieta City",
          state: "Northern Mindanao",
          country: "Philippines",
        },
      }),
    });

    await expect(
      resolveLocationLabel({ latitude: 8.155235, longitude: 123.842146 }),
    ).resolves.toBe("Oroquieta City, Northern Mindanao");

    const requestedUrl = new URL(fetch.mock.calls[0][0]);
    expect(requestedUrl.searchParams.get("lat")).toBe("8.155235");
    expect(requestedUrl.searchParams.get("lon")).toBe("123.842146");
    expect(fetch.mock.calls[0][1].headers.Accept).toBe("application/json");
  });

  it("rejects failed reverse-geocode responses with a user-facing error", async () => {
    // This protects the error path used when the location provider is down.
    fetch.mockResolvedValueOnce({ ok: false, json: async () => ({}) });

    await expect(
      resolveLocationLabel({ latitude: 8.166236, longitude: 123.853147 }),
    ).rejects.toThrow("Unable to resolve the current location label.");
  });

  it("searches, labels, filters, and sorts nearby location suggestions", async () => {
    // This protects search suggestions from returning invalid entries or distant outliers.
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          place_id: 1,
          lat: "8.1553",
          lon: "123.8422",
          display_name: "Library, Test University, Philippines",
          address: {
            amenity: "Library",
            city: "Oroquieta City",
            state: "Northern Mindanao",
          },
        },
        {
          place_id: 2,
          lat: "9.5",
          lon: "125.0",
          display_name: "Far Campus, Philippines",
          address: { amenity: "Far Campus" },
        },
        {
          place_id: 3,
          lat: "not-a-number",
          lon: "123.8422",
          display_name: "Invalid",
        },
      ],
    });

    const suggestions = await searchLocationSuggestions({
      query: "library",
      near: { latitude: 8.1552, longitude: 123.8421 },
      radiusMeters: 1000,
      limit: 9,
    });

    expect(suggestions).toHaveLength(1);
    expect(suggestions[0]).toMatchObject({
      id: "1",
      label: "Library",
      secondaryLabel: "Oroquieta City, Northern Mindanao",
      latitude: 8.1553,
      longitude: 123.8422,
    });

    const requestedUrl = new URL(fetch.mock.calls[0][0]);
    expect(requestedUrl.searchParams.get("q")).toBe("library");
    expect(requestedUrl.searchParams.get("limit")).toBe("8");
    expect(requestedUrl.searchParams.get("countrycodes")).toBe("ph");
    expect(requestedUrl.searchParams.get("bounded")).toBe("1");
  });

  it("returns an empty suggestion list for empty queries or disabled endpoints", async () => {
    // This protects the search box from unnecessary network calls.
    await expect(searchLocationSuggestions({ query: "   " })).resolves.toEqual([]);
    vi.stubEnv("VITE_FORWARD_GEOCODE_URL", " ");
    await expect(searchLocationSuggestions({ query: "library" })).resolves.toEqual([]);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("measures and formats venue distance labels", () => {
    // This protects the distance text shown beside suggested venue matches.
    const distance = measureDistanceMeters(
      { latitude: 8.1552, longitude: 123.8421 },
      { latitude: 8.1552, longitude: 123.8511 },
    );

    expect(distance).toBeGreaterThan(900);
    expect(formatVenueDistance(36.4)).toBe("36 m to venue");
    expect(formatVenueDistance(1530)).toBe("1.5 km to venue");
    expect(formatVenueDistance(-1)).toBe("");
  });
});
