import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import EventLocationPicker from "@/components/events/EventLocationPicker.vue";
import {
  getCurrentPositionIfAvailable,
  getCurrentPositionOrThrow,
} from "@/services/devicePermissions.js";
import {
  resolveLocationLabel,
  searchLocationSuggestions,
} from "@/services/locationDisplay.js";

vi.mock("@/services/devicePermissions.js", () => ({
  getCurrentPositionIfAvailable: vi.fn(),
  getCurrentPositionOrThrow: vi.fn(),
}));

vi.mock("@/services/locationDisplay.js", () => ({
  formatCoordinateLocationLabel: ({ latitude, longitude }) => `${Number(latitude).toFixed(4)}, ${Number(longitude).toFixed(4)}`,
  resolveLocationLabel: vi.fn(),
  searchLocationSuggestions: vi.fn(),
}));

const mapControls = {
  lastClickHandler: null,
  invalidateSize: vi.fn(),
  remove: vi.fn(),
  setView: vi.fn(),
  fitBounds: vi.fn(),
  getZoom: vi.fn(() => 14),
  hasLayer: vi.fn(() => true),
  removeLayer: vi.fn(),
  on: vi.fn((event, handler) => {
    if (event === "click") mapControls.lastClickHandler = handler;
  }),
  off: vi.fn(),
};

const markerControls = {
  addTo: vi.fn(() => markerControls),
  on: vi.fn(),
  off: vi.fn(),
  setLatLng: vi.fn(),
  getLatLng: vi.fn(() => ({ lat: 8.1552, lng: 123.8421 })),
  remove: vi.fn(),
  dragging: {
    enable: vi.fn(),
    disable: vi.fn(),
  },
};

const circleControls = {
  addTo: vi.fn(() => circleControls),
  setLatLng: vi.fn(),
  setRadius: vi.fn(),
  setStyle: vi.fn(),
  getBounds: vi.fn(() => ({
    pad: vi.fn(() => "bounds"),
  })),
  remove: vi.fn(),
};

vi.mock("leaflet", () => ({
  default: {
    latLngBounds: vi.fn(() => "world-bounds"),
    map: vi.fn(() => mapControls),
    control: {
      zoom: vi.fn(() => ({
        addTo: vi.fn(),
      })),
    },
    tileLayer: vi.fn(() => ({
      addTo: vi.fn(),
    })),
    latLng: vi.fn((latitude, longitude) => ({ latitude, longitude, lat: latitude, lng: longitude })),
    marker: vi.fn(() => markerControls),
    circle: vi.fn(() => circleControls),
    divIcon: vi.fn((options) => options),
  },
}));

function mountPicker(props = {}) {
  return mount(EventLocationPicker, {
    props,
    attachTo: document.body,
  });
}

async function settleMountedPicker(wrapper) {
  await flushPromises();
  await wrapper.vm.$nextTick();
}

describe("EventLocationPicker", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    mapControls.lastClickHandler = null;
    getCurrentPositionIfAvailable.mockResolvedValue(null);
    getCurrentPositionOrThrow.mockResolvedValue({
      latitude: 8.1552,
      longitude: 123.8421,
      accuracy: 18,
    });
    resolveLocationLabel.mockResolvedValue("Resolved Location");
    searchLocationSuggestions.mockResolvedValue([]);
    globalThis.ResizeObserver = class {
      observe = vi.fn();
      disconnect = vi.fn();
    };
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("renders existing coordinates and allows clearing the pin", async () => {
    // This protects edit flows where an event already has a saved map pin.
    const wrapper = mountPicker({
      locationLabel: "Saved Venue",
      latitude: 8.1552,
      longitude: 123.8421,
      radiusM: 250,
    });
    await settleMountedPicker(wrapper);

    expect(wrapper.text()).toContain("8.155200");
    expect(wrapper.text()).toContain("123.842100");
    expect(wrapper.text()).toContain("250 m");

    await wrapper.get("button.event-location-picker__action:not(.event-location-picker__action--primary)").trigger("click");

    expect(wrapper.emitted("update:latitude")?.at(-1)).toEqual([""]);
    expect(wrapper.emitted("update:longitude")?.at(-1)).toEqual([""]);
    expect(wrapper.text()).toContain("Pin cleared.");
  });

  it("searches nearby locations and emits the selected suggestion", async () => {
    // This protects the typeahead path from search query through selected map coordinates.
    searchLocationSuggestions.mockResolvedValueOnce([
      {
        id: "place-1",
        label: "Library",
        secondaryLabel: "Main Campus",
        displayName: "Library, Main Campus",
        latitude: 8.155333,
        longitude: 123.842222,
      },
    ]);

    const wrapper = mountPicker();
    await settleMountedPicker(wrapper);

    await wrapper.get("input[name='event_location']").trigger("focus");
    await wrapper.get("input[name='event_location']").setValue("Library");
    await vi.advanceTimersByTimeAsync(230);
    await flushPromises();

    expect(searchLocationSuggestions).toHaveBeenCalledWith(
      expect.objectContaining({
        query: "Library",
        limit: 6,
      }),
    );
    await wrapper.get(".event-location-picker__suggestion").trigger("mousedown");
    await flushPromises();

    expect(wrapper.emitted("update:locationLabel")?.at(-1)).toEqual(["Library, Main Campus"]);
    expect(wrapper.emitted("update:latitude")?.at(-1)).toEqual([8.155333]);
    expect(wrapper.emitted("update:longitude")?.at(-1)).toEqual([123.842222]);
    expect(wrapper.text()).toContain("Location selected.");
  });

  it("shows a search error when the suggestion provider fails", async () => {
    // This protects the user-facing error shown when venue search cannot complete.
    searchLocationSuggestions.mockRejectedValueOnce(new Error("Search provider unavailable."));

    const wrapper = mountPicker();
    await settleMountedPicker(wrapper);

    await wrapper.get("input[name='event_location']").trigger("focus");
    await wrapper.get("input[name='event_location']").setValue("Gym");
    await vi.advanceTimersByTimeAsync(230);
    await flushPromises();

    expect(wrapper.text()).toContain("Search provider unavailable.");
  });

  it("uses current location and reverse-geocodes the emitted label", async () => {
    // This protects the Current button path used when users want the browser/device location.
    getCurrentPositionOrThrow.mockResolvedValueOnce({
      latitude: 8.155244,
      longitude: 123.842155,
      accuracy: 24,
    });
    resolveLocationLabel.mockResolvedValueOnce("Current Campus Gate");

    const wrapper = mountPicker();
    await settleMountedPicker(wrapper);

    await wrapper.get("button.event-location-picker__action--primary").trigger("click");
    await flushPromises();

    expect(getCurrentPositionOrThrow).toHaveBeenCalledWith(
      expect.objectContaining({ enableHighAccuracy: true }),
    );
    expect(wrapper.emitted("update:latitude")?.at(-1)).toEqual([8.155244]);
    expect(wrapper.emitted("update:longitude")?.at(-1)).toEqual([123.842155]);
    expect(wrapper.emitted("update:locationLabel")?.at(-1)).toEqual(["Current Campus Gate"]);
    expect(wrapper.text()).toContain("Current location selected");
  });

  it("reports current-location failures without emitting coordinates", async () => {
    // This protects denied/unavailable location errors from silently selecting a bad pin.
    getCurrentPositionOrThrow.mockRejectedValueOnce(new Error("Location access was denied."));

    const wrapper = mountPicker();
    await settleMountedPicker(wrapper);

    await wrapper.get("button.event-location-picker__action--primary").trigger("click");
    await flushPromises();

    expect(wrapper.emitted("update:latitude")).toBeUndefined();
    expect(wrapper.emitted("update:longitude")).toBeUndefined();
    expect(wrapper.text()).toContain("Location access was denied.");
  });

  it("disables text search, current location, and clearing while disabled", async () => {
    // This protects read-only event forms from changing map state.
    const wrapper = mountPicker({
      disabled: true,
      latitude: 8.1552,
      longitude: 123.8421,
    });
    await settleMountedPicker(wrapper);

    expect(wrapper.get("input[name='event_location']").attributes("disabled")).toBeDefined();
    for (const button of wrapper.findAll("button.event-location-picker__action")) {
      expect(button.attributes("disabled")).toBeDefined();
    }

    await wrapper.get("input[name='event_location']").trigger("focus");
    await vi.advanceTimersByTimeAsync(230);
    await flushPromises();
    expect(searchLocationSuggestions).not.toHaveBeenCalled();
  });
});
