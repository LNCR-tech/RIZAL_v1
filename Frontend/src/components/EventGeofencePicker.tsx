import { useEffect, useMemo, useState } from "react";
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

const DEFAULT_CENTER: LatLngExpression = [12.8797, 121.774];
const DEFAULT_ZOOM = 6;
const SELECTED_ZOOM = 16;

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
  invalidateKey,
}: {
  center: LatLngExpression;
  invalidateKey?: string | number | boolean;
}) => {
  const map = useMap();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      map.invalidateSize();
      map.setView(center);
    }, 100);

    return () => {
      window.clearTimeout(timer);
    };
  }, [center, invalidateKey, map]);

  return null;
};

const normalizeNumber = (value: string, fallback: number) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return parsed;
};

const EventGeofencePicker = ({
  value,
  onChange,
  invalidateKey,
}: EventGeofencePickerProps) => {
  const [mapCenter, setMapCenter] = useState<LatLngExpression>(DEFAULT_CENTER);
  const selectedCenter = useMemo<LatLngExpression | null>(() => {
    if (value.latitude == null || value.longitude == null) {
      return null;
    }
    return [value.latitude, value.longitude];
  }, [value.latitude, value.longitude]);

  useEffect(() => {
    if (selectedCenter) {
      setMapCenter(selectedCenter);
    }
  }, [selectedCenter]);

  useEffect(() => {
    if (selectedCenter) {
      return;
    }

    if (!navigator.geolocation) {
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setMapCenter([position.coords.latitude, position.coords.longitude]);
      },
      () => undefined,
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0,
      }
    );
  }, [selectedCenter]);

  const updateLocation = (latitude: number, longitude: number) => {
    onChange({
      ...value,
      latitude: Number(latitude.toFixed(6)),
      longitude: Number(longitude.toFixed(6)),
      required: true,
    });
    setMapCenter([latitude, longitude]);
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

      <div className="event-geofence-picker__map-frame">
        <MapContainer
          center={mapCenter}
          zoom={selectedCenter ? SELECTED_ZOOM : DEFAULT_ZOOM}
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
            invalidateKey={invalidateKey}
          />
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
