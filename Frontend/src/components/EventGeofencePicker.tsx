import { useEffect, useMemo, useRef, useState } from "react";
import {
  Circle,
  CircleMarker,
  MapContainer,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import type { LatLngExpression } from "leaflet";
import { FaCrosshairs, FaMapMarkerAlt, FaTrashAlt } from "react-icons/fa";
import "leaflet/dist/leaflet.css";
import "../css/EventGeofencePicker.css";

export interface EventGeofenceValue {
  latitude: number | null;
  longitude: number | null;
  radiusM: number;
  maxAccuracyM: number;
  required: boolean;
}

interface EventGeofencePickerProps {
  value: EventGeofenceValue;
  onChange: (nextValue: EventGeofenceValue) => void;
  invalidateKey?: string | number | boolean;
}

type CoordinatePair = [number, number];
type SearchScope = "nearby" | "fallback";

const DEFAULT_CENTER: CoordinatePair = [12.8797, 121.774];
const DEFAULT_ZOOM = 6;
const CURRENT_LOCATION_ZOOM = 17;
const SELECTED_ZOOM = 16;
const SEARCH_RESULT_LIMIT = 5;
const SEARCH_DEBOUNCE_MS = 450;
const SEARCH_MIN_CHARACTERS = 2;
const NEARBY_SEARCH_RADIUS_KM = 15;

interface LocationSearchResult {
  display_name: string;
  lat: string;
  lon: string;
  place_id: number;
  distanceKm?: number | null;
}

const MapClickHandler = ({
  onSelect,
}: {
  onSelect: (latitude: number, longitude: number) => void;
}) => {
  useMapEvents({
    click(event) {
      onSelect(event.latlng.lat, event.latlng.lng);
    },
  });

  return null;
};

const MapViewportController = ({
  center,
  zoom,
  invalidateKey,
}: {
  center: LatLngExpression;
  zoom: number;
  invalidateKey?: string | number | boolean;
}) => {
  const map = useMap();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      map.invalidateSize();
      map.setView(center, zoom);
    }, 100);

    return () => {
      window.clearTimeout(timer);
    };
  }, [center, invalidateKey, map, zoom]);

  return null;
};

const normalizeNumber = (value: string, fallback: number) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return parsed;
};

const clampLatitude = (value: number) => Math.max(-90, Math.min(90, value));

const clampLongitude = (value: number) => Math.max(-180, Math.min(180, value));

const buildNearbyViewbox = ([latitude, longitude]: CoordinatePair) => {
  const latitudeDelta = NEARBY_SEARCH_RADIUS_KM / 111.32;
  const latitudeRadians = (latitude * Math.PI) / 180;
  const longitudeScale = Math.max(Math.abs(Math.cos(latitudeRadians)), 0.2);
  const longitudeDelta = NEARBY_SEARCH_RADIUS_KM / (111.32 * longitudeScale);

  const west = clampLongitude(longitude - longitudeDelta);
  const east = clampLongitude(longitude + longitudeDelta);
  const north = clampLatitude(latitude + latitudeDelta);
  const south = clampLatitude(latitude - latitudeDelta);

  return `${west},${north},${east},${south}`;
};

const toRadians = (value: number) => (value * Math.PI) / 180;

const getDistanceKm = ([originLatitude, originLongitude]: CoordinatePair, destination: CoordinatePair) => {
  const [destinationLatitude, destinationLongitude] = destination;
  const earthRadiusKm = 6371;
  const latitudeDelta = toRadians(destinationLatitude - originLatitude);
  const longitudeDelta = toRadians(destinationLongitude - originLongitude);
  const originLatitudeRadians = toRadians(originLatitude);
  const destinationLatitudeRadians = toRadians(destinationLatitude);

  const a =
    Math.sin(latitudeDelta / 2) * Math.sin(latitudeDelta / 2) +
    Math.cos(originLatitudeRadians) *
      Math.cos(destinationLatitudeRadians) *
      Math.sin(longitudeDelta / 2) *
      Math.sin(longitudeDelta / 2);

  return 2 * earthRadiusKm * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

const withDistance = (
  results: LocationSearchResult[],
  referencePoint: CoordinatePair | null
) => {
  if (!referencePoint) {
    return results;
  }

  return [...results]
    .map((result) => ({
      ...result,
      distanceKm: getDistanceKm(referencePoint, [Number(result.lat), Number(result.lon)]),
    }))
    .sort((left, right) => (left.distanceKm ?? Number.MAX_SAFE_INTEGER) - (right.distanceKm ?? Number.MAX_SAFE_INTEGER));
};

const formatDistanceLabel = (distanceKm: number | null | undefined) => {
  if (distanceKm == null || !Number.isFinite(distanceKm)) {
    return null;
  }

  if (distanceKm < 1) {
    return `${Math.round(distanceKm * 1000)} m away`;
  }

  return `${distanceKm < 10 ? distanceKm.toFixed(1) : distanceKm.toFixed(0)} km away`;
};

const areCoordinatesEqual = (left: CoordinatePair, right: CoordinatePair) =>
  left[0] === right[0] && left[1] === right[1];

const MapViewportTracker = ({
  onViewportChange,
}: {
  onViewportChange: (center: CoordinatePair, zoom: number) => void;
}) => {
  const map = useMapEvents({
    moveend() {
      const center = map.getCenter();
      onViewportChange(
        [Number(center.lat.toFixed(6)), Number(center.lng.toFixed(6))],
        map.getZoom()
      );
    },
  });

  return null;
};

const EventGeofencePicker = ({
  value,
  onChange,
  invalidateKey,
}: EventGeofencePickerProps) => {
  const [mapCenter, setMapCenter] = useState<CoordinatePair>(DEFAULT_CENTER);
  const [mapZoom, setMapZoom] = useState(DEFAULT_ZOOM);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<LocationSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchScope, setSearchScope] = useState<SearchScope | null>(null);
  const autoLocationAppliedRef = useRef(false);
  const suppressNextAutoSearchRef = useRef(false);
  const selectedCenter = useMemo<CoordinatePair | null>(() => {
    if (value.latitude == null || value.longitude == null) {
      return null;
    }
    return [value.latitude, value.longitude];
  }, [value.latitude, value.longitude]);
  const nearbyReferencePoint = selectedCenter ?? mapCenter;

  const updateViewport = (center: CoordinatePair, zoom: number) => {
    setMapCenter((current) => (areCoordinatesEqual(current, center) ? current : center));
    setMapZoom((current) => (current === zoom ? current : zoom));
  };

  useEffect(() => {
    if (selectedCenter) {
      updateViewport(selectedCenter, SELECTED_ZOOM);
    }
  }, [selectedCenter]);

  useEffect(() => {
    if (selectedCenter || autoLocationAppliedRef.current) {
      return;
    }

    if (!navigator.geolocation) {
      return;
    }

    autoLocationAppliedRef.current = true;

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = Number(position.coords.latitude.toFixed(6));
        const longitude = Number(position.coords.longitude.toFixed(6));
        updateViewport([latitude, longitude], CURRENT_LOCATION_ZOOM);
      },
      () => undefined,
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 0,
      }
    );
  }, [selectedCenter]);

  const updateLocation = (latitude: number, longitude: number) => {
    onChange({
      ...value,
      latitude: Number(latitude.toFixed(6)),
      longitude: Number(longitude.toFixed(6)),
    });
    updateViewport([latitude, longitude], SELECTED_ZOOM);
  };

  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        updateLocation(position.coords.latitude, position.coords.longitude);
      },
      () => undefined,
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 0,
      }
    );
  };

  const handleClear = () => {
    onChange({
      ...value,
      latitude: null,
      longitude: null,
    });
  };

  useEffect(() => {
    if (suppressNextAutoSearchRef.current) {
      suppressNextAutoSearchRef.current = false;
      setDebouncedSearchTerm("");
      return;
    }

    const query = searchTerm.trim();
    if (!query) {
      setDebouncedSearchTerm("");
      setSearchResults([]);
      setSearchError(null);
      setSearchScope(null);
      setSearching(false);
      return;
    }

    if (query.length < SEARCH_MIN_CHARACTERS) {
      setDebouncedSearchTerm("");
      setSearchResults([]);
      setSearchError(null);
      setSearchScope(null);
      setSearching(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setDebouncedSearchTerm(query);
    }, SEARCH_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timer);
    };
  }, [searchTerm]);

  useEffect(() => {
    if (!debouncedSearchTerm) {
      return;
    }

    const controller = new AbortController();

    const searchLocations = async () => {
      const runSearch = async (restrictToNearby: boolean) => {
        const params = new URLSearchParams({
          format: "jsonv2",
          q: debouncedSearchTerm,
          limit: `${SEARCH_RESULT_LIMIT}`,
          addressdetails: "1",
        });

        params.set("viewbox", buildNearbyViewbox(nearbyReferencePoint));
        if (restrictToNearby) {
          params.set("bounded", "1");
        }

        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?${params.toString()}`,
          {
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          throw new Error("Location search is temporarily unavailable.");
        }

        return withDistance(
          (await response.json()) as LocationSearchResult[],
          nearbyReferencePoint
        );
      };

      try {
        setSearching(true);
        setSearchError(null);

        const nearbyResults = await runSearch(true);
        if (controller.signal.aborted) {
          return;
        }

        if (nearbyResults.length > 0) {
          setSearchResults(nearbyResults);
          setSearchScope("nearby");
          return;
        }

        const fallbackResults = await runSearch(false);
        if (controller.signal.aborted) {
          return;
        }

        setSearchResults(fallbackResults);
        setSearchScope(fallbackResults.length > 0 ? "fallback" : null);
        if (fallbackResults.length === 0) {
          setSearchError("No matching locations were found. Try a more specific search.");
        }
      } catch (searchRequestError) {
        if (controller.signal.aborted) {
          return;
        }

        setSearchResults([]);
        setSearchScope(null);
        setSearchError(
          searchRequestError instanceof Error
            ? searchRequestError.message
            : "Failed to search for that location."
        );
      } finally {
        if (!controller.signal.aborted) {
          setSearching(false);
        }
      }
    };

    void searchLocations();

    return () => {
      controller.abort();
    };
  }, [debouncedSearchTerm, nearbyReferencePoint]);

  const searchMeta =
    searchTerm.trim().length < SEARCH_MIN_CHARACTERS
      ? `Type at least ${SEARCH_MIN_CHARACTERS} characters to search nearby places.`
      : searching
        ? "Searching nearby places..."
        : searchScope === "nearby"
          ? "Showing the closest matches near your current pin or map view."
          : searchScope === "fallback"
            ? "No close nearby match was found, so wider results are shown."
            : "Search nearby places or addresses.";

  return (
    <section className="event-geofence-picker">
      <div className="event-geofence-picker__toolbar">
        <div>
          <h3>Event Location Verification</h3>
          <p>Click the map to mark the event venue and set the allowed check-in radius.</p>
        </div>
        <div className="event-geofence-picker__actions">
          <button
            type="button"
            className="event-geofence-picker__button"
            onClick={handleUseCurrentLocation}
          >
            <FaCrosshairs />
            Use Current Location
          </button>
          <button
            type="button"
            className="event-geofence-picker__button event-geofence-picker__button--danger"
            onClick={handleClear}
          >
            <FaTrashAlt />
            Clear
          </button>
        </div>
      </div>

      <div className="event-geofence-picker__search">
        <div className="event-geofence-picker__search-shell">
          <input
            type="text"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search nearby places or addresses"
          />
          {searchTerm ? (
            <button
              type="button"
              className="event-geofence-picker__search-clear"
              onClick={() => {
                suppressNextAutoSearchRef.current = true;
                setSearchTerm("");
                setDebouncedSearchTerm("");
                setSearchResults([]);
                setSearchError(null);
                setSearchScope(null);
                setSearching(false);
              }}
            >
              Clear
            </button>
          ) : null}
        </div>
        <div className="event-geofence-picker__search-meta" aria-live="polite">
          {searchMeta}
        </div>
      </div>

      {searchError ? <div className="event-geofence-picker__message">{searchError}</div> : null}
      {searchResults.length > 0 ? (
        <div className="event-geofence-picker__results" role="list">
          {searchResults.map((result) => (
            <button
              key={result.place_id}
              type="button"
              className="event-geofence-picker__result"
              onClick={() => {
                updateLocation(Number(result.lat), Number(result.lon));
                suppressNextAutoSearchRef.current = true;
                setSearchTerm(result.display_name);
                setDebouncedSearchTerm("");
                setSearchResults([]);
                setSearchError(null);
                setSearchScope(null);
              }}
            >
              <span className="event-geofence-picker__result-title">
                {result.display_name}
              </span>
              <span className="event-geofence-picker__result-meta">
                {searchScope === "nearby" ? (
                  <span className="event-geofence-picker__result-tag">Nearby match</span>
                ) : null}
                {formatDistanceLabel(result.distanceKm) ? (
                  <span>{formatDistanceLabel(result.distanceKm)}</span>
                ) : null}
              </span>
            </button>
          ))}
        </div>
      ) : null}

      <div className="event-geofence-picker__map-frame">
        <MapContainer
          center={mapCenter}
          zoom={selectedCenter ? SELECTED_ZOOM : mapZoom}
          scrollWheelZoom
          className="event-geofence-picker__map"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onSelect={updateLocation} />
          <MapViewportController
            center={selectedCenter ?? mapCenter}
            zoom={selectedCenter ? SELECTED_ZOOM : mapZoom}
            invalidateKey={invalidateKey}
          />
          <MapViewportTracker onViewportChange={updateViewport} />
          {selectedCenter ? (
            <>
              <Circle
                center={selectedCenter}
                radius={Math.max(1, value.radiusM)}
                pathOptions={{
                  color: "#162f65",
                  fillColor: "#2c5f9e",
                  fillOpacity: 0.16,
                  weight: 2,
                }}
              />
              <CircleMarker
                center={selectedCenter}
                radius={8}
                pathOptions={{
                  color: "#ffffff",
                  fillColor: "#d9443c",
                  fillOpacity: 1,
                  weight: 3,
                }}
              />
            </>
          ) : null}
        </MapContainer>
        {!selectedCenter ? (
          <div className="event-geofence-picker__hint">
            <FaMapMarkerAlt />
            <span>Select the event venue on the map.</span>
          </div>
        ) : null}
      </div>

      <div className="event-geofence-picker__grid">
        <label className="event-geofence-picker__field">
          <span>Latitude</span>
          <input
            type="number"
            step="0.000001"
            value={value.latitude ?? ""}
            onChange={(event) =>
              onChange({
                ...value,
                latitude:
                  event.target.value === "" ? null : Number(event.target.value),
              })
            }
            placeholder="Pick a point on the map"
          />
        </label>

        <label className="event-geofence-picker__field">
          <span>Longitude</span>
          <input
            type="number"
            step="0.000001"
            value={value.longitude ?? ""}
            onChange={(event) =>
              onChange({
                ...value,
                longitude:
                  event.target.value === "" ? null : Number(event.target.value),
              })
            }
            placeholder="Pick a point on the map"
          />
        </label>

        <label className="event-geofence-picker__field">
          <span>Allowed Radius (meters)</span>
          <input
            type="number"
            min="1"
            max="5000"
            value={value.radiusM}
            onChange={(event) =>
              onChange({
                ...value,
                radiusM: normalizeNumber(event.target.value, 100),
              })
            }
          />
        </label>

        <label className="event-geofence-picker__field">
          <span>Max GPS Accuracy (meters)</span>
          <input
            type="number"
            min="1"
            max="1000"
            value={value.maxAccuracyM}
            onChange={(event) =>
              onChange({
                ...value,
                maxAccuracyM: normalizeNumber(event.target.value, 50),
              })
            }
          />
        </label>
      </div>

      <label className="event-geofence-picker__toggle">
        <input
          type="checkbox"
          checked={value.required}
          onChange={(event) =>
            onChange({
              ...value,
              required: event.target.checked,
            })
          }
        />
        <span>Require students to be inside this geofence when signing in.</span>
      </label>
    </section>
  );
};

export default EventGeofencePicker;
