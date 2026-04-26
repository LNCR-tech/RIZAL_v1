import {
  normalizeGovernanceRequest,
  normalizeGovernanceSetting,
  normalizeNotificationLogItem,
  normalizeSchoolItAccount,
  normalizeSchoolSummary,
  normalizeUserWithRelations,
  normalizeAuditLogResponse,
} from '@/services/backendNormalizers.js'

function isoOffset({ days = 0, hours = 0, minutes = 0 }) {
  const date = new Date()
  date.setDate(date.getDate() + days)
  date.setHours(date.getHours() + hours)
  date.setMinutes(date.getMinutes() + minutes)
  return date.toISOString()
}

function createSchools() {
  return [
    normalizeSchoolSummary({
      school_id: 301,
      school_name: 'Jose Rizal Memorial State University',
      school_code: 'JRMSU',
      subscription_status: 'active',
      active_status: true,
      primary_color: '#AAFF00',
      secondary_color: '#64748B',
      logo_url: null,
      created_at: isoOffset({ days: -420 }),
      updated_at: isoOffset({ days: -2 }),
    }),
    normalizeSchoolSummary({
      school_id: 302,
      school_name: 'Western Bay State College',
      school_code: 'WBSC',
      subscription_status: 'trial',
      active_status: true,
      primary_color: '#38BDF8',
      secondary_color: '#0F172A',
      logo_url: null,
      created_at: isoOffset({ days: -190 }),
      updated_at: isoOffset({ days: -12 }),
    }),
    normalizeSchoolSummary({
      school_id: 303,
      school_name: 'North Valley Polytechnic Institute',
      school_code: 'NVPI',
      subscription_status: 'suspended',
      active_status: false,
      primary_color: '#F97316',
      secondary_color: '#7C2D12',
      logo_url: null,
      created_at: isoOffset({ days: -610 }),
      updated_at: isoOffset({ days: -25 }),
    }),
  ]
}

function createCampusAccounts() {
  return [
    normalizeSchoolItAccount({
      user_id: 9101,
      email: 'campusadmin@jrmsu.edu.ph',
      first_name: 'Rizalyn',
      last_name: 'Morales',
      school_id: 301,
      school_name: 'Jose Rizal Memorial State University',
      is_active: true,
    }),
    normalizeSchoolItAccount({
      user_id: 9102,
      email: 'operations@wbsc.edu.ph',
      first_name: 'Alden',
      last_name: 'Dela Cruz',
      school_id: 302,
      school_name: 'Western Bay State College',
      is_active: true,
    }),
    normalizeSchoolItAccount({
      user_id: 9103,
      email: 'admin@nvpi.edu.ph',
      first_name: 'Mae',
      last_name: 'Rosales',
      school_id: 303,
      school_name: 'North Valley Polytechnic Institute',
      is_active: false,
    }),
  ]
}

function createAuditLogs() {
  return normalizeAuditLogResponse({
    total: 5,
    items: [
      {
        id: 6001,
        school_id: 301,
        actor_user_id: 1,
        action: 'school_update',
        status: 'success',
        details_json: { school_name: 'Jose Rizal Memorial State University', logo_updated: true },
        created_at: isoOffset({ hours: -6 }),
      },
      {
        id: 6002,
        school_id: 302,
        actor_user_id: 1,
        action: 'school_status_update',
        status: 'success',
        details_json: { active_status: true, subscription_status: 'trial' },
        created_at: isoOffset({ days: -1, hours: -2 }),
      },
      {
        id: 6003,
        school_id: 301,
        actor_user_id: 9101,
        action: 'student_bulk_import_attempt',
        status: 'queued',
        details_json: { filename: 'students-batch.xlsx', rows: 142 },
        created_at: isoOffset({ days: -1, hours: -7 }),
      },
      {
        id: 6004,
        school_id: 303,
        actor_user_id: 1,
        action: 'school_it_status_update',
        status: 'success',
        details_json: { school_it_user_id: 9103, is_active: false },
        created_at: isoOffset({ days: -2 }),
      },
      {
        id: 6005,
        school_id: 302,
        actor_user_id: 1,
        action: 'school_it_password_reset',
        status: 'success',
        details_json: { school_it_user_id: 9102 },
        created_at: isoOffset({ days: -3 }),
      },
    ],
  })
}

function createNotificationLogs() {
  return [
    normalizeNotificationLogItem({
      id: 7101,
      school_id: 301,
      user_id: 441,
      category: 'low_attendance',
      channel: 'email',
      status: 'sent',
      subject: 'Low attendance alert',
      message: 'Attendance dropped below the configured threshold.',
      created_at: isoOffset({ hours: -10 }),
    }),
    normalizeNotificationLogItem({
      id: 7102,
      school_id: 302,
      user_id: 552,
      category: 'missed_events',
      channel: 'email',
      status: 'sent',
      subject: 'Missed event reminder',
      message: 'A student missed a scheduled event.',
      created_at: isoOffset({ days: -1 }),
    }),
    normalizeNotificationLogItem({
      id: 7103,
      school_id: 303,
      user_id: 9103,
      category: 'account_security',
      channel: 'email',
      status: 'failed',
      subject: 'Security notification',
      message: 'Please review the recent password reset request.',
      error_message: 'Mailbox unavailable',
      created_at: isoOffset({ days: -2 }),
    }),
  ]
}

function createGovernanceRequests() {
  return [
    normalizeGovernanceRequest({
      id: 8101,
      school_id: 301,
      requested_by_user_id: 441,
      target_user_id: 441,
      request_type: 'export',
      scope: 'user_data',
      status: 'pending',
      reason: 'Need a copy of my attendance data.',
      created_at: isoOffset({ hours: -18 }),
    }),
    normalizeGovernanceRequest({
      id: 8102,
      school_id: 302,
      requested_by_user_id: 552,
      target_user_id: 552,
      request_type: 'delete',
      scope: 'user_data',
      status: 'approved',
      reason: 'Please remove my inactive account data.',
      handled_by_user_id: 1,
      resolved_at: isoOffset({ days: -1, hours: -3 }),
      created_at: isoOffset({ days: -2 }),
    }),
  ]
}

function createGovernanceSettingsBySchool() {
  return {
    301: normalizeGovernanceSetting({
      school_id: 301,
      attendance_retention_days: 365,
      audit_log_retention_days: 730,
      import_file_retention_days: 45,
      auto_delete_enabled: false,
      updated_at: isoOffset({ days: -4 }),
    }),
    302: normalizeGovernanceSetting({
      school_id: 302,
      attendance_retention_days: 540,
      audit_log_retention_days: 730,
      import_file_retention_days: 30,
      auto_delete_enabled: true,
      updated_at: isoOffset({ days: -9 }),
    }),
    303: normalizeGovernanceSetting({
      school_id: 303,
      attendance_retention_days: 365,
      audit_log_retention_days: 365,
      import_file_retention_days: 21,
      auto_delete_enabled: false,
      updated_at: isoOffset({ days: -17 }),
    }),
  }
}

export function createAdminDashboardPreviewData() {
  return {
    user: normalizeUserWithRelations({
      id: 1,
      email: 'platform.admin@valid8.local',
      first_name: 'Platform',
      last_name: 'Admin',
      roles: [{ role: { id: 1, name: 'admin' } }],
      school_id: null,
      school_name: 'VALID8 Platform',
    }),
    schools: createSchools(),
    campusAccounts: createCampusAccounts(),
    auditLogs: createAuditLogs(),
    notificationLogs: createNotificationLogs(),
    governanceRequests: createGovernanceRequests(),
    governanceSettingsBySchool: createGovernanceSettingsBySchool(),
  }
}

export const adminDashboardPreviewData = createAdminDashboardPreviewData()
