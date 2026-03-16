import type { GovernanceEventDefaults } from "../api/governanceHierarchyApi";
import type { SchoolSettings } from "../api/schoolSettingsApi";

export interface EventDefaultSettings {
  early_check_in_minutes: number;
  late_threshold_minutes: number;
  sign_out_grace_minutes: number;
}

export const FALLBACK_EVENT_DEFAULT_SETTINGS: EventDefaultSettings = {
  early_check_in_minutes: 30,
  late_threshold_minutes: 10,
  sign_out_grace_minutes: 20,
};

export const getSchoolEventDefaultSettings = (
  settings?: Pick<
    SchoolSettings,
    | "event_default_early_check_in_minutes"
    | "event_default_late_threshold_minutes"
    | "event_default_sign_out_grace_minutes"
  > | null
): EventDefaultSettings => ({
  early_check_in_minutes:
    settings?.event_default_early_check_in_minutes ??
    FALLBACK_EVENT_DEFAULT_SETTINGS.early_check_in_minutes,
  late_threshold_minutes:
    settings?.event_default_late_threshold_minutes ??
    FALLBACK_EVENT_DEFAULT_SETTINGS.late_threshold_minutes,
  sign_out_grace_minutes:
    settings?.event_default_sign_out_grace_minutes ??
    FALLBACK_EVENT_DEFAULT_SETTINGS.sign_out_grace_minutes,
});

export const getGovernanceEventDefaultSettings = (
  defaults?: Pick<
    GovernanceEventDefaults,
    | "effective_early_check_in_minutes"
    | "effective_late_threshold_minutes"
    | "effective_sign_out_grace_minutes"
  > | null
): EventDefaultSettings => ({
  early_check_in_minutes:
    defaults?.effective_early_check_in_minutes ??
    FALLBACK_EVENT_DEFAULT_SETTINGS.early_check_in_minutes,
  late_threshold_minutes:
    defaults?.effective_late_threshold_minutes ??
    FALLBACK_EVENT_DEFAULT_SETTINGS.late_threshold_minutes,
  sign_out_grace_minutes:
    defaults?.effective_sign_out_grace_minutes ??
    FALLBACK_EVENT_DEFAULT_SETTINGS.sign_out_grace_minutes,
});
