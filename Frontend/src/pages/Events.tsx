import { FormEvent, useCallback, useDeferredValue, useEffect, useMemo, useState } from "react";
import Modal from "react-modal";
import { FaEdit, FaFilter, FaPlus, FaSearch, FaTrashAlt } from "react-icons/fa";
import { Link } from "react-router-dom";

import {
  fetchGovernanceEventDefaults,
  fetchMyGovernanceAccess,
  GovernanceEventDefaults,
  updateGovernanceEventDefaults,
} from "../api/governanceHierarchyApi";
import { NavbarAdmin } from "../components/NavbarAdmin";
import EventGeofencePicker from "../components/EventGeofencePicker";
import NavbarSchoolIT from "../components/NavbarSchoolIT";
import SsgFeatureShell from "../components/SsgFeatureShell";
import {
  createEvent,
  type CreateEventPayload,
  deleteEvent,
  EventStatus,
  fetchAllEvents,
  GovernanceContext,
  type Event as EventRecord,
  updateEvent,
  type UpdateEventPayload,
  updateEventStatus,
} from "../api/eventsApi";
import {
  fetchSchoolSettings,
  type SchoolSettings,
  updateSchoolSettings,
} from "../api/schoolSettingsApi";
import "../css/Events.css";
import "../css/GovernanceHierarchyManagement.css";
import { formatManilaDateTime, parseEventDateTime } from "../utils/eventAttendanceWindow";
import {
  type EventDefaultSettings,
  FALLBACK_EVENT_DEFAULT_SETTINGS,
  getGovernanceEventDefaultSettings,
  getSchoolEventDefaultSettings,
} from "../utils/eventDefaultSettings";
import { getGovernanceEventDetailsPath } from "../utils/governanceEventPaths";
import { formatEventDepartments, formatEventPrograms } from "../utils/eventScopeLabels";

interface EventsProps {
  role: string;
}

interface EventDraftState {
  name: string;
  location: string;
  start_datetime: string;
  end_datetime: string;
  status: EventStatus;
  early_check_in_minutes: string;
  late_threshold_minutes: string;
  sign_out_grace_minutes: string;
  geo_required: boolean;
  geo_latitude: string;
  geo_longitude: string;
  geo_radius_m: string;
  geo_max_accuracy_m: string;
}

interface EventDefaultsDraftState {
  early_check_in_minutes: string;
  late_threshold_minutes: string;
  sign_out_grace_minutes: string;
}

interface PendingStatusConfirmationState {
  eventRecord: EventRecord;
  nextStatus: EventStatus;
}

interface PendingEventSaveState {
  eventName: string;
  payload: CreateEventPayload | UpdateEventPayload;
}

Modal.setAppElement("#root");

const toDateTimeLocalValue = (date: Date) => {
  const pad = (value: number) => `${value}`.padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
};

const getDefaultDraft = (
  defaults: EventDefaultSettings = FALLBACK_EVENT_DEFAULT_SETTINGS
): EventDraftState => {
  const start = new Date();
  start.setSeconds(0, 0);
  start.setMinutes(0);
  start.setHours(start.getHours() + 1);

  const end = new Date(start);
  end.setHours(end.getHours() + 2);

  return {
    name: "",
    location: "",
    start_datetime: toDateTimeLocalValue(start),
    end_datetime: toDateTimeLocalValue(end),
    status: "upcoming",
    early_check_in_minutes: `${defaults.early_check_in_minutes}`,
    late_threshold_minutes: `${defaults.late_threshold_minutes}`,
    sign_out_grace_minutes: `${defaults.sign_out_grace_minutes}`,
    geo_required: false,
    geo_latitude: "",
    geo_longitude: "",
    geo_radius_m: "",
    geo_max_accuracy_m: "",
  };
};

const toEventDefaultsDraft = (
  defaults: EventDefaultSettings = FALLBACK_EVENT_DEFAULT_SETTINGS
): EventDefaultsDraftState => ({
  early_check_in_minutes: `${defaults.early_check_in_minutes}`,
  late_threshold_minutes: `${defaults.late_threshold_minutes}`,
  sign_out_grace_minutes: `${defaults.sign_out_grace_minutes}`,
});

const parseOptionalNumber = (value: string): number | null => {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : NaN;
};

const formatOptionalNumber = (value?: number | null) => (value == null ? "" : `${value}`);

const toDraftDateTimeValue = (value: string, fallback: string) => {
  const parsed = parseEventDateTime(value);
  return Number.isFinite(parsed.getTime()) ? toDateTimeLocalValue(parsed) : fallback;
};

const getScopeTitle = (governanceContext: GovernanceContext) => {
  if (governanceContext === "SSG") {
    return "New events created here are scoped to the whole campus SSG workspace.";
  }
  if (governanceContext === "SG") {
    return "New events created here are automatically limited to your SG department.";
  }
  return "New events created here are automatically limited to your ORG program.";
};

const NEAR_START_ATTENDANCE_OVERRIDE_ABSENT_WINDOW_MINUTES = 20;

type NearStartAttendanceOverridePreview = {
  effectivePresentUntil: Date;
  effectiveLateUntil: Date;
};

const getNearStartAttendanceOverrideValidationMessage = ({
  startDate,
  endDate,
  earlyCheckInMinutes,
  lateThresholdMinutes,
  now = new Date(),
}: {
  startDate: Date;
  endDate: Date;
  earlyCheckInMinutes: number;
  lateThresholdMinutes: number;
  now?: Date;
}) => {
  const normalizedEarlyCheckInMinutes = Math.max(0, Math.trunc(earlyCheckInMinutes));
  const normalizedLateThresholdMinutes = Math.max(0, Math.trunc(lateThresholdMinutes));

  if (normalizedEarlyCheckInMinutes <= 0) {
    return null;
  }

  const timeUntilStartMs = startDate.getTime() - now.getTime();
  if (timeUntilStartMs >= normalizedEarlyCheckInMinutes * 60_000) {
    return null;
  }

  if (startDate.getTime() <= now.getTime()) {
    return "This event start time is already in the past, so the near-start attendance override cannot preserve the full present window. Move the start time later or reduce the early check-in minutes.";
  }

  const requiredDurationMinutes =
    normalizedEarlyCheckInMinutes +
    normalizedLateThresholdMinutes +
    NEAR_START_ATTENDANCE_OVERRIDE_ABSENT_WINDOW_MINUTES;
  const remainingDurationMs = endDate.getTime() - now.getTime();

  if (remainingDurationMs < requiredDurationMinutes * 60_000) {
    return `This event is too short for the near-start attendance override. It needs at least ${requiredDurationMinutes} minutes from now until the event end to keep ${normalizedEarlyCheckInMinutes} minutes present, ${normalizedLateThresholdMinutes} minutes late, and ${NEAR_START_ATTENDANCE_OVERRIDE_ABSENT_WINDOW_MINUTES} minutes absent.`;
  }

  return null;
};

const getNearStartAttendanceOverridePreview = ({
  startDate,
  endDate,
  earlyCheckInMinutes,
  lateThresholdMinutes,
  now = new Date(),
}: {
  startDate: Date;
  endDate: Date;
  earlyCheckInMinutes: number;
  lateThresholdMinutes: number;
  now?: Date;
}): NearStartAttendanceOverridePreview | null => {
  const validationMessage = getNearStartAttendanceOverrideValidationMessage({
    startDate,
    endDate,
    earlyCheckInMinutes,
    lateThresholdMinutes,
    now,
  });

  if (validationMessage) {
    return null;
  }

  const normalizedEarlyCheckInMinutes = Math.max(0, Math.trunc(earlyCheckInMinutes));
  const timeUntilStartMs = startDate.getTime() - now.getTime();
  if (normalizedEarlyCheckInMinutes <= 0 || timeUntilStartMs >= normalizedEarlyCheckInMinutes * 60_000) {
    return null;
  }

  const effectivePresentUntil = new Date(now.getTime() + normalizedEarlyCheckInMinutes * 60_000);
  const effectiveLateUntil = new Date(
    effectivePresentUntil.getTime() + Math.max(0, Math.trunc(lateThresholdMinutes)) * 60_000
  );

  return {
    effectivePresentUntil,
    effectiveLateUntil,
  };
};

const getNextStatusActions = (status: EventStatus) => {
  if (status === "upcoming") {
    return [
      { label: "Start", status: "ongoing" as EventStatus, tone: "btn btn-primary" },
      { label: "Cancel", status: "cancelled" as EventStatus, tone: "btn btn-outline-secondary" },
    ];
  }

  if (status === "ongoing") {
    return [
      { label: "Complete", status: "completed" as EventStatus, tone: "btn btn-primary" },
      { label: "Cancel", status: "cancelled" as EventStatus, tone: "btn btn-outline-secondary" },
    ];
  }

  return [{ label: "Reopen", status: "upcoming" as EventStatus, tone: "btn btn-outline-secondary" }];
};

export const Events: React.FC<EventsProps> = ({ role }) => {
  const governanceContext: GovernanceContext | null =
    role === "ssg" ? "SSG" : role === "sg" ? "SG" : role === "org" ? "ORG" : null;
  const governanceUnitType = (governanceContext ?? "SSG") as GovernanceContext;
  const isGovernanceRole = Boolean(governanceContext);
  const canManageSchoolEventDefaults = role === "campus_admin";
  const canManageGovernanceEventDefaults =
    governanceContext === "SG" || governanceContext === "ORG";
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState<
    "all" | "upcoming" | "ongoing" | "completed" | "cancelled"
  >("all");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [statusActionKey, setStatusActionKey] = useState<string | null>(null);
  const [settingsLoading, setSettingsLoading] = useState(
    role !== "admin"
  );
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<EventRecord | null>(null);
  const [pendingDelete, setPendingDelete] = useState<EventRecord | null>(null);
  const [pendingStatusConfirmation, setPendingStatusConfirmation] =
    useState<PendingStatusConfirmationState | null>(null);
  const [pendingEventSave, setPendingEventSave] = useState<PendingEventSaveState | null>(null);
  const [draft, setDraft] = useState<EventDraftState>(() => getDefaultDraft());
  const [settingsDraft, setSettingsDraft] = useState<EventDefaultsDraftState>(() =>
    toEventDefaultsDraft()
  );
  const [schoolSettings, setSchoolSettings] = useState<SchoolSettings | null>(null);
  const [governanceEventDefaults, setGovernanceEventDefaults] =
    useState<GovernanceEventDefaults | null>(null);
  const [governanceSettingsUnitId, setGovernanceSettingsUnitId] = useState<number | null>(null);
  const deferredSearchTerm = useDeferredValue(searchTerm);

  const schoolEventDefaults = useMemo(
    () => getSchoolEventDefaultSettings(schoolSettings),
    [schoolSettings]
  );
  const effectiveEventDefaults = useMemo(() => {
    if (canManageGovernanceEventDefaults) {
      return getGovernanceEventDefaultSettings(governanceEventDefaults);
    }
    return schoolEventDefaults;
  }, [canManageGovernanceEventDefaults, governanceEventDefaults, schoolEventDefaults]);

  const geofenceValue = useMemo(
    () => ({
      latitude: draft.geo_latitude.trim() ? Number(draft.geo_latitude) : null,
      longitude: draft.geo_longitude.trim() ? Number(draft.geo_longitude) : null,
      radiusM: Number(draft.geo_radius_m || "100") || 100,
      maxAccuracyM: Number(draft.geo_max_accuracy_m || "50") || 50,
      required: draft.geo_required,
    }),
    [
      draft.geo_latitude,
      draft.geo_longitude,
      draft.geo_radius_m,
      draft.geo_max_accuracy_m,
      draft.geo_required,
    ]
  );
  const nearStartAttendanceOverridePreview = useMemo(() => {
    const startDate = parseEventDateTime(draft.start_datetime);
    const endDate = parseEventDateTime(draft.end_datetime);
    const earlyCheckInMinutes = Number(draft.early_check_in_minutes || "0");
    const lateThresholdMinutes = Number(draft.late_threshold_minutes || "0");

    if (
      !Number.isFinite(startDate.getTime()) ||
      !Number.isFinite(endDate.getTime()) ||
      !Number.isFinite(earlyCheckInMinutes) ||
      !Number.isFinite(lateThresholdMinutes) ||
      earlyCheckInMinutes < 0 ||
      lateThresholdMinutes < 0
    ) {
      return null;
    }

    return getNearStartAttendanceOverridePreview({
      startDate,
      endDate,
      earlyCheckInMinutes,
      lateThresholdMinutes,
    });
  }, [
    draft.end_datetime,
    draft.early_check_in_minutes,
    draft.late_threshold_minutes,
    draft.start_datetime,
  ]);

  const loadEvents = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      const allEvents = await fetchAllEvents(forceRefresh, governanceContext ?? undefined);
      setEvents(allEvents);
      setError(null);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to fetch events. Please try again later."
      );
    } finally {
      setLoading(false);
    }
  }, [governanceContext]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  useEffect(() => {
    if (role === "admin") {
      setSchoolSettings(null);
      setGovernanceEventDefaults(null);
      setGovernanceSettingsUnitId(null);
      setSettingsLoading(false);
      return;
    }

    let isMounted = true;
    setSettingsLoading(true);

    const loadEventDefaults = async () => {
      try {
        const schoolSettingsResult = await fetchSchoolSettings();
        if (!isMounted) {
          return;
        }
        setSchoolSettings(schoolSettingsResult);

        if (governanceContext === "SG" || governanceContext === "ORG") {
          const access = await fetchMyGovernanceAccess();
          if (!isMounted) {
            return;
          }
          const accessUnit =
            access.units.find((unit) => unit.unit_type === governanceContext) ?? null;
          if (!accessUnit) {
            throw new Error(`No ${governanceContext} governance workspace was found for this account.`);
          }
          setGovernanceSettingsUnitId(accessUnit.governance_unit_id);
          const governanceDefaultsResult = await fetchGovernanceEventDefaults(
            accessUnit.governance_unit_id
          );
          if (!isMounted) {
            return;
          }
          setGovernanceEventDefaults(governanceDefaultsResult);
          const nextDefaults = getGovernanceEventDefaultSettings(governanceDefaultsResult);
          setSettingsDraft(toEventDefaultsDraft(nextDefaults));
        } else {
          setGovernanceEventDefaults(null);
          setGovernanceSettingsUnitId(null);
          const nextDefaults = getSchoolEventDefaultSettings(schoolSettingsResult);
          setSettingsDraft(toEventDefaultsDraft(nextDefaults));
        }
      } catch (requestError) {
        if (!isMounted) {
          return;
        }
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to load the event default settings."
        );
      } finally {
        if (isMounted) {
          setSettingsLoading(false);
        }
      }
    };

    void loadEventDefaults();

    return () => {
      isMounted = false;
    };
  }, [governanceContext, role]);

  useEffect(() => {
    if (!isCreateModalOpen || editingEvent) {
      return;
    }

    setDraft((current) => ({
      ...current,
      early_check_in_minutes: `${effectiveEventDefaults.early_check_in_minutes}`,
      late_threshold_minutes: `${effectiveEventDefaults.late_threshold_minutes}`,
      sign_out_grace_minutes: `${effectiveEventDefaults.sign_out_grace_minutes}`,
    }));
  }, [editingEvent, effectiveEventDefaults, isCreateModalOpen]);

  const formatDateTime = (datetime: string) => {
    return formatManilaDateTime(datetime);
  };

  const filteredEvents = useMemo(
    () =>
      events
        .filter((event) => event.name.toLowerCase().includes(deferredSearchTerm.toLowerCase()))
        .filter((event) => {
          if (filter === "upcoming") return event.status === "upcoming";
          if (filter === "ongoing") return event.status === "ongoing";
          if (filter === "completed") return event.status === "completed";
          if (filter === "cancelled") return event.status === "cancelled";
          return true;
        }),
    [deferredSearchTerm, events, filter]
  );

  const eventStats = useMemo(
    () => [
      {
        label: "Total Events",
        value: events.length,
        hint: "All events currently visible in your scope",
      },
      {
        label: "Upcoming",
        value: events.filter((event) => event.status === "upcoming").length,
        hint: "Events scheduled to start later",
      },
      {
        label: "Ongoing",
        value: events.filter((event) => event.status === "ongoing").length,
        hint: "Events happening right now",
      },
      {
        label: "Completed",
        value: events.filter((event) => event.status === "completed").length,
        hint: "Finished events already on record",
      },
    ],
    [events]
  );

  const openCreateModal = () => {
    setEditingEvent(null);
    setDraft(getDefaultDraft(effectiveEventDefaults));
    setIsCreateModalOpen(true);
    setError(null);
    setSuccess(null);
  };

  const openEditModal = (eventRecord: EventRecord) => {
    const fallbackDraft = getDefaultDraft(effectiveEventDefaults);
    setEditingEvent(eventRecord);
    setDraft({
      name: eventRecord.name,
      location: eventRecord.location,
      start_datetime: toDraftDateTimeValue(eventRecord.start_datetime, fallbackDraft.start_datetime),
      end_datetime: toDraftDateTimeValue(eventRecord.end_datetime, fallbackDraft.end_datetime),
      status: eventRecord.status,
      early_check_in_minutes: `${eventRecord.early_check_in_minutes ?? 0}`,
      late_threshold_minutes: `${eventRecord.late_threshold_minutes ?? 0}`,
      sign_out_grace_minutes: `${eventRecord.sign_out_grace_minutes ?? 0}`,
      geo_required: Boolean(eventRecord.geo_required),
      geo_latitude: formatOptionalNumber(eventRecord.geo_latitude),
      geo_longitude: formatOptionalNumber(eventRecord.geo_longitude),
      geo_radius_m: formatOptionalNumber(eventRecord.geo_radius_m),
      geo_max_accuracy_m: formatOptionalNumber(eventRecord.geo_max_accuracy_m),
    });
    setIsCreateModalOpen(true);
    setError(null);
    setSuccess(null);
  };

  const closeCreateModal = () => {
    if (saving) {
      return;
    }
    setEditingEvent(null);
    setPendingEventSave(null);
    setIsCreateModalOpen(false);
  };

  const parseSettingsDraft = () => {
    const earlyCheckInMinutes = Number(settingsDraft.early_check_in_minutes || "0");
    const lateThresholdMinutes = Number(settingsDraft.late_threshold_minutes || "0");
    const signOutGraceMinutes = Number(settingsDraft.sign_out_grace_minutes || "0");

    if (!Number.isFinite(earlyCheckInMinutes) || earlyCheckInMinutes < 0) {
      throw new Error("Early check-in default must be zero or greater.");
    }
    if (!Number.isFinite(lateThresholdMinutes) || lateThresholdMinutes < 0) {
      throw new Error("Late threshold default must be zero or greater.");
    }
    if (!Number.isFinite(signOutGraceMinutes) || signOutGraceMinutes < 0) {
      throw new Error("Sign-out default must be zero or greater.");
    }

    return {
      early_check_in_minutes: earlyCheckInMinutes,
      late_threshold_minutes: lateThresholdMinutes,
      sign_out_grace_minutes: signOutGraceMinutes,
    };
  };

  const syncCreateDraftWithDefaults = (defaults: EventDefaultSettings) => {
    setDraft((current) =>
      editingEvent
        ? current
        : {
            ...current,
            early_check_in_minutes: `${defaults.early_check_in_minutes}`,
            late_threshold_minutes: `${defaults.late_threshold_minutes}`,
            sign_out_grace_minutes: `${defaults.sign_out_grace_minutes}`,
          }
    );
  };

  const handleSaveEventDefaults = async () => {
    try {
      const parsedDefaults = parseSettingsDraft();
      setSettingsSaving(true);
      setError(null);
      setSuccess(null);

      if (canManageGovernanceEventDefaults) {
        if (!governanceSettingsUnitId) {
          throw new Error("No governance unit was found for event default settings.");
        }
        const updatedDefaults = await updateGovernanceEventDefaults(governanceSettingsUnitId, {
          early_check_in_minutes: parsedDefaults.early_check_in_minutes,
          late_threshold_minutes: parsedDefaults.late_threshold_minutes,
          sign_out_grace_minutes: parsedDefaults.sign_out_grace_minutes,
        });
        setGovernanceEventDefaults(updatedDefaults);
        const nextDefaults = getGovernanceEventDefaultSettings(updatedDefaults);
        setSettingsDraft(toEventDefaultsDraft(nextDefaults));
        syncCreateDraftWithDefaults(nextDefaults);
        setSuccess(`${governanceContext} event defaults updated successfully.`);
        return;
      }

      if (canManageSchoolEventDefaults) {
        const updatedSchoolSettings = await updateSchoolSettings({
          event_default_early_check_in_minutes: parsedDefaults.early_check_in_minutes,
          event_default_late_threshold_minutes: parsedDefaults.late_threshold_minutes,
          event_default_sign_out_grace_minutes: parsedDefaults.sign_out_grace_minutes,
        });
        setSchoolSettings(updatedSchoolSettings);
        const nextDefaults = getSchoolEventDefaultSettings(updatedSchoolSettings);
        setSettingsDraft(toEventDefaultsDraft(nextDefaults));
        syncCreateDraftWithDefaults(nextDefaults);
        setSuccess("School event defaults updated successfully.");
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to update the event default settings."
      );
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleResetGovernanceDefaultsToSchool = async () => {
    if (!canManageGovernanceEventDefaults || !governanceSettingsUnitId) {
      return;
    }

    try {
      setSettingsSaving(true);
      setError(null);
      setSuccess(null);
      const updatedDefaults = await updateGovernanceEventDefaults(governanceSettingsUnitId, {
        early_check_in_minutes: null,
        late_threshold_minutes: null,
        sign_out_grace_minutes: null,
      });
      setGovernanceEventDefaults(updatedDefaults);
      const nextDefaults = getGovernanceEventDefaultSettings(updatedDefaults);
      setSettingsDraft(toEventDefaultsDraft(nextDefaults));
      syncCreateDraftWithDefaults(nextDefaults);
      setSuccess(`${governanceContext} event defaults now inherit the school defaults.`);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to reset the governance event defaults."
      );
    } finally {
      setSettingsSaving(false);
    }
  };

  const buildEventPayload = (): PendingEventSaveState | null => {
    const name = draft.name.trim();
    const location = draft.location.trim();
    const startDate = parseEventDateTime(draft.start_datetime);
    const endDate = parseEventDateTime(draft.end_datetime);
    const earlyCheckInMinutes = Number(draft.early_check_in_minutes || "0");
    const lateThresholdMinutes = Number(draft.late_threshold_minutes || "0");
    const signOutGraceMinutes = Number(draft.sign_out_grace_minutes || "0");

    if (!name || !location) {
      setError("Event name and location are required.");
      return null;
    }

    if (!Number.isFinite(startDate.getTime()) || !Number.isFinite(endDate.getTime())) {
      setError("Start and end date/time must be valid.");
      return null;
    }

    if (startDate >= endDate) {
      setError("End date/time must be after the start date/time.");
      return null;
    }

    if (!Number.isFinite(lateThresholdMinutes) || lateThresholdMinutes < 0) {
      setError("Late threshold minutes must be zero or greater.");
      return null;
    }

    if (!Number.isFinite(earlyCheckInMinutes) || earlyCheckInMinutes < 0) {
      setError("Early check-in window must be zero or greater.");
      return null;
    }

    if (!Number.isFinite(signOutGraceMinutes) || signOutGraceMinutes < 0) {
      setError("Sign-out window must be zero or greater.");
      return null;
    }

    const nearStartValidationMessage = getNearStartAttendanceOverrideValidationMessage({
      startDate,
      endDate,
      earlyCheckInMinutes,
      lateThresholdMinutes,
    });
    if (nearStartValidationMessage) {
      setError(nearStartValidationMessage);
      return null;
    }

    const geoLatitude = parseOptionalNumber(draft.geo_latitude);
    const geoLongitude = parseOptionalNumber(draft.geo_longitude);
    const geoRadius = parseOptionalNumber(draft.geo_radius_m);
    const geoMaxAccuracy = parseOptionalNumber(draft.geo_max_accuracy_m);

    if (
      draft.geo_required &&
      (geoLatitude === null || geoLongitude === null || geoRadius === null)
    ) {
      setError("Latitude, longitude, and radius are required when geolocation is enabled.");
      return null;
    }

    if ([geoLatitude, geoLongitude, geoRadius, geoMaxAccuracy].some((value) => Number.isNaN(value))) {
      setError("Geolocation fields must contain valid numbers.");
      return null;
    }

    const payload: CreateEventPayload = {
      name,
      location,
      start_datetime: draft.start_datetime,
      end_datetime: draft.end_datetime,
      status: draft.status,
      geo_required: draft.geo_required,
      geo_latitude: geoLatitude,
      geo_longitude: geoLongitude,
      geo_radius_m: geoRadius,
      geo_max_accuracy_m: geoMaxAccuracy,
    };

    if (editingEvent) {
      payload.early_check_in_minutes = earlyCheckInMinutes;
      payload.late_threshold_minutes = lateThresholdMinutes;
      payload.sign_out_grace_minutes = signOutGraceMinutes;
    } else {
      if (earlyCheckInMinutes !== effectiveEventDefaults.early_check_in_minutes) {
        payload.early_check_in_minutes = earlyCheckInMinutes;
      }
      if (lateThresholdMinutes !== effectiveEventDefaults.late_threshold_minutes) {
        payload.late_threshold_minutes = lateThresholdMinutes;
      }
      if (signOutGraceMinutes !== effectiveEventDefaults.sign_out_grace_minutes) {
        payload.sign_out_grace_minutes = signOutGraceMinutes;
      }
    }

    return {
      eventName: name,
      payload,
    };
  };

  const persistEventSave = async (payload: CreateEventPayload | UpdateEventPayload) => {
    if (!governanceContext) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      if (editingEvent) {
        await updateEvent(editingEvent.id, payload, governanceContext);
      } else {
        await createEvent(payload as CreateEventPayload, governanceContext);
      }

      await loadEvents(true);
      setSuccess(editingEvent ? "Event updated successfully." : "Event created successfully.");
      setEditingEvent(null);
      setPendingEventSave(null);
      setIsCreateModalOpen(false);
      setDraft(getDefaultDraft(effectiveEventDefaults));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : editingEvent
            ? "Failed to update event"
            : "Failed to create event"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleSaveEvent = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!governanceContext) {
      return;
    }

    const preparedSave = buildEventPayload();
    if (!preparedSave) {
      return;
    }

    if (editingEvent) {
      setError(null);
      setSuccess(null);
      setPendingEventSave(preparedSave);
      return;
    }

    await persistEventSave(preparedSave.payload);
  };

  const handleDeleteEvent = async () => {
    if (!governanceContext || !pendingDelete) {
      return;
    }

    try {
      setDeleting(true);
      setError(null);
      setSuccess(null);
      await deleteEvent(pendingDelete.id, governanceContext);
      await loadEvents(true);
      setSuccess("Event deleted successfully.");
      setPendingDelete(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to delete event");
    } finally {
      setDeleting(false);
    }
  };

  const handleGeofenceChange = (nextValue: {
    latitude: number | null;
    longitude: number | null;
    radiusM: number;
    maxAccuracyM: number;
    required: boolean;
  }) => {
    setDraft((current) => ({
      ...current,
      geo_required: nextValue.required,
      geo_latitude: nextValue.latitude == null ? "" : `${nextValue.latitude}`,
      geo_longitude: nextValue.longitude == null ? "" : `${nextValue.longitude}`,
      geo_radius_m: `${nextValue.radiusM}`,
      geo_max_accuracy_m: `${nextValue.maxAccuracyM}`,
    }));
  };

  const runQuickStatusChange = async (
    eventRecord: EventRecord,
    nextStatus: EventStatus
  ): Promise<boolean> => {
    if (!governanceContext) {
      return false;
    }

    try {
      const actionKey = `${eventRecord.id}:${nextStatus}`;
      setStatusActionKey(actionKey);
      setError(null);
      setSuccess(null);
      const updatedEvent = await updateEventStatus(eventRecord.id, nextStatus, governanceContext);
      await loadEvents(true);
      setSuccess(`Event status updated to ${updatedEvent.status}.`);
      return true;
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to update the event status"
      );
      return false;
    } finally {
      setStatusActionKey(null);
    }
  };

  const handleQuickStatusChange = async (
    eventRecord: EventRecord,
    nextStatus: EventStatus
  ) => {
    if (nextStatus === "cancelled") {
      setError(null);
      setSuccess(null);
      setPendingStatusConfirmation({ eventRecord, nextStatus });
      return;
    }

    await runQuickStatusChange(eventRecord, nextStatus);
  };

  const handleConfirmStatusChange = async () => {
    if (!pendingStatusConfirmation) {
      return;
    }

    const wasSuccessful = await runQuickStatusChange(
      pendingStatusConfirmation.eventRecord,
      pendingStatusConfirmation.nextStatus
    );
    if (wasSuccessful) {
      setPendingStatusConfirmation(null);
    }
  };

  const handleConfirmEventSave = async () => {
    if (!pendingEventSave) {
      return;
    }

    await persistEventSave(pendingEventSave.payload);
  };

  if (isGovernanceRole) {
    const activeGovernanceContext = governanceContext as GovernanceContext;
    const shellTitle =
      activeGovernanceContext === "SSG"
        ? "Campus event directory"
        : activeGovernanceContext === "SG"
          ? "Department event directory"
          : "Organization event directory";
    const shellDescription =
      activeGovernanceContext === "SSG"
        ? "Review all visible events, scan their current status, and create new events for the campus SSG workspace."
        : activeGovernanceContext === "SG"
          ? "Review department-scoped events, monitor their status, and create new SG events inside your department."
          : "Review organization events, monitor their status, and create new ORG events inside your program.";

    return (
      <>
        <SsgFeatureShell
          eyebrow={`${activeGovernanceContext} / Events`}
          title={shellTitle}
          description={shellDescription}
          stats={eventStats}
          unitType={governanceUnitType}
          actions={
            <button type="button" className="btn btn-light" onClick={openCreateModal}>
              <FaPlus className="me-2" />
              New Event
            </button>
          }
        >
          {error && <div className="alert alert-danger mb-0">{error}</div>}
          {success && <div className="alert alert-success mb-0">{success}</div>}

          <section className="ssg-feature-card">
            <div className="ssg-feature-card__header">
              <div>
                <h2 className="ssg-feature-card__title">Event default settings</h2>
                <p className="ssg-feature-card__subtitle">
                  New {activeGovernanceContext} events use these attendance timing defaults automatically.
                </p>
              </div>
              {canManageGovernanceEventDefaults ? (
                <div className="ssg-inline-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => void handleSaveEventDefaults()}
                    disabled={settingsLoading || settingsSaving}
                  >
                    {settingsSaving ? "Saving..." : "Save Defaults"}
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={() => void handleResetGovernanceDefaultsToSchool()}
                    disabled={settingsLoading || settingsSaving}
                  >
                    Use School Defaults
                  </button>
                </div>
              ) : null}
            </div>

            {settingsLoading ? (
              <div className="ssg-feature-empty">Loading event default settings...</div>
            ) : canManageGovernanceEventDefaults ? (
              <>
                <div className="ssg-muted-note">
                  {governanceEventDefaults?.inherits_school_defaults
                    ? "This workspace currently inherits the school-wide defaults."
                    : "This workspace currently uses its own SG/ORG override for future events."}
                </div>
                <div className="ssg-feature-form-grid">
                  <div className="form-group">
                    <label htmlFor="governanceDefaultEarlyCheckIn">Early check-in window (minutes)</label>
                    <input
                      id="governanceDefaultEarlyCheckIn"
                      type="number"
                      min={0}
                      max={1440}
                      value={settingsDraft.early_check_in_minutes}
                      onChange={(changeEvent) =>
                        setSettingsDraft((current) => ({
                          ...current,
                          early_check_in_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="governanceDefaultLateThreshold">Late threshold (minutes)</label>
                    <input
                      id="governanceDefaultLateThreshold"
                      type="number"
                      min={0}
                      max={1440}
                      value={settingsDraft.late_threshold_minutes}
                      onChange={(changeEvent) =>
                        setSettingsDraft((current) => ({
                          ...current,
                          late_threshold_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="governanceDefaultSignOut">Sign-out window (minutes after end)</label>
                    <input
                      id="governanceDefaultSignOut"
                      type="number"
                      min={0}
                      max={1440}
                      value={settingsDraft.sign_out_grace_minutes}
                      onChange={(changeEvent) =>
                        setSettingsDraft((current) => ({
                          ...current,
                          sign_out_grace_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>
                </div>
                <div className="ssg-muted-note">
                  School defaults: early {schoolEventDefaults.early_check_in_minutes} min, late{" "}
                  {schoolEventDefaults.late_threshold_minutes} min, sign-out{" "}
                  {schoolEventDefaults.sign_out_grace_minutes} min.
                </div>
              </>
            ) : (
              <div className="ssg-feature-form-grid">
                <div className="ssg-feature-field">
                  <label>Early check-in window</label>
                  <div className="ssg-muted-note">
                    {schoolEventDefaults.early_check_in_minutes} minute(s)
                  </div>
                </div>
                <div className="ssg-feature-field">
                  <label>Late threshold</label>
                  <div className="ssg-muted-note">
                    {schoolEventDefaults.late_threshold_minutes} minute(s)
                  </div>
                </div>
                <div className="ssg-feature-field">
                  <label>Sign-out window</label>
                  <div className="ssg-muted-note">
                    {schoolEventDefaults.sign_out_grace_minutes} minute(s) after the scheduled end
                  </div>
                </div>
                <div className="ssg-muted-note">
                  SSG uses the school-wide defaults. Campus Admin can change these values from the campus Events page.
                </div>
              </div>
            )}
          </section>

          <section className="ssg-feature-card">
            <div className="ssg-feature-card__header">
              <div>
                <h2 className="ssg-feature-card__title">Event records</h2>
                <p className="ssg-feature-card__subtitle">
                  Search events by name, filter by status, and open the create form for new
                  {activeGovernanceContext === "SSG"
                    ? " campus"
                    : activeGovernanceContext === "SG"
                      ? " department"
                      : " organization"} events.
                </p>
              </div>
              <button type="button" className="btn btn-primary" onClick={openCreateModal}>
                <FaPlus className="me-2" />
                Create Event
              </button>
            </div>

            <div className="ssg-muted-note">{getScopeTitle(activeGovernanceContext)}</div>

            <div className="ssg-feature-controls">
              <div className="ssg-feature-search">
                <FaSearch />
                <input
                  type="text"
                  placeholder="Search events..."
                  value={searchTerm}
                  onChange={(searchEvent) => setSearchTerm(searchEvent.target.value)}
                />
              </div>

              <select
                className="ssg-feature-select"
                value={filter}
                onChange={(filterEvent) =>
                  setFilter(
                    filterEvent.target.value as
                      | "all"
                      | "upcoming"
                      | "ongoing"
                      | "completed"
                      | "cancelled"
                  )
                }
              >
                <option value="all">All Events</option>
                <option value="upcoming">Upcoming</option>
                <option value="ongoing">Ongoing</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {loading ? (
              <div className="ssg-feature-empty">Loading events...</div>
            ) : (
              <div className="ssg-feature-table-card">
                <table>
                  <thead>
                    <tr>
                      <th>Event Name</th>
                      <th>Department(s)</th>
                      <th>Program(s)</th>
                      <th>Date & Time</th>
                      <th>Location</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEvents.length > 0 ? (
                      filteredEvents.map((listedEvent) => (
                        <tr key={listedEvent.id}>
                          <td data-label="Event Name">
                            <Link
                              to={getGovernanceEventDetailsPath(activeGovernanceContext, listedEvent.id)}
                              className="ssg-link-button"
                            >
                              {listedEvent.name}
                            </Link>
                          </td>
                          <td>{formatEventDepartments(listedEvent.departments)}</td>
                          <td>{formatEventPrograms(listedEvent.programs)}</td>
                          <td>
                            {formatDateTime(listedEvent.start_datetime)} -{" "}
                            {formatDateTime(listedEvent.end_datetime)}
                          </td>
                          <td>{listedEvent.location}</td>
                          <td>
                            <span
                              className={`ssg-badge ${
                                listedEvent.status === "upcoming"
                                  ? "ssg-badge--draft"
                                  : listedEvent.status === "ongoing"
                                    ? "ssg-badge--published"
                                    : "ssg-badge--archived"
                              }`}
                            >
                              {listedEvent.status.charAt(0).toUpperCase() + listedEvent.status.slice(1)}
                            </span>
                          </td>
                          <td data-label="Actions">
                            <div className="ssg-inline-actions">
                              <Link
                                to={getGovernanceEventDetailsPath(activeGovernanceContext, listedEvent.id)}
                                className="btn btn-light"
                              >
                                Details
                              </Link>
                              {getNextStatusActions(listedEvent.status).map((action) => {
                                const actionKey = `${listedEvent.id}:${action.status}`;
                                return (
                                  <button
                                    key={action.status}
                                    type="button"
                                    className={action.tone}
                                    onClick={() =>
                                      void handleQuickStatusChange(listedEvent, action.status)
                                    }
                                    disabled={statusActionKey === actionKey}
                                  >
                                    {statusActionKey === actionKey
                                      ? "Saving..."
                                      : action.label}
                                  </button>
                                );
                              })}
                              <button
                                type="button"
                                className="btn btn-outline-secondary"
                                onClick={() => openEditModal(listedEvent)}
                              >
                                <FaEdit className="me-2" />
                                Edit
                              </button>
                              <button
                                type="button"
                                className="btn btn-danger"
                                onClick={() => setPendingDelete(listedEvent)}
                              >
                                <FaTrashAlt className="me-2" />
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7}>
                          <div className="ssg-feature-empty d-flex flex-column align-items-start gap-3">
                            <span>No matching events found.</span>
                            <button
                              type="button"
                              className="btn btn-primary"
                              onClick={openCreateModal}
                            >
                              <FaPlus className="me-2" />
                              Create Event
                            </button>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </SsgFeatureShell>

        <Modal
          isOpen={isCreateModalOpen}
          onRequestClose={closeCreateModal}
          className="ssg-setup-modal"
          overlayClassName="ssg-setup-overlay"
        >
          <form onSubmit={handleSaveEvent}>
            <div className="ssg-setup-modal__header">
              <div>
                <h3>{editingEvent ? "Edit Event" : "Create Event"}</h3>
                <p className="mb-0 text-muted">{getScopeTitle(activeGovernanceContext)}</p>
              </div>
              <button type="button" className="ssg-setup-modal__close" onClick={closeCreateModal}>
                &times;
              </button>
            </div>

            <div className="ssg-setup-modal__body">
              <div className="form-group">
                <label htmlFor="eventName">Event name</label>
                <input
                  id="eventName"
                  value={draft.name}
                  onChange={(changeEvent) =>
                    setDraft((current) => ({ ...current, name: changeEvent.target.value }))
                  }
                  placeholder="Campus Leadership Summit"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="eventLocation">Location</label>
                <input
                  id="eventLocation"
                  value={draft.location}
                  onChange={(changeEvent) =>
                    setDraft((current) => ({ ...current, location: changeEvent.target.value }))
                  }
                  placeholder="University Gymnasium"
                  required
                />
              </div>

              <div className="row g-3">
                <div className="col-md-6 form-group">
                  <label htmlFor="eventStart">Start date and time</label>
                  <input
                    id="eventStart"
                    type="datetime-local"
                    value={draft.start_datetime}
                    onChange={(changeEvent) =>
                      setDraft((current) => ({ ...current, start_datetime: changeEvent.target.value }))
                    }
                    required
                  />
                </div>
                <div className="col-md-6 form-group">
                  <label htmlFor="eventEnd">End date and time</label>
                  <input
                    id="eventEnd"
                    type="datetime-local"
                    value={draft.end_datetime}
                    onChange={(changeEvent) =>
                      setDraft((current) => ({ ...current, end_datetime: changeEvent.target.value }))
                    }
                    required
                  />
                </div>
              </div>

              {nearStartAttendanceOverridePreview ? (
                <div className="ssg-muted-note">
                  This event starts too close to the current time to keep the full present window on
                  the scheduled start alone. If you save it, the backend will keep students
                  <strong> present</strong> until{" "}
                  <strong>
                    {formatManilaDateTime(
                      nearStartAttendanceOverridePreview.effectivePresentUntil.toISOString()
                    )}
                  </strong>{" "}
                  and <strong>late</strong> until{" "}
                  <strong>
                    {formatManilaDateTime(
                      nearStartAttendanceOverridePreview.effectiveLateUntil.toISOString()
                    )}
                  </strong>
                  . The event workflow status will still follow the scheduled start and end time.
                </div>
              ) : null}

              {editingEvent ? (
                <>
                  <div className="form-group">
                    <label htmlFor="earlyCheckInMinutes">Early check-in window (minutes)</label>
                    <input
                      id="earlyCheckInMinutes"
                      type="number"
                      min={0}
                      max={1440}
                      value={draft.early_check_in_minutes}
                      onChange={(changeEvent) =>
                        setDraft((current) => ({
                          ...current,
                          early_check_in_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="lateThresholdMinutes">Late threshold minutes</label>
                    <input
                      id="lateThresholdMinutes"
                      type="number"
                      min={0}
                      max={1440}
                      value={draft.late_threshold_minutes}
                      onChange={(changeEvent) =>
                        setDraft((current) => ({
                          ...current,
                          late_threshold_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="signOutGraceMinutes">Sign-out window (minutes after end)</label>
                    <input
                      id="signOutGraceMinutes"
                      type="number"
                      min={0}
                      max={1440}
                      value={draft.sign_out_grace_minutes}
                      onChange={(changeEvent) =>
                        setDraft((current) => ({
                          ...current,
                          sign_out_grace_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>
                </>
              ) : (
                <div className="ssg-muted-note">
                  This new event will use the current default attendance timing: early check-in{" "}
                  <strong>{effectiveEventDefaults.early_check_in_minutes} min</strong>, late threshold{" "}
                  <strong>{effectiveEventDefaults.late_threshold_minutes} min</strong>, sign-out{" "}
                  <strong>{effectiveEventDefaults.sign_out_grace_minutes} min</strong>. Update the Event
                  Default Settings above if you want future events to use different values.
                </div>
              )}

              {editingEvent ? (
                <div className="form-group">
                  <label htmlFor="eventStatus">Event status</label>
                  <select
                    id="eventStatus"
                    value={draft.status}
                    onChange={(changeEvent) =>
                      setDraft((current) => ({
                        ...current,
                        status: changeEvent.target.value as EventStatus,
                      }))
                    }
                  >
                    <option value="upcoming">Upcoming</option>
                    <option value="ongoing">Ongoing</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              ) : null}

              <EventGeofencePicker
                value={geofenceValue}
                onChange={handleGeofenceChange}
                invalidateKey={editingEvent?.id ?? isCreateModalOpen}
              />

              <div className="ssg-muted-note">
                {editingEvent ? (
                  <>This event stays inside the current governance scope while you edit it.</>
                ) : (
                  <>New governance events are created with the default <strong>upcoming</strong> status.</>
                )}
              </div>
            </div>

            <div className="ssg-setup-modal__footer">
              <button type="button" className="btn btn-outline-secondary" onClick={closeCreateModal}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? "Saving..." : editingEvent ? "Save Changes" : "Create Event"}
              </button>
            </div>
          </form>
        </Modal>

        <Modal
          isOpen={pendingDelete !== null}
          onRequestClose={() => {
            if (!deleting) {
              setPendingDelete(null);
            }
          }}
          className="ssg-setup-modal ssg-setup-modal--compact"
          overlayClassName="ssg-setup-overlay"
        >
          <div className="ssg-setup-modal__header">
            <h3>Delete Event</h3>
            <button
              type="button"
              className="ssg-setup-modal__close"
              onClick={() => {
                if (!deleting) {
                  setPendingDelete(null);
                }
              }}
            >
              &times;
            </button>
          </div>
          <div className="ssg-setup-modal__body">
            <p className="mb-0">
              Delete <strong>{pendingDelete?.name}</strong>? This will permanently remove the event
              and its attendance records from the current governance workspace.
            </p>
          </div>
          <div className="ssg-setup-modal__footer">
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={() => setPendingDelete(null)}
              disabled={deleting}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => void handleDeleteEvent()}
              disabled={deleting}
            >
              {deleting ? "Deleting..." : "Confirm Delete"}
            </button>
          </div>
        </Modal>

        <Modal
          isOpen={pendingStatusConfirmation !== null}
          onRequestClose={() => {
            if (!statusActionKey) {
              setPendingStatusConfirmation(null);
            }
          }}
          className="ssg-setup-modal ssg-setup-modal--compact"
          overlayClassName="ssg-setup-overlay"
        >
          <div className="ssg-setup-modal__header">
            <h3>Cancel Event</h3>
            <button
              type="button"
              className="ssg-setup-modal__close"
              onClick={() => {
                if (!statusActionKey) {
                  setPendingStatusConfirmation(null);
                }
              }}
            >
              &times;
            </button>
          </div>
          <div className="ssg-setup-modal__body">
            <p className="mb-0">
              {pendingStatusConfirmation?.eventRecord.status === "ongoing" ? (
                <>
                  Cancel <strong>{pendingStatusConfirmation.eventRecord.name}</strong>? This event is
                  already ongoing, so students will stop using its current attendance window until
                  you reopen it.
                </>
              ) : (
                <>
                  Cancel <strong>{pendingStatusConfirmation?.eventRecord.name}</strong>? This event
                  will stay cancelled until you reopen it.
                </>
              )}
            </p>
          </div>
          <div className="ssg-setup-modal__footer">
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={() => setPendingStatusConfirmation(null)}
              disabled={Boolean(statusActionKey)}
            >
              Keep Event
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => void handleConfirmStatusChange()}
              disabled={Boolean(statusActionKey)}
            >
              {statusActionKey ? "Saving..." : "Confirm Cancel"}
            </button>
          </div>
        </Modal>

        <Modal
          isOpen={pendingEventSave !== null}
          onRequestClose={() => {
            if (!saving) {
              setPendingEventSave(null);
            }
          }}
          className="ssg-setup-modal ssg-setup-modal--compact"
          overlayClassName="ssg-setup-overlay"
        >
          <div className="ssg-setup-modal__header">
            <h3>Save Event Changes</h3>
            <button
              type="button"
              className="ssg-setup-modal__close"
              onClick={() => {
                if (!saving) {
                  setPendingEventSave(null);
                }
              }}
            >
              &times;
            </button>
          </div>
          <div className="ssg-setup-modal__body">
            <p className="mb-0">
              Save the latest changes for <strong>{pendingEventSave?.eventName}</strong>? This will
              update the event details for the current governance workspace.
            </p>
          </div>
          <div className="ssg-setup-modal__footer">
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={() => setPendingEventSave(null)}
              disabled={saving}
            >
              Review Again
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void handleConfirmEventSave()}
              disabled={saving}
            >
              {saving ? "Saving..." : "Confirm Save"}
            </button>
          </div>
        </Modal>
      </>
    );
  }

  return (
    <div className="events-page">
      {role === "admin" && <NavbarAdmin />}
      {role === "campus_admin" && <NavbarSchoolIT />}

      <div className="events-container">
        <div className="events-header">
          <h2>Events</h2>
          <p className="subtitle">View and manage all events</p>
        </div>

        {canManageSchoolEventDefaults ? (
          <div className="card border-0 shadow-sm mb-4">
            <div className="card-body">
              <div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3">
                <div>
                  <h4 className="mb-1">School Event Default Settings</h4>
                  <p className="text-muted mb-0">
                    New SSG, SG, and ORG events inherit these values unless a department or organization override is saved.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void handleSaveEventDefaults()}
                  disabled={settingsLoading || settingsSaving}
                >
                  {settingsSaving ? "Saving..." : "Save Defaults"}
                </button>
              </div>

              {settingsLoading ? (
                <p className="text-muted mb-0">Loading event default settings...</p>
              ) : (
                <div className="row g-3">
                  <div className="col-md-4">
                    <label className="form-label" htmlFor="schoolDefaultEarlyCheckIn">
                      Early check-in window (minutes)
                    </label>
                    <input
                      id="schoolDefaultEarlyCheckIn"
                      className="form-control"
                      type="number"
                      min={0}
                      max={1440}
                      value={settingsDraft.early_check_in_minutes}
                      onChange={(changeEvent) =>
                        setSettingsDraft((current) => ({
                          ...current,
                          early_check_in_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label" htmlFor="schoolDefaultLateThreshold">
                      Late threshold (minutes)
                    </label>
                    <input
                      id="schoolDefaultLateThreshold"
                      className="form-control"
                      type="number"
                      min={0}
                      max={1440}
                      value={settingsDraft.late_threshold_minutes}
                      onChange={(changeEvent) =>
                        setSettingsDraft((current) => ({
                          ...current,
                          late_threshold_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label" htmlFor="schoolDefaultSignOut">
                      Sign-out window (minutes after end)
                    </label>
                    <input
                      id="schoolDefaultSignOut"
                      className="form-control"
                      type="number"
                      min={0}
                      max={1440}
                      value={settingsDraft.sign_out_grace_minutes}
                      onChange={(changeEvent) =>
                        setSettingsDraft((current) => ({
                          ...current,
                          sign_out_grace_minutes: changeEvent.target.value,
                        }))
                      }
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : null}

        <div className="search-filter-section">
          <div className="search-box">
            <FaSearch className="search-icon" />
            <input
              type="text"
              placeholder="Search events..."
              value={searchTerm}
              onChange={(changeEvent) => setSearchTerm(changeEvent.target.value)}
              className="search-input"
            />
          </div>

          <div className="filter-container">
            <button className="filter-btn" onClick={() => setDropdownOpen(!dropdownOpen)}>
              <FaFilter /> Filter
            </button>
            {dropdownOpen && (
              <div className="filter-dropdown">
                <button
                  className={`dropdown-item ${filter === "all" ? "active" : ""}`}
                  onClick={() => {
                    setFilter("all");
                    setDropdownOpen(false);
                  }}
                >
                  All Events
                </button>
                <button
                  className={`dropdown-item ${filter === "upcoming" ? "active" : ""}`}
                  onClick={() => {
                    setFilter("upcoming");
                    setDropdownOpen(false);
                  }}
                >
                  Upcoming
                </button>
                <button
                  className={`dropdown-item ${filter === "ongoing" ? "active" : ""}`}
                  onClick={() => {
                    setFilter("ongoing");
                    setDropdownOpen(false);
                  }}
                >
                  Ongoing
                </button>
                <button
                  className={`dropdown-item ${filter === "completed" ? "active" : ""}`}
                  onClick={() => {
                    setFilter("completed");
                    setDropdownOpen(false);
                  }}
                >
                  Completed
                </button>
                <button
                  className={`dropdown-item ${filter === "cancelled" ? "active" : ""}`}
                  onClick={() => {
                    setFilter("cancelled");
                    setDropdownOpen(false);
                  }}
                >
                  Cancelled
                </button>
              </div>
            )}
          </div>
        </div>

        {loading && <div className="loading-indicator">Loading events...</div>}
        {error && <div className="error-message">{error}</div>}

        {!loading && !error && (
          <div className="table-responsive">
            <table className="events-table">
              <thead>
                <tr>
                  <th>Event Name</th>
                  <th>Department(s)</th>
                  <th>Program(s)</th>
                  <th>Date & Time</th>
                  <th>Location</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.length > 0 ? (
                  filteredEvents.map((listedEvent) => (
                    <tr key={listedEvent.id}>
                      <td data-label="Event Name">{listedEvent.name}</td>
                      <td data-label="Department(s)">{formatEventDepartments(listedEvent.departments)}</td>
                      <td data-label="Program(s)">{formatEventPrograms(listedEvent.programs)}</td>
                      <td data-label="Date & Time">
                        {formatDateTime(listedEvent.start_datetime)} -{" "}
                        {formatDateTime(listedEvent.end_datetime)}
                      </td>
                      <td data-label="Location">{listedEvent.location}</td>
                      <td data-label="Status">
                        <span className={`status-badge ${listedEvent.status}`}>
                          {listedEvent.status.charAt(0).toUpperCase() + listedEvent.status.slice(1)}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="no-results">
                      No matching events found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Events;
