<template>
  <section class="school-it-import">
    <div class="school-it-import__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-import__body">
        <section class="school-it-import__hero dashboard-enter dashboard-enter--2">
          <div class="school-it-import__hero-top">
            <div class="school-it-import__hero-copy">
              <span class="school-it-import__eyebrow">Campus Admin</span>
              <h1 class="school-it-import__title">Bulk Student Import</h1>
              <p class="school-it-import__subtitle">
                Upload the backend template, preview every row first, then queue only the approved students.
              </p>
            </div>

            <div class="school-it-import__hero-actions">
              <button
                class="school-it-import__button school-it-import__button--surface"
                type="button"
                :disabled="stage === 'processing'"
                @click="downloadTemplate"
              >
                <Download :size="16" />
                Download Template
              </button>

              <button
                v-if="stage !== 'idle' || selectedFile"
                class="school-it-import__button school-it-import__button--ghost"
                type="button"
                :disabled="stage === 'processing'"
                @click="resetFlow"
              >
                <RefreshCcw :size="16" />
                Reset Flow
              </button>
            </div>
          </div>

          <div class="school-it-import__step-grid">
            <article
              v-for="step in workflowSteps"
              :key="step.id"
              class="school-it-import__step"
              :class="[
                `school-it-import__step--${step.state}`,
              ]"
            >
              <span class="school-it-import__step-index">{{ step.index }}</span>
              <div class="school-it-import__step-copy">
                <p class="school-it-import__step-title">{{ step.label }}</p>
                <p class="school-it-import__step-detail">{{ step.detail }}</p>
              </div>
            </article>
          </div>
        </section>

        <div class="school-it-import__layout">
          <section class="school-it-import__workspace dashboard-enter dashboard-enter--3">
            <article class="school-it-import__panel school-it-import__panel--upload">
              <div class="school-it-import__panel-head">
                <div>
                  <p class="school-it-import__panel-kicker">Source File</p>
                  <h2 class="school-it-import__panel-title">
                    {{ selectedFile ? 'File Ready For Review' : 'Upload Student Spreadsheet' }}
                  </h2>
                  <p class="school-it-import__panel-copy">
                    {{ selectedFile ? fileStatusCopy : 'The backend accepts only .csv and .xlsx files with the exact template headers.' }}
                  </p>
                </div>

                <div class="school-it-import__panel-actions">
                  <button
                    class="school-it-import__button school-it-import__button--ghost"
                    type="button"
                    :disabled="stage === 'processing'"
                    @click="openFilePicker"
                  >
                    <Upload :size="16" />
                    {{ selectedFile ? 'Replace File' : 'Choose File' }}
                  </button>

                  <button
                    class="school-it-import__button school-it-import__button--primary"
                    type="button"
                    :disabled="isPrimaryActionDisabled"
                    @click="handlePrimaryAction"
                  >
                    <LoaderCircle
                      v-if="stage === 'processing'"
                      class="school-it-import__button-spinner"
                      :size="16"
                    />
                    <template v-else>
                      <ArrowRight :size="16" />
                    </template>
                    {{ primaryActionLabel }}
                  </button>
                </div>
              </div>

              <button
                v-if="!selectedFile"
                class="school-it-import__dropzone"
                :class="{ 'school-it-import__dropzone--active': isDragActive }"
                type="button"
                @click="openFilePicker"
                @dragenter.prevent="isDragActive = true"
                @dragover.prevent="isDragActive = true"
                @dragleave.prevent="isDragActive = false"
                @drop.prevent="handleFileDrop"
              >
                <CloudUpload class="school-it-import__dropzone-icon" :size="42" />
                <div class="school-it-import__dropzone-copy">
                  <p class="school-it-import__dropzone-title">Drop a CSV or XLSX file here</p>
                  <p class="school-it-import__dropzone-detail">
                    Preview is required before the backend will accept the import.
                  </p>
                </div>
              </button>

              <div v-else class="school-it-import__file-card">
                <div class="school-it-import__file-main">
                  <span class="school-it-import__file-icon">
                    <FileSpreadsheet :size="18" />
                  </span>

                  <div class="school-it-import__file-copy">
                    <p class="school-it-import__file-name">{{ selectedFile.name }}</p>
                    <p class="school-it-import__file-meta">
                      {{ selectedFileSizeLabel }} · {{ fileExtensionLabel }}
                    </p>
                  </div>
                </div>

                <div class="school-it-import__file-pills">
                  <span
                    class="school-it-import__status-pill"
                    :class="[`school-it-import__status-pill--${fileStatusTone}`]"
                  >
                    {{ fileStatusLabel }}
                  </span>
                  <span class="school-it-import__micro-pill">CSV / XLSX</span>
                  <span v-if="previewSummary" class="school-it-import__micro-pill">
                    {{ previewSummary.total_rows }} rows detected
                  </span>
                  <span v-if="importSummary?.job_id" class="school-it-import__micro-pill school-it-import__micro-pill--mono">
                    Job {{ importSummary.job_id }}
                  </span>
                </div>
              </div>
            </article>

            <p
              v-if="feedbackMessage"
              class="school-it-import__feedback"
              :class="{ 'school-it-import__feedback--error': feedbackError }"
            >
              {{ feedbackMessage }}
            </p>

            <section
              v-if="summaryCards.length"
              class="school-it-import__summary-grid"
            >
              <article
                v-for="card in summaryCards"
                :key="card.id"
                class="school-it-import__summary-card"
                :class="[`school-it-import__summary-card--${card.tone}`]"
              >
                <span class="school-it-import__summary-label">{{ card.label }}</span>
                <strong class="school-it-import__summary-value">{{ card.value }}</strong>
                <span class="school-it-import__summary-note">{{ card.note }}</span>
              </article>
            </section>

            <article
              v-if="stage === 'processing'"
              class="school-it-import__panel school-it-import__panel--processing"
            >
              <div class="school-it-import__processing-main">
                <span class="school-it-import__processing-icon">
                  <LoaderCircle :size="20" />
                </span>
                <div class="school-it-import__processing-copy">
                  <p class="school-it-import__processing-title">{{ processingLabel }}</p>
                  <p class="school-it-import__processing-detail">{{ processingStatusHint }}</p>
                </div>
              </div>

              <div class="school-it-import__progress-wrap" aria-hidden="true">
                <div class="school-it-import__progress-track">
                  <span
                    class="school-it-import__progress-fill"
                    :class="{ 'school-it-import__progress-fill--indeterminate': !hasDeterminateProgress }"
                    :style="hasDeterminateProgress ? { width: `${displayProgress}%` } : undefined"
                  />
                </div>
                <span class="school-it-import__progress-value">
                  {{ hasDeterminateProgress ? `${Math.round(displayProgress)}%` : 'Working' }}
                </span>
              </div>
            </article>

            <article
              v-else-if="stage === 'result'"
              class="school-it-import__panel school-it-import__panel--results"
            >
              <div class="school-it-import__result-head">
                <div>
                  <p class="school-it-import__panel-kicker">{{ resultKicker }}</p>
                  <h2 class="school-it-import__panel-title">{{ resultTitle }}</h2>
                  <p class="school-it-import__panel-copy">{{ resultSummary }}</p>
                </div>

                <div class="school-it-import__result-head-actions">
                  <button
                    v-if="showSecondaryAction"
                    class="school-it-import__button school-it-import__button--ghost"
                    type="button"
                    :disabled="stage === 'processing'"
                    @click="handleSecondaryAction"
                  >
                    {{ secondaryActionLabel }}
                  </button>
                </div>
              </div>

              <div
                v-if="showPreviewRepairActions || showImportErrorDownload || showRetryFailedRowsAction"
                class="school-it-import__result-actions"
              >
                <button
                  v-if="showPreviewRepairActions"
                  class="school-it-import__button school-it-import__button--surface"
                  type="button"
                  :disabled="stage === 'processing'"
                  @click="handleDownloadPreviewErrors"
                >
                  <Download :size="15" />
                  Download Errors
                </button>

                <button
                  v-if="showPreviewRepairActions"
                  class="school-it-import__button school-it-import__button--surface"
                  type="button"
                  :disabled="stage === 'processing'"
                  @click="handleDownloadPreviewRetryFile"
                >
                  <RefreshCcw :size="15" />
                  Retry File
                </button>

                <button
                  v-if="showPreviewRepairActions && canKeepValidRows"
                  class="school-it-import__button school-it-import__button--primary"
                  type="button"
                  :disabled="stage === 'processing'"
                  @click="handleKeepValidRows"
                >
                  <ShieldCheck :size="15" />
                  Keep Valid Rows
                </button>

                <button
                  v-if="showImportErrorDownload"
                  class="school-it-import__button school-it-import__button--surface"
                  type="button"
                  :disabled="stage === 'processing'"
                  @click="handleDownloadImportErrors"
                >
                  <Download :size="15" />
                  Download Failed Rows
                </button>

                <button
                  v-if="showRetryFailedRowsAction"
                  class="school-it-import__button school-it-import__button--primary"
                  type="button"
                  :disabled="stage === 'processing'"
                  @click="handleRetryFailedRows"
                >
                  <RefreshCcw :size="15" />
                  Retry Failed Rows
                </button>
              </div>

              <div v-if="displayRows.length" class="school-it-import__result-filter">
                <button
                  v-for="filter in rowFilters"
                  :key="filter.id"
                  class="school-it-import__filter-pill"
                  :class="{ 'school-it-import__filter-pill--active': rowFilter === filter.id }"
                  type="button"
                  @click="rowFilter = filter.id"
                >
                  {{ filter.label }}
                </button>
              </div>

              <div v-if="filteredDisplayRows.length" class="school-it-import__rows">
                <article
                  v-for="row in filteredDisplayRows"
                  :key="row.id"
                  class="school-it-import__row"
                  :class="{ 'school-it-import__row--issue': row.status !== 'valid' }"
                >
                  <div class="school-it-import__row-top">
                    <div class="school-it-import__row-copy">
                      <p class="school-it-import__row-name">{{ row.name }}</p>
                      <p class="school-it-import__row-id">{{ row.studentId || `Row ${row.row}` }}</p>
                    </div>

                    <span
                      class="school-it-import__status-pill"
                      :class="[`school-it-import__status-pill--${row.status === 'valid' ? 'ready' : 'issue'}`]"
                    >
                      {{ resolveRowStatusLabel(row) }}
                    </span>
                  </div>

                  <div class="school-it-import__row-meta">
                    <span>{{ row.department }}</span>
                    <span>{{ row.program }}</span>
                    <span>Row {{ row.row }}</span>
                  </div>

                  <p v-if="row.errors.length" class="school-it-import__row-error">
                    {{ row.errors[0] }}
                  </p>
                </article>
              </div>

              <p v-else class="school-it-import__empty">
                {{ emptyStateMessage }}
              </p>
            </article>

            <input
              ref="fileInputEl"
              class="school-it-import__file-input"
              type="file"
              accept=".xlsx,.csv"
              @change="handleFileSelect"
            >
          </section>

          <aside class="school-it-import__sidebar dashboard-enter dashboard-enter--4">
            <article class="school-it-import__side-card">
              <p class="school-it-import__panel-kicker">Backend Workflow</p>
              <h2 class="school-it-import__side-title">How this import works</h2>

              <ul class="school-it-import__side-list">
                <li>Template download uses the backend’s exact student-import headers.</li>
                <li>Preview validates the file first and returns a required `preview_token`.</li>
                <li>Import only starts after the frontend sends that `preview_token` back.</li>
                <li>Failed rows can be downloaded or re-queued without reimporting the whole batch.</li>
              </ul>
            </article>

            <article class="school-it-import__side-card">
              <p class="school-it-import__panel-kicker">Required Headers</p>
              <h2 class="school-it-import__side-title">Exact column names</h2>

              <div class="school-it-import__header-chips">
                <span
                  v-for="header in EXPECTED_HEADERS"
                  :key="header"
                  class="school-it-import__header-chip"
                >
                  {{ header }}
                </span>
              </div>
            </article>

            <article class="school-it-import__side-card">
              <p class="school-it-import__panel-kicker">Current Context</p>
              <h2 class="school-it-import__side-title">{{ sidebarContextTitle }}</h2>

              <div class="school-it-import__context-list">
                <div
                  v-for="item in sidebarContextItems"
                  :key="item.label"
                  class="school-it-import__context-item"
                >
                  <span class="school-it-import__context-label">{{ item.label }}</span>
                  <span
                    class="school-it-import__context-value"
                    :class="{ 'school-it-import__context-value--mono': item.mono }"
                  >
                    {{ item.value }}
                  </span>
                </div>
              </div>
            </article>
          </aside>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import {
  ArrowRight,
  CloudUpload,
  Download,
  FileSpreadsheet,
  LoaderCircle,
  RefreshCcw,
  ShieldCheck,
  Upload,
} from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import {
  BackendApiError,
  downloadImportErrors,
  downloadPreviewImportErrors,
  downloadPreviewRetryFile,
  downloadStudentImportTemplate,
  getAuditLogs,
  getStudentImportStatus,
  previewImportStudents,
  removeInvalidPreviewRows,
  retryFailedStudentImport,
  startStudentImport,
} from '@/services/backendApi.js'
import { downloadBlobFile } from '@/services/fileDownload.js'
import {
  createMockImportPreviewSummary,
  extractStudentImportDisplayRows,
  mergeImportStatusErrorsIntoDisplayRows,
} from '@/services/studentImport.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const POLL_INTERVAL_MS = 1200
const IMPORT_JOB_LOOKUP_ATTEMPTS = 10
const IMPORT_JOB_LOOKUP_INTERVAL_MS = 1200
const EXPECTED_HEADERS = [
  'Student_ID',
  'Email',
  'Last Name',
  'First Name',
  'Middle Name',
  'Department',
  'Course',
]

const fileInputEl = ref(null)
const isDragActive = ref(false)
const selectedFile = ref(null)
const stage = ref('idle')
const processingMode = ref('preview')
const processingLabel = ref('Preparing import preview...')
const displayProgress = ref(null)
const feedbackMessage = ref('')
const feedbackError = ref(false)
const previewSummary = ref(null)
const importSummary = ref(null)
const displayRows = ref([])
const rowFilter = ref('all')

let pollTimeoutId = 0

const { currentUser, schoolSettings, apiBaseUrl, token } = useDashboardSession()
const { logout } = useAuth()

const activeUser = computed(() => (props.preview ? schoolItPreviewData.user : currentUser.value))
const activeSchoolSettings = computed(() => (props.preview ? schoolItPreviewData.schoolSettings : schoolSettings.value))

usePreviewTheme(() => props.preview, activeSchoolSettings)

const displayName = computed(() => {
  const first = activeUser.value?.first_name || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'Campus Admin'
})

const initials = computed(() => buildInitials(displayName.value))
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const selectedFileSizeLabel = computed(() => formatFileSize(selectedFile.value?.size))
const fileExtensionLabel = computed(() => {
  const fileName = String(selectedFile.value?.name || '')
  const extension = fileName.includes('.') ? fileName.split('.').pop() : ''
  return extension ? extension.toUpperCase() : 'Spreadsheet'
})

const validDisplayRows = computed(() => displayRows.value.filter((row) => row.status === 'valid'))
const invalidDisplayRows = computed(() => displayRows.value.filter((row) => row.status !== 'valid'))
const issueFilterLabel = computed(() => importSummary.value ? 'Failed' : 'Needs Review')

const rowFilters = computed(() => ([
  {
    id: 'all',
    label: `All (${displayRows.value.length})`,
  },
  {
    id: 'issue',
    label: `${issueFilterLabel.value} (${invalidDisplayRows.value.length})`,
  },
  {
    id: 'ready',
    label: `${importSummary.value ? 'Imported' : 'Ready'} (${validDisplayRows.value.length})`,
  },
]))

const filteredDisplayRows = computed(() => {
  const rows = [...displayRows.value].sort((left, right) => {
    const leftIssue = left.status === 'valid' ? 1 : 0
    const rightIssue = right.status === 'valid' ? 1 : 0
    if (leftIssue !== rightIssue) return leftIssue - rightIssue
    return Number(left.row || 0) - Number(right.row || 0)
  })

  if (rowFilter.value === 'issue') {
    return rows.filter((row) => row.status !== 'valid')
  }

  if (rowFilter.value === 'ready') {
    return rows.filter((row) => row.status === 'valid')
  }

  return rows
})

const canKeepValidRows = computed(() => (
  validDisplayRows.value.length > 0
  && invalidDisplayRows.value.length > 0
  && Boolean(previewSummary.value?.preview_token)
))

const showPreviewRepairActions = computed(() => (
  stage.value === 'result'
  && !importSummary.value
  && Boolean(previewSummary.value?.preview_token)
  && invalidDisplayRows.value.length > 0
))

const showImportErrorDownload = computed(() => (
  stage.value === 'result'
  && Number(importSummary.value?.failed_count || 0) > 0
  && Boolean(importSummary.value?.job_id)
))

const showRetryFailedRowsAction = computed(() => (
  !props.preview
  && stage.value === 'result'
  && Number(importSummary.value?.failed_count || 0) > 0
  && Boolean(importSummary.value?.job_id)
))

const hasDeterminateProgress = computed(() => Number.isFinite(Number(displayProgress.value)))

const primaryActionLabel = computed(() => {
  if (!selectedFile.value) return 'Choose File'
  if (stage.value === 'processing') return 'Processing'
  if (stage.value === 'idle') return 'Preview File'
  if (stage.value === 'result' && !importSummary.value && previewSummary.value?.can_commit) return 'Start Import'
  if (stage.value === 'result' && !importSummary.value && !previewSummary.value?.can_commit) return 'Replace File'
  return 'Import Another File'
})

const isPrimaryActionDisabled = computed(() => {
  if (stage.value === 'processing') return true
  if (!selectedFile.value) return false
  return false
})

const showSecondaryAction = computed(() => (
  stage.value !== 'processing'
  && (Boolean(selectedFile.value) || stage.value === 'result')
))

const secondaryActionLabel = computed(() => {
  if (stage.value === 'idle') return 'Clear File'
  if (importSummary.value) return 'Start Over'
  return 'Choose Another File'
})

const resultKicker = computed(() => {
  if (importSummary.value?.state === 'completed') return 'Import Finished'
  if (importSummary.value?.state === 'failed') return 'Import Requires Review'
  return 'Preview Results'
})

const resultTitle = computed(() => {
  if (importSummary.value?.state === 'completed' && Number(importSummary.value?.failed_count || 0) <= 0) {
    return 'Students Imported'
  }

  if (importSummary.value?.state === 'completed') {
    return 'Import Completed With Failed Rows'
  }

  if (importSummary.value?.state === 'failed') {
    return 'Import Stopped With Issues'
  }

  if (invalidDisplayRows.value.length > 0) {
    return 'Preview Needs Attention'
  }

  return 'Preview Ready To Import'
})

const resultSummary = computed(() => {
  if (importSummary.value) {
    const processedRows = Number(importSummary.value?.processed_rows || 0)
    const totalRows = Number(importSummary.value?.total_rows || 0)
    const successCount = Number(importSummary.value?.success_count || 0)
    const failedCount = Number(importSummary.value?.failed_count || 0)
    return `${successCount} imported, ${failedCount} failed, ${processedRows}/${totalRows || processedRows} processed.`
  }

  if (!previewSummary.value) {
    return 'Upload a file to start the student import preview.'
  }

  return `${previewSummary.value.valid_rows} ready, ${previewSummary.value.invalid_rows} flagged from ${previewSummary.value.filename || 'the selected file'}.`
})

const processingStatusHint = computed(() => {
  if (stage.value !== 'processing') return ''

  if (processingMode.value === 'preview') {
    return 'Checking file type, header order, and row-level validation rules from the backend import service.'
  }

  if (processingMode.value === 'retry') {
    return 'Re-queuing only the backend rows that previously failed.'
  }

  const summary = importSummary.value
  const approvedRows = Number(previewSummary.value?.valid_rows || previewSummary.value?.total_rows || 0)
  const totalRows = Number(summary?.total_rows || 0)
  const processedRows = Number(summary?.processed_rows || 0)
  const etaSeconds = Number(summary?.estimated_time_remaining_seconds)
  const hasEta = Number.isFinite(etaSeconds) && etaSeconds > 0

  if (!summary?.job_id) {
    return approvedRows > 0
      ? `${approvedRows} approved rows are being handed to the backend import worker.`
      : 'The backend is preparing the import job.'
  }

  if (summary.state === 'pending' || summary.state === 'queued') {
    return approvedRows > 0
      ? `${approvedRows} approved rows are queued. Waiting for the worker to start.`
      : 'Waiting for the worker to start.'
  }

  if (summary.state === 'processing' && totalRows > 0) {
    const etaLabel = hasEta ? ` Estimated time left: ${formatEtaSeconds(etaSeconds)}.` : ''
    return `${processedRows}/${totalRows} rows processed.${etaLabel}`
  }

  return 'Processing the current import job.'
})

const fileStatusLabel = computed(() => {
  if (!selectedFile.value) return 'No File'
  if (stage.value === 'processing' && processingMode.value === 'preview') return 'Previewing'
  if (stage.value === 'processing' && processingMode.value === 'retry') return 'Retrying Failed Rows'
  if (stage.value === 'processing') return 'Importing'
  if (importSummary.value?.state === 'completed' && Number(importSummary.value?.failed_count || 0) <= 0) return 'Imported'
  if (importSummary.value?.state === 'completed') return 'Imported With Issues'
  if (importSummary.value?.state === 'failed') return 'Import Failed'
  if (previewSummary.value && invalidDisplayRows.value.length > 0) return 'Needs Review'
  if (previewSummary.value?.can_commit) return 'Ready To Import'
  return 'File Selected'
})

const fileStatusTone = computed(() => {
  if (!selectedFile.value) return 'neutral'
  if (stage.value === 'processing') return 'active'
  if (importSummary.value?.state === 'failed' || invalidDisplayRows.value.length > 0) return 'issue'
  if (previewSummary.value || importSummary.value?.state === 'completed') return 'ready'
  return 'neutral'
})

const fileStatusCopy = computed(() => {
  if (importSummary.value) {
    return 'The current file has already been previewed and sent to the backend import queue.'
  }

  if (previewSummary.value?.can_commit) {
    return 'Preview passed. You can start the import job or replace the file.'
  }

  if (previewSummary.value && invalidDisplayRows.value.length > 0) {
    return 'Preview found rows that need correction before import.'
  }

  return 'Review the selected file before sending it to the backend.'
})

const summaryCards = computed(() => {
  if (importSummary.value) {
    return [
      {
        id: 'imported',
        label: 'Imported',
        value: Number(importSummary.value?.success_count || 0),
        note: 'Rows successfully created as students.',
        tone: 'ready',
      },
      {
        id: 'failed',
        label: 'Failed',
        value: Number(importSummary.value?.failed_count || 0),
        note: 'Rows the backend rejected during import.',
        tone: Number(importSummary.value?.failed_count || 0) > 0 ? 'issue' : 'neutral',
      },
      {
        id: 'processed',
        label: 'Processed',
        value: `${Number(importSummary.value?.processed_rows || 0)}/${Number(importSummary.value?.total_rows || 0) || Number(importSummary.value?.processed_rows || 0)}`,
        note: 'Worker progress reported by the backend.',
        tone: 'neutral',
      },
    ]
  }

  if (previewSummary.value) {
    return [
      {
        id: 'rows',
        label: 'Rows Detected',
        value: Number(previewSummary.value?.total_rows || 0),
        note: 'Rows parsed from the uploaded file.',
        tone: 'neutral',
      },
      {
        id: 'ready',
        label: 'Ready',
        value: Number(previewSummary.value?.valid_rows || 0),
        note: 'Rows approved for import.',
        tone: 'ready',
      },
      {
        id: 'review',
        label: 'Needs Review',
        value: Number(previewSummary.value?.invalid_rows || 0),
        note: 'Rows blocked by validation errors.',
        tone: Number(previewSummary.value?.invalid_rows || 0) > 0 ? 'issue' : 'neutral',
      },
    ]
  }

  if (selectedFile.value) {
    return [
      {
        id: 'headers',
        label: 'Template Columns',
        value: EXPECTED_HEADERS.length,
        note: 'The backend checks exact header names.',
        tone: 'neutral',
      },
      {
        id: 'formats',
        label: 'Accepted Files',
        value: 'CSV / XLSX',
        note: 'Other formats are rejected before preview.',
        tone: 'neutral',
      },
      {
        id: 'flow',
        label: 'Import Mode',
        value: 'Preview First',
        note: 'A preview token is required before import.',
        tone: 'active',
      },
    ]
  }

  return []
})

const workflowSteps = computed(() => {
  const steps = [
    { id: 'template', index: '01', label: 'Template', detail: 'Use the exact backend column names.' },
    { id: 'preview', index: '02', label: 'Preview', detail: 'Validate rows before import.' },
    { id: 'queue', index: '03', label: 'Queue', detail: 'Send the preview token to import.' },
    { id: 'finish', index: '04', label: 'Finish', detail: 'Review or retry failed rows.' },
  ]

  let activeIndex = 0
  let completeThrough = -1

  if (selectedFile.value) {
    activeIndex = 1
    completeThrough = 0
  }

  if (stage.value === 'processing' && processingMode.value === 'preview') {
    activeIndex = 1
    completeThrough = 0
  } else if (previewSummary.value && !importSummary.value) {
    completeThrough = 1
    activeIndex = previewSummary.value.can_commit ? 2 : 3
  }

  if (stage.value === 'processing' && ['import', 'retry'].includes(processingMode.value)) {
    activeIndex = 2
    completeThrough = 1
  }

  if (importSummary.value) {
    completeThrough = 2
    activeIndex = 3
  }

  return steps.map((step, index) => ({
    ...step,
    state: index <= completeThrough ? 'done' : index === activeIndex ? 'active' : 'pending',
  }))
})

const sidebarContextTitle = computed(() => {
  if (importSummary.value?.job_id) return 'Live Import Status'
  if (previewSummary.value?.preview_token) return 'Preview Ready'
  if (selectedFile.value) return 'Selected File'
  return 'Waiting For File'
})

const sidebarContextItems = computed(() => {
  if (importSummary.value?.job_id) {
    return [
      {
        label: 'Job ID',
        value: importSummary.value.job_id,
        mono: true,
      },
      {
        label: 'State',
        value: String(importSummary.value?.state || 'queued').replace(/_/g, ' '),
      },
      {
        label: 'Failed Rows',
        value: Number(importSummary.value?.failed_count || 0),
      },
    ]
  }

  if (previewSummary.value?.preview_token) {
    return [
      {
        label: 'Preview Token',
        value: previewSummary.value.preview_token,
        mono: true,
      },
      {
        label: 'Can Commit',
        value: previewSummary.value.can_commit ? 'Yes' : 'No',
      },
      {
        label: 'Detected Rows',
        value: Number(previewSummary.value?.total_rows || 0),
      },
    ]
  }

  if (selectedFile.value) {
    return [
      {
        label: 'Filename',
        value: selectedFile.value.name,
      },
      {
        label: 'Size',
        value: selectedFileSizeLabel.value,
      },
      {
        label: 'Next Action',
        value: 'Preview file',
      },
    ]
  }

  return [
    {
      label: 'Accepted Files',
      value: 'CSV, XLSX',
    },
    {
      label: 'Required Flow',
      value: 'Preview first',
    },
    {
      label: 'Access',
      value: 'Campus Admin / Admin',
    },
  ]
})

const emptyStateMessage = computed(() => {
  if (importSummary.value) {
    return 'No preview rows are available for this import result.'
  }

  return 'No students could be resolved from this file.'
})

onBeforeUnmount(() => {
  clearPollTimer()
})

function buildInitials(value) {
  const parts = String(value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  }
  return String(value || '').slice(0, 2).toUpperCase()
}

function formatEtaSeconds(totalSeconds) {
  const normalized = Math.max(0, Math.round(Number(totalSeconds) || 0))
  if (normalized < 60) return `${normalized}s`

  const minutes = Math.floor(normalized / 60)
  const seconds = normalized % 60
  if (!seconds) return `${minutes}m`
  return `${minutes}m ${seconds}s`
}

function formatFileSize(sizeInBytes) {
  const size = Number(sizeInBytes)
  if (!Number.isFinite(size) || size <= 0) return '0 KB'
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function openFilePicker() {
  if (stage.value === 'processing') return
  fileInputEl.value?.click()
}

function handleFileSelect(event) {
  const file = event?.target?.files?.[0] || null
  commitSelectedFile(file)
  if (event?.target) event.target.value = ''
}

function handleFileDrop(event) {
  isDragActive.value = false
  const file = event?.dataTransfer?.files?.[0] || null
  commitSelectedFile(file)
}

function commitSelectedFile(file) {
  feedbackMessage.value = ''
  feedbackError.value = false
  previewSummary.value = null
  importSummary.value = null
  displayRows.value = []
  rowFilter.value = 'all'
  displayProgress.value = null
  processingMode.value = 'preview'
  stage.value = 'idle'

  if (!file) {
    selectedFile.value = null
    return
  }

  const normalizedName = String(file.name || '').toLowerCase()
  if (!normalizedName.endsWith('.xlsx') && !normalizedName.endsWith('.csv')) {
    selectedFile.value = null
    feedbackError.value = true
    feedbackMessage.value = 'Only .xlsx and .csv files are allowed.'
    return
  }

  selectedFile.value = file
  feedbackMessage.value = 'File ready. Run preview before importing.'
}

async function handlePrimaryAction() {
  if (!selectedFile.value) {
    openFilePicker()
    return
  }

  if (stage.value === 'processing') return

  if (stage.value === 'idle') {
    await runPreviewFlow()
    return
  }

  if (stage.value === 'result' && !importSummary.value) {
    if (previewSummary.value?.can_commit) {
      await runImportFlow()
      return
    }

    openFilePicker()
    return
  }

  resetFlow()
  await nextTick()
  openFilePicker()
}

function handleSecondaryAction() {
  if (stage.value === 'idle') {
    resetFlow()
    return
  }

  if (!importSummary.value) {
    openFilePicker()
    return
  }

  resetFlow()
}

function resolveRowStatusLabel(row) {
  if (row.status === 'valid') {
    return importSummary.value ? 'Imported' : 'Ready'
  }

  return importSummary.value ? 'Failed' : 'Needs Review'
}

async function downloadTemplate() {
  if (props.preview) {
    feedbackError.value = false
    feedbackMessage.value = 'Template download is available when connected to the backend.'
    return
  }

  try {
    const blob = await downloadStudentImportTemplate(apiBaseUrl.value, token.value)
    await downloadBlobFile(blob, 'student_import_template.xlsx', {
      title: 'Student import template',
    })
  } catch (error) {
    feedbackError.value = true
    feedbackMessage.value = resolveImportErrorMessage(error)
  }
}

async function runPreviewFlow() {
  if (!selectedFile.value) return

  stage.value = 'processing'
  processingMode.value = 'preview'
  processingLabel.value = 'Previewing uploaded file...'
  displayProgress.value = null
  feedbackMessage.value = ''
  feedbackError.value = false

  try {
    const summary = props.preview
      ? await runMockPreview(selectedFile.value)
      : await previewImportStudents(apiBaseUrl.value, token.value, selectedFile.value)

    previewSummary.value = summary
    importSummary.value = null
    displayRows.value = extractStudentImportDisplayRows(summary)
    rowFilter.value = summary.invalid_rows > 0 ? 'issue' : 'all'
    stage.value = 'result'

    if (summary.can_commit) {
      feedbackError.value = false
      feedbackMessage.value = 'Preview passed. The backend is ready to accept this import.'
    } else {
      feedbackError.value = true
      feedbackMessage.value = 'Preview found rows that need correction before import.'
    }
  } catch (error) {
    stage.value = 'idle'
    feedbackError.value = true
    feedbackMessage.value = resolveImportErrorMessage(error)
  }
}

async function runImportFlow() {
  if (!previewSummary.value?.preview_token) {
    feedbackError.value = true
    feedbackMessage.value = 'Preview token missing. Preview the file again before importing.'
    return
  }

  stage.value = 'processing'
  processingMode.value = 'import'
  processingLabel.value = 'Queuing student import...'
  displayProgress.value = 0
  feedbackMessage.value = ''
  feedbackError.value = false

  try {
    let finalSummary = null

    if (props.preview) {
      finalSummary = await runMockImport(previewSummary.value)
    } else {
      const jobId = await resolveImportJobId(previewSummary.value.preview_token)
      importSummary.value = {
        job_id: jobId,
        state: 'pending',
        total_rows: Number(previewSummary.value?.valid_rows || previewSummary.value?.total_rows || 0),
        processed_rows: 0,
        success_count: 0,
        failed_count: 0,
        percentage_completed: 0,
        errors: [],
      }

      finalSummary = await pollImportJob(jobId)
    }

    importSummary.value = finalSummary
    displayRows.value = mergeImportStatusErrorsIntoDisplayRows(
      extractStudentImportDisplayRows(previewSummary.value),
      finalSummary
    )
    rowFilter.value = Number(finalSummary?.failed_count || 0) > 0 ? 'issue' : 'all'
    stage.value = 'result'

    if (Number(finalSummary?.failed_count || 0) > 0) {
      feedbackError.value = true
      feedbackMessage.value = 'Import finished, but some rows failed. Download or retry the failed rows below.'
    } else {
      feedbackError.value = false
      feedbackMessage.value = 'Student import completed successfully.'
    }
  } catch (error) {
    stage.value = 'result'
    feedbackError.value = true
    feedbackMessage.value = resolveImportErrorMessage(error)
  }
}

async function handleRetryFailedRows() {
  if (props.preview || !importSummary.value?.job_id) return

  stage.value = 'processing'
  processingMode.value = 'retry'
  processingLabel.value = 'Retrying failed rows...'
  displayProgress.value = 0
  feedbackMessage.value = ''
  feedbackError.value = false

  try {
    const response = await retryFailedStudentImport(apiBaseUrl.value, token.value, importSummary.value.job_id)
    const retryJobId = String(response?.job_id || importSummary.value.job_id)
    importSummary.value = {
      ...importSummary.value,
      job_id: retryJobId,
      state: response?.status || 'pending',
      processed_rows: 0,
      success_count: 0,
      failed_count: 0,
      percentage_completed: 0,
      errors: [],
    }

    const finalSummary = await pollImportJob(retryJobId)
    importSummary.value = finalSummary
    displayRows.value = mergeImportStatusErrorsIntoDisplayRows(
      extractStudentImportDisplayRows(previewSummary.value),
      finalSummary
    )
    rowFilter.value = Number(finalSummary?.failed_count || 0) > 0 ? 'issue' : 'all'
    stage.value = 'result'

    if (Number(finalSummary?.failed_count || 0) > 0) {
      feedbackError.value = true
      feedbackMessage.value = 'Retry finished, but some rows still failed.'
    } else {
      feedbackError.value = false
      feedbackMessage.value = 'All previously failed rows were imported successfully.'
    }
  } catch (error) {
    stage.value = 'result'
    feedbackError.value = true
    feedbackMessage.value = resolveImportErrorMessage(error)
  }
}

async function handleDownloadPreviewErrors() {
  if (props.preview || !previewSummary.value?.preview_token) return

  try {
    const blob = await downloadPreviewImportErrors(apiBaseUrl.value, token.value, previewSummary.value.preview_token)
    await downloadBlobFile(blob, `preview_${previewSummary.value.preview_token}_errors.xlsx`, {
      title: 'Preview import errors',
    })
  } catch (error) {
    feedbackError.value = true
    feedbackMessage.value = resolveImportErrorMessage(error)
  }
}

async function handleDownloadPreviewRetryFile() {
  if (props.preview || !previewSummary.value?.preview_token) return

  try {
    const blob = await downloadPreviewRetryFile(apiBaseUrl.value, token.value, previewSummary.value.preview_token)
    await downloadBlobFile(blob, `preview_retry_${previewSummary.value.preview_token}.xlsx`, {
      title: 'Preview retry file',
    })
  } catch (error) {
    feedbackError.value = true
    feedbackMessage.value = resolveImportErrorMessage(error)
  }
}

async function handleKeepValidRows() {
  if (props.preview || !previewSummary.value?.preview_token || !canKeepValidRows.value) return

  stage.value = 'processing'
  processingMode.value = 'preview'
  processingLabel.value = 'Keeping valid rows from preview...'
  displayProgress.value = null
  feedbackMessage.value = ''
  feedbackError.value = false

  try {
    const cleanedPreview = await removeInvalidPreviewRows(apiBaseUrl.value, token.value, previewSummary.value.preview_token)
    previewSummary.value = cleanedPreview
    displayRows.value = extractStudentImportDisplayRows(cleanedPreview)
    rowFilter.value = 'all'
    stage.value = 'result'
    feedbackError.value = false
    feedbackMessage.value = 'Invalid rows were removed. The remaining rows are ready to import.'
  } catch (error) {
    stage.value = 'result'
    feedbackError.value = true
    feedbackMessage.value = resolveImportErrorMessage(error)
  }
}

async function handleDownloadImportErrors() {
  if (props.preview || !importSummary.value?.job_id) return

  try {
    const blob = await downloadImportErrors(apiBaseUrl.value, token.value, importSummary.value.job_id)
    await downloadBlobFile(blob, `import_${importSummary.value.job_id}_failed_rows.xlsx`, {
      title: 'Import failed rows',
    })
  } catch (error) {
    feedbackError.value = true
    feedbackMessage.value = resolveImportErrorMessage(error)
  }
}

async function runMockPreview(file) {
  await wait(500)

  return createMockImportPreviewSummary({
    fileName: file?.name || 'student_import_template.xlsx',
    users: schoolItPreviewData.users,
    departments: schoolItPreviewData.departments,
    programs: schoolItPreviewData.programs,
  })
}

async function runMockImport(preview) {
  displayProgress.value = 78
  await wait(900)

  return {
    job_id: `preview-${Date.now()}`,
    state: 'completed',
    total_rows: preview.total_rows,
    processed_rows: preview.total_rows,
    success_count: preview.valid_rows,
    failed_count: 0,
    percentage_completed: 100,
    estimated_time_remaining_seconds: 0,
    errors: [],
    failed_report_download_url: '',
  }
}

function createAsyncTracker(promise) {
  const tracker = {
    status: 'pending',
    value: null,
    error: null,
  }

  tracker.promise = Promise.resolve(promise)
    .then((value) => {
      tracker.status = 'fulfilled'
      tracker.value = value
      return value
    })
    .catch((error) => {
      tracker.status = 'rejected'
      tracker.error = error
      return null
    })

  return tracker
}

async function findQueuedImportJobByPreviewToken(previewToken, startedAtIso) {
  const actorUserId = Number(activeUser.value?.id || currentUser.value?.id)
  if (!previewToken || !Number.isFinite(actorUserId)) return null

  const response = await getAuditLogs(apiBaseUrl.value, token.value, {
    action: 'student_bulk_import_attempt',
    actor_user_id: actorUserId,
    q: previewToken,
    start_date: startedAtIso,
    limit: 20,
  }).catch(() => null)

  const items = Array.isArray(response?.items) ? response.items : []
  const match = items.find((item) => {
    const details = item?.details_json
    return details?.preview_token === previewToken && details?.job_id
  })

  return match?.details_json?.job_id ? String(match.details_json.job_id) : null
}

async function resolveImportJobId(previewToken) {
  const startedAtIso = new Date(Date.now() - 5000).toISOString()
  const requestTracker = createAsyncTracker(
    startStudentImport(apiBaseUrl.value, token.value, previewToken)
  )

  for (let attempt = 0; attempt < IMPORT_JOB_LOOKUP_ATTEMPTS; attempt += 1) {
    if (requestTracker.status === 'fulfilled' && requestTracker.value?.job_id) {
      return String(requestTracker.value.job_id)
    }

    const recoveredJobId = await findQueuedImportJobByPreviewToken(previewToken, startedAtIso)
    if (recoveredJobId) {
      return recoveredJobId
    }

    if (requestTracker.status === 'rejected') {
      break
    }

    await wait(IMPORT_JOB_LOOKUP_INTERVAL_MS)
  }

  await requestTracker.promise

  if (requestTracker.status === 'fulfilled' && requestTracker.value?.job_id) {
    return String(requestTracker.value.job_id)
  }

  const recoveredJobId = await findQueuedImportJobByPreviewToken(previewToken, startedAtIso)
  if (recoveredJobId) {
    return recoveredJobId
  }

  throw requestTracker.error || new BackendApiError('Import job could not be queued.')
}

async function pollImportJob(jobId) {
  clearPollTimer()

  for (let attempt = 0; attempt < 120; attempt += 1) {
    const summary = await getStudentImportStatus(apiBaseUrl.value, token.value, jobId)
    importSummary.value = summary

    if (summary.state === 'pending' || summary.state === 'queued') {
      processingLabel.value = 'Queued import job. Waiting for worker...'
    } else if (Number(summary.total_rows) > 0) {
      processingLabel.value = `Importing students... ${summary.processed_rows}/${summary.total_rows}`
    } else {
      processingLabel.value = 'Importing students...'
    }

    if (summary.state === 'completed') {
      displayProgress.value = 100
    } else if (Number.isFinite(Number(summary.percentage_completed))) {
      displayProgress.value = Math.max(0, Math.min(99, Number(summary.percentage_completed)))
    } else {
      displayProgress.value = null
    }

    if (summary.state === 'completed' || summary.state === 'failed') {
      return summary
    }

    await wait(POLL_INTERVAL_MS)
  }

  throw new BackendApiError('Import is taking longer than expected. Please try again in a moment.')
}

function clearPollTimer() {
  if (pollTimeoutId) {
    window.clearTimeout(pollTimeoutId)
    pollTimeoutId = 0
  }
}

function wait(ms) {
  return new Promise((resolve) => {
    clearPollTimer()
    pollTimeoutId = window.setTimeout(() => {
      pollTimeoutId = 0
      resolve()
    }, ms)
  })
}

function resetFlow() {
  clearPollTimer()
  selectedFile.value = null
  if (fileInputEl.value) fileInputEl.value.value = ''
  stage.value = 'idle'
  processingMode.value = 'preview'
  processingLabel.value = 'Preparing import preview...'
  displayProgress.value = null
  previewSummary.value = null
  importSummary.value = null
  displayRows.value = []
  rowFilter.value = 'all'
  feedbackMessage.value = ''
  feedbackError.value = false
  isDragActive.value = false
}

function resolveImportErrorMessage(error) {
  if (!(error instanceof BackendApiError)) {
    return error?.message || 'Unable to process this import right now.'
  }

  if (error.status === 400) {
    if (/preview_token/i.test(String(error.message || ''))) {
      return 'The backend requires a valid preview token before import. Preview the file again first.'
    }
    return error.message || 'The uploaded file failed backend validation.'
  }

  if (error.status === 401) {
    return 'Session expired. Please log in again.'
  }

  if (error.status === 403) {
    return 'This session is not allowed to import students right now.'
  }

  if (error.status === 413) {
    return error.message || 'The uploaded file is too large.'
  }

  if (error.status === 422) {
    return error.message || 'The backend rejected one or more import fields.'
  }

  if (error.status === 429) {
    return 'Too many import requests. Please wait before trying again.'
  }

  return error.message || 'Unable to process this import right now.'
}

async function handleLogout() {
  await logout()
}
</script>

<style scoped>
.school-it-import {
  min-height: 100vh;
  padding: 32px 28px 72px;
  font-family: 'Manrope', sans-serif;
}

.school-it-import__shell {
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
}

.school-it-import__body {
  display: flex;
  flex-direction: column;
  gap: 22px;
  margin-top: 24px;
}

.school-it-import__hero,
.school-it-import__panel,
.school-it-import__side-card {
  border-radius: 34px;
  background: var(--color-surface);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.school-it-import__hero {
  padding: 28px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 18%, transparent) 0, transparent 38%),
    linear-gradient(145deg, var(--color-surface) 0%, color-mix(in srgb, var(--color-surface) 86%, var(--color-bg)) 100%);
  border: 1px solid color-mix(in srgb, var(--color-surface-border) 60%, transparent);
}

.school-it-import__hero-top,
.school-it-import__panel-head,
.school-it-import__result-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.school-it-import__hero-copy,
.school-it-import__panel-head > div:first-child,
.school-it-import__result-head > div:first-child {
  min-width: 0;
}

.school-it-import__eyebrow,
.school-it-import__panel-kicker,
.school-it-import__summary-label,
.school-it-import__context-label {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.school-it-import__title,
.school-it-import__panel-title,
.school-it-import__side-title {
  margin: 0;
  color: var(--color-text-primary);
  letter-spacing: -0.05em;
}

.school-it-import__title {
  margin-top: 8px;
  font-size: clamp(30px, 5vw, 50px);
  line-height: 0.92;
  font-weight: 800;
}

.school-it-import__subtitle,
.school-it-import__panel-copy,
.school-it-import__step-detail,
.school-it-import__summary-note,
.school-it-import__processing-detail,
.school-it-import__empty,
.school-it-import__side-list,
.school-it-import__context-value {
  margin: 0;
  color: var(--color-text-secondary);
}

.school-it-import__subtitle {
  max-width: 58ch;
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.55;
}

.school-it-import__hero-actions,
.school-it-import__panel-actions,
.school-it-import__result-actions,
.school-it-import__result-head-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.school-it-import__step-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 24px;
}

.school-it-import__step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border-radius: 24px;
  border: 1px solid color-mix(in srgb, var(--color-surface-border) 70%, transparent);
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
}

.school-it-import__step--active {
  background: color-mix(in srgb, var(--color-primary) 12%, white);
  border-color: color-mix(in srgb, var(--color-primary) 28%, transparent);
}

.school-it-import__step--done {
  background: color-mix(in srgb, #14b86a 9%, white);
  border-color: color-mix(in srgb, #14b86a 24%, transparent);
}

.school-it-import__step-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  font-size: 11px;
  font-weight: 800;
  flex-shrink: 0;
}

.school-it-import__step-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.school-it-import__step-title,
.school-it-import__dropzone-title,
.school-it-import__file-name,
.school-it-import__processing-title,
.school-it-import__row-name {
  margin: 0;
  color: var(--color-text-primary);
  font-weight: 800;
}

.school-it-import__step-title {
  font-size: 14px;
  line-height: 1.1;
}

.school-it-import__step-detail {
  font-size: 12px;
  line-height: 1.45;
}

.school-it-import__layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.82fr);
  gap: 22px;
  align-items: start;
}

.school-it-import__workspace,
.school-it-import__sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.school-it-import__panel,
.school-it-import__side-card {
  padding: 24px;
}

.school-it-import__dropzone {
  width: 100%;
  min-height: 220px;
  margin-top: 20px;
  padding: 26px;
  border: 1.5px dashed color-mix(in srgb, var(--color-primary) 32%, transparent);
  border-radius: 30px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--color-primary) 6%, white) 0%, transparent 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  text-align: center;
  transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.24s ease;
}

.school-it-import__dropzone--active {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--color-primary) 56%, transparent);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
}

.school-it-import__dropzone-icon {
  color: var(--color-primary);
}

.school-it-import__dropzone-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 34ch;
}

.school-it-import__dropzone-title {
  font-size: 20px;
  line-height: 1.05;
}

.school-it-import__dropzone-detail,
.school-it-import__file-meta,
.school-it-import__row-id,
.school-it-import__row-meta {
  margin: 0;
  color: var(--color-text-secondary);
}

.school-it-import__dropzone-detail,
.school-it-import__file-meta,
.school-it-import__processing-detail,
.school-it-import__row-id {
  font-size: 13px;
  line-height: 1.45;
}

.school-it-import__file-card {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 20px;
  padding: 18px;
  border-radius: 28px;
  background: color-mix(in srgb, var(--color-surface) 84%, var(--color-bg));
}

.school-it-import__file-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.school-it-import__file-icon,
.school-it-import__processing-icon {
  width: 42px;
  height: 42px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-primary) 18%, white);
  color: var(--color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.school-it-import__file-copy {
  min-width: 0;
}

.school-it-import__file-name {
  font-size: 15px;
  line-height: 1.1;
  word-break: break-word;
}

.school-it-import__file-pills,
.school-it-import__header-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.school-it-import__status-pill,
.school-it-import__micro-pill,
.school-it-import__filter-pill,
.school-it-import__header-chip {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.school-it-import__status-pill {
  background: color-mix(in srgb, var(--color-surface) 74%, var(--color-bg));
  color: var(--color-text-primary);
}

.school-it-import__status-pill--active {
  background: color-mix(in srgb, #2f7bff 16%, white);
  color: #1755c2;
}

.school-it-import__status-pill--ready {
  background: color-mix(in srgb, #14b86a 16%, white);
  color: #0f8a50;
}

.school-it-import__status-pill--issue {
  background: color-mix(in srgb, #ff5a36 14%, white);
  color: #b9361a;
}

.school-it-import__status-pill--neutral {
  background: color-mix(in srgb, var(--color-surface) 70%, var(--color-bg));
}

.school-it-import__micro-pill,
.school-it-import__header-chip {
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
  color: var(--color-text-secondary);
}

.school-it-import__micro-pill--mono,
.school-it-import__context-value--mono {
  font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 11px;
}

.school-it-import__feedback {
  margin: 0;
  padding: 0 4px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
  color: #0f8a50;
}

.school-it-import__feedback--error {
  color: #b9361a;
}

.school-it-import__summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.school-it-import__summary-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 136px;
  padding: 18px;
  border-radius: 28px;
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
}

.school-it-import__summary-card--ready {
  background: color-mix(in srgb, #14b86a 10%, white);
}

.school-it-import__summary-card--issue {
  background: color-mix(in srgb, #ff5a36 10%, white);
}

.school-it-import__summary-card--active {
  background: color-mix(in srgb, #2f7bff 10%, white);
}

.school-it-import__summary-value {
  color: var(--color-text-primary);
  font-size: clamp(24px, 5vw, 36px);
  line-height: 0.95;
  letter-spacing: -0.06em;
}

.school-it-import__summary-note {
  font-size: 12px;
  line-height: 1.45;
}

.school-it-import__processing-main {
  display: flex;
  align-items: center;
  gap: 14px;
}

.school-it-import__processing-icon :deep(svg),
.school-it-import__button-spinner {
  animation: school-it-import-spin 1s linear infinite;
}

.school-it-import__processing-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.school-it-import__processing-title {
  font-size: 18px;
  line-height: 1.08;
}

.school-it-import__progress-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
}

.school-it-import__progress-track {
  position: relative;
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 70%, var(--color-bg));
  overflow: hidden;
}

.school-it-import__progress-fill {
  position: absolute;
  inset: 0 auto 0 0;
  min-width: 48px;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--color-primary) 0%, color-mix(in srgb, var(--color-primary) 72%, white) 100%);
  transition: width 0.3s ease;
}

.school-it-import__progress-fill--indeterminate {
  width: 32%;
  animation: school-it-import-progress 1.15s cubic-bezier(0.22, 1, 0.36, 1) infinite;
}

.school-it-import__progress-value {
  min-width: 52px;
  font-size: 12px;
  font-weight: 800;
  color: var(--color-text-secondary);
  text-align: right;
}

.school-it-import__result-actions {
  justify-content: flex-start;
  margin-top: 18px;
}

.school-it-import__result-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

.school-it-import__filter-pill {
  border: none;
  background: color-mix(in srgb, var(--color-surface) 82%, var(--color-bg));
  color: var(--color-text-secondary);
  transition: background 0.2s ease, color 0.2s ease;
}

.school-it-import__filter-pill--active {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.school-it-import__rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 18px;
  max-height: 480px;
  overflow: auto;
  padding-right: 2px;
}

.school-it-import__row {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
  border-radius: 26px;
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
}

.school-it-import__row--issue {
  background: color-mix(in srgb, #ff5a36 9%, white);
}

.school-it-import__row-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.school-it-import__row-copy {
  min-width: 0;
}

.school-it-import__row-name {
  font-size: 15px;
  line-height: 1.1;
}

.school-it-import__row-id {
  margin-top: 4px;
  font-weight: 700;
}

.school-it-import__row-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  font-size: 12px;
  font-weight: 600;
}

.school-it-import__row-error {
  margin: 0;
  color: #b9361a;
  font-size: 12px;
  line-height: 1.45;
  font-weight: 700;
}

.school-it-import__empty {
  padding: 28px 6px 2px;
  font-size: 14px;
  line-height: 1.5;
  text-align: center;
}

.school-it-import__side-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.school-it-import__side-title {
  font-size: 22px;
  line-height: 0.98;
  font-weight: 800;
}

.school-it-import__side-list {
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}

.school-it-import__context-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.school-it-import__context-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
}

.school-it-import__context-value {
  font-size: 14px;
  line-height: 1.35;
  color: var(--color-text-primary);
  word-break: break-word;
}

.school-it-import__button {
  min-height: 42px;
  padding: 0 16px;
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: transform 0.18s ease, filter 0.22s ease, opacity 0.2s ease;
}

.school-it-import__button:disabled {
  opacity: 0.58;
  cursor: not-allowed;
}

.school-it-import__button:not(:disabled):hover {
  filter: brightness(1.03);
}

.school-it-import__button:not(:disabled):active {
  transform: scale(0.98);
}

.school-it-import__button--primary {
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.school-it-import__button--surface {
  background: color-mix(in srgb, var(--color-surface) 84%, var(--color-bg));
  color: var(--color-text-primary);
}

.school-it-import__button--ghost {
  background: transparent;
  color: var(--color-text-primary);
  border: 1px solid color-mix(in srgb, var(--color-surface-border) 72%, transparent);
}

.school-it-import__file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

@keyframes school-it-import-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@keyframes school-it-import-progress {
  0% {
    transform: translateX(-110%);
  }

  100% {
    transform: translateX(260%);
  }
}

@media (max-width: 1023px) {
  .school-it-import {
    padding: 28px 22px 56px;
  }

  .school-it-import__step-grid,
  .school-it-import__summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .school-it-import__layout {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 767px) {
  .school-it-import {
    padding: 24px 18px 46px;
  }

  .school-it-import__body {
    gap: 18px;
  }

  .school-it-import__hero,
  .school-it-import__panel,
  .school-it-import__side-card {
    border-radius: 28px;
    padding: 20px;
  }

  .school-it-import__hero-top,
  .school-it-import__panel-head,
  .school-it-import__result-head {
    flex-direction: column;
  }

  .school-it-import__hero-actions,
  .school-it-import__panel-actions,
  .school-it-import__result-head-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .school-it-import__button {
    width: 100%;
  }

  .school-it-import__step-grid,
  .school-it-import__summary-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .school-it-import__dropzone {
    min-height: 184px;
    padding: 22px 18px;
  }

  .school-it-import__file-card,
  .school-it-import__row-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .school-it-import__progress-wrap {
    flex-direction: column;
    align-items: stretch;
  }

  .school-it-import__progress-value {
    text-align: left;
  }
}

@media (prefers-reduced-motion: reduce) {
  .school-it-import__button,
  .school-it-import__dropzone,
  .school-it-import__progress-fill,
  .school-it-import__button-spinner,
  .school-it-import__processing-icon :deep(svg) {
    animation: none;
    transition: none;
  }
}
</style>
