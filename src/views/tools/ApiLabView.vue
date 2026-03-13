<template>
  <div class="api-lab-page">
    <div class="api-lab-shell">
      <header class="lab-hero">
        <div>
          <p class="lab-kicker">Temporary Backend Lab</p>
          <h1 class="lab-title">Create a real school, school IT account, and test student against the deployed API.</h1>
          <p class="lab-copy">
            This screen bypasses mock data and talks directly to the Railway backend. Start with an `admin`
            account to create the school and `school_IT` user, then continue with the real student and face
            enrollment flow.
          </p>
        </div>

        <RouterLink class="lab-back-link" to="/">
          Back to Login
        </RouterLink>
      </header>

      <section class="lab-banner">
        <label class="field-label" for="api-base-url">API Base URL</label>
        <div class="banner-row">
          <input
            id="api-base-url"
            v-model="apiBaseUrl"
            class="lab-input"
            type="url"
            autocomplete="off"
            spellcheck="false"
            placeholder="https://sas-deploy-production.up.railway.app"
          />
          <button class="ghost-btn" type="button" :disabled="isCatalogLoading" @click="loadCatalogData">
            {{ isCatalogLoading ? 'Refreshing...' : 'Refresh Catalog' }}
          </button>
        </div>
        <p class="banner-note">
          Departments and programs are read from the live API so the student profile form stays aligned with backend IDs.
        </p>
      </section>

      <div class="lab-grid">
        <section class="lab-panel">
          <div class="panel-head">
            <span class="panel-step">1</span>
            <div>
              <h2 class="panel-title">Admin Session</h2>
              <p class="panel-copy">Use an admin account. School creation is restricted to the admin-only endpoint.</p>
            </div>
          </div>

          <form class="panel-form" @submit.prevent="handleAdminLogin">
            <label class="field">
              <span class="field-label">Email</span>
              <input v-model="adminSession.email" class="lab-input" type="email" autocomplete="username" required />
            </label>

            <label class="field">
              <span class="field-label">Password</span>
              <input
                v-model="adminSession.password"
                class="lab-input"
                type="password"
                autocomplete="current-password"
                required
              />
            </label>

            <button class="primary-btn" type="submit" :disabled="isAdminLoggingIn">
              {{ isAdminLoggingIn ? 'Signing In...' : 'Sign In as Admin' }}
            </button>
          </form>

          <p v-if="adminError" class="panel-error">{{ adminError }}</p>

          <div v-if="adminIdentity" class="panel-result">
            <p class="result-label">Connected Admin</p>
            <p class="result-value">{{ formatUserName(adminIdentity) }}</p>
            <p class="result-meta">{{ adminIdentity.email }}</p>
            <p class="result-meta">Roles: {{ formatRoles(adminIdentity) }}</p>
          </div>
        </section>

        <section class="lab-panel lab-panel--wide">
          <div class="panel-head">
            <span class="panel-step">2</span>
            <div>
              <h2 class="panel-title">Create School + School IT</h2>
              <p class="panel-copy">
                This uses `POST /api/school/admin/create-school-it`, uploads the bundled JRMSU logo asset,
                and then applies the black accent through `PUT /school-settings/me`.
              </p>
            </div>
          </div>

          <div class="school-setup-layout">
            <div class="logo-card">
              <p class="result-label">Bundled Logo</p>
              <div class="logo-preview-shell">
                <img :src="jrmsuLogoUrl" alt="JRMSU logo preview" class="logo-preview-image" />
              </div>
              <p class="result-meta">Source: `src/data/jrmsu_icon.png`</p>
            </div>

            <form class="panel-form school-setup-form" @submit.prevent="handleCreateSchoolIt">
              <div class="field-row">
                <label class="field">
                  <span class="field-label">School Name</span>
                  <input v-model="schoolForm.schoolName" class="lab-input" type="text" required />
                </label>

                <label class="field">
                  <span class="field-label">School Code</span>
                  <input v-model="schoolForm.schoolCode" class="lab-input" type="text" placeholder="JRMSU" />
                </label>
              </div>

              <div class="field-row">
                <label class="field">
                  <span class="field-label">School IT First Name</span>
                  <input v-model="schoolForm.firstName" class="lab-input" type="text" required />
                </label>

                <label class="field">
                  <span class="field-label">Middle Name</span>
                  <input v-model="schoolForm.middleName" class="lab-input" type="text" />
                </label>

                <label class="field">
                  <span class="field-label">Last Name</span>
                  <input v-model="schoolForm.lastName" class="lab-input" type="text" required />
                </label>
              </div>

              <div class="field-row">
                <label class="field">
                  <span class="field-label">School IT Email</span>
                  <input v-model="schoolForm.email" class="lab-input" type="email" autocomplete="off" required />
                </label>

                <label class="field">
                  <span class="field-label">Password</span>
                  <input
                    v-model="schoolForm.password"
                    class="lab-input"
                    type="text"
                    autocomplete="off"
                    placeholder="Leave blank to let backend generate one"
                  />
                </label>
              </div>

              <div class="field-row">
                <label class="field">
                  <span class="field-label">Primary Color</span>
                  <input v-model="schoolForm.primaryColor" class="lab-input" type="text" required />
                </label>

                <label class="field">
                  <span class="field-label">Secondary Color</span>
                  <input v-model="schoolForm.secondaryColor" class="lab-input" type="text" />
                </label>

                <label class="field">
                  <span class="field-label">Accent Color</span>
                  <input v-model="schoolForm.accentColor" class="lab-input" type="text" required />
                </label>
              </div>

              <p class="field-hint">
                Default test branding is blue `#0057B8`, yellow `#FFD400`, and black `#000000`.
              </p>

              <button class="primary-btn" type="submit" :disabled="!adminToken || isSchoolCreating">
                {{ isSchoolCreating ? 'Creating School...' : 'Create School IT Setup' }}
              </button>
            </form>
          </div>

          <p v-if="schoolError" class="panel-error">{{ schoolError }}</p>

          <div v-if="schoolSetupResult || schoolBrandingResult" class="response-grid">
            <div v-if="schoolSetupResult" class="response-card">
              <p class="result-label">School Create Response</p>
              <p class="result-value">{{ schoolSetupResult.school?.school_name || schoolForm.schoolName }}</p>
              <p class="result-meta">School IT: {{ schoolSetupResult.school_it_email }}</p>
              <p class="result-meta">User ID: {{ schoolSetupResult.school_it_user_id }}</p>
              <p v-if="schoolSetupResult.generated_temporary_password" class="result-meta">
                Temporary Password: {{ schoolSetupResult.generated_temporary_password }}
              </p>
              <p v-if="schoolSetupResult.school?.logo_url" class="result-meta result-meta--wrap">
                Logo URL: {{ schoolSetupResult.school.logo_url }}
              </p>
            </div>

            <div v-if="schoolBrandingResult" class="response-card">
              <p class="result-label">School Branding</p>
              <pre class="json-block">{{ formatJson(schoolBrandingResult) }}</pre>
            </div>
          </div>
        </section>

        <section class="lab-panel">
          <div class="panel-head">
            <span class="panel-step">3</span>
            <div>
              <h2 class="panel-title">Create Student User</h2>
              <p class="panel-copy">This hits `POST /users/` with the real student role.</p>
            </div>
          </div>

          <form class="panel-form" @submit.prevent="handleCreateUser">
            <label class="field">
              <span class="field-label">First Name</span>
              <input v-model="userForm.firstName" class="lab-input" type="text" required />
            </label>

            <label class="field">
              <span class="field-label">Middle Name</span>
              <input v-model="userForm.middleName" class="lab-input" type="text" />
            </label>

            <label class="field">
              <span class="field-label">Last Name</span>
              <input v-model="userForm.lastName" class="lab-input" type="text" required />
            </label>

            <label class="field">
              <span class="field-label">Email</span>
              <input v-model="userForm.email" class="lab-input" type="email" autocomplete="off" required />
            </label>

            <label class="field">
              <span class="field-label">Password</span>
              <input v-model="userForm.password" class="lab-input" type="text" autocomplete="off" />
            </label>

            <button class="primary-btn" type="submit" :disabled="!adminToken || isUserCreating">
              {{ isUserCreating ? 'Creating...' : 'Create Student User' }}
            </button>
          </form>

          <p v-if="userError" class="panel-error">{{ userError }}</p>

          <div v-if="createdUser" class="panel-result">
            <p class="result-label">Created User</p>
            <p class="result-value">{{ formatUserName(createdUser) }}</p>
            <p class="result-meta">{{ createdUser.email }}</p>
            <p class="result-meta">User ID: {{ createdUser.id }}</p>
          </div>
        </section>

        <section class="lab-panel">
          <div class="panel-head">
            <span class="panel-step">4</span>
            <div>
              <h2 class="panel-title">Attach Student Profile</h2>
              <p class="panel-copy">This maps the new user to the backend student profile record.</p>
            </div>
          </div>

          <form class="panel-form" @submit.prevent="handleCreateStudentProfile">
            <label class="field">
              <span class="field-label">User ID</span>
              <input v-model="studentProfileForm.userId" class="lab-input" type="number" min="1" required />
            </label>

            <label class="field">
              <span class="field-label">Student ID</span>
              <input v-model="studentProfileForm.studentId" class="lab-input" type="text" placeholder="CS-2026-001" />
            </label>

            <label class="field">
              <span class="field-label">Department</span>
              <select v-model="studentProfileForm.departmentId" class="lab-input">
                <option value="">Select department</option>
                <option v-for="department in departments" :key="department.id" :value="String(department.id)">
                  {{ department.name }}
                </option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Program</span>
              <select v-model="studentProfileForm.programId" class="lab-input">
                <option value="">Select program</option>
                <option v-for="program in availablePrograms" :key="program.id" :value="String(program.id)">
                  {{ program.name }}
                </option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Year Level</span>
              <select v-model="studentProfileForm.yearLevel" class="lab-input">
                <option value="">Select year level</option>
                <option v-for="level in [1, 2, 3, 4, 5]" :key="level" :value="String(level)">
                  Year {{ level }}
                </option>
              </select>
            </label>

            <button class="primary-btn" type="submit" :disabled="!adminToken || isStudentProfileCreating">
              {{ isStudentProfileCreating ? 'Saving...' : 'Create Student Profile' }}
            </button>
          </form>

          <p v-if="studentProfileError" class="panel-error">{{ studentProfileError }}</p>

          <div v-if="studentProfileResult" class="panel-result">
            <p class="result-label">Student Profile Ready</p>
            <p class="result-value">{{ formatUserName(studentProfileResult) }}</p>
            <p class="result-meta">Student ID: {{ studentProfileResult.student_profile?.student_id || 'No student id returned' }}</p>
          </div>
        </section>

        <section class="lab-panel">
          <div class="panel-head">
            <span class="panel-step">5</span>
            <div>
              <h2 class="panel-title">Student Session</h2>
              <p class="panel-copy">Sign in as the created student before saving the face reference.</p>
            </div>
          </div>

          <form class="panel-form" @submit.prevent="handleStudentLogin">
            <label class="field">
              <span class="field-label">Student Email</span>
              <input v-model="studentSession.email" class="lab-input" type="email" autocomplete="username" required />
            </label>

            <label class="field">
              <span class="field-label">Student Password</span>
              <input
                v-model="studentSession.password"
                class="lab-input"
                type="password"
                autocomplete="current-password"
                required
              />
            </label>

            <button class="primary-btn" type="submit" :disabled="isStudentLoggingIn">
              {{ isStudentLoggingIn ? 'Signing In...' : 'Sign In as Student' }}
            </button>
          </form>

          <p v-if="studentError" class="panel-error">{{ studentError }}</p>

          <div v-if="studentIdentity" class="panel-result">
            <p class="result-label">Current Student</p>
            <p class="result-value">{{ formatUserName(studentIdentity) }}</p>
            <p class="result-meta">{{ studentIdentity.email }}</p>
            <p class="result-meta">
              Face enrolled:
              {{ faceStatus?.face_reference_enrolled ? 'Yes' : 'No' }}
            </p>
          </div>
        </section>

        <section class="lab-panel lab-panel--wide">
          <div class="panel-head">
            <span class="panel-step">6</span>
            <div>
              <h2 class="panel-title">Register Face Reference</h2>
              <p class="panel-copy">
                Upload a clear front-facing image. The screen will attempt the security endpoint with the selected student session.
              </p>
            </div>
          </div>

          <div class="face-layout">
            <div class="face-preview">
              <div v-if="selectedImagePreviewUrl" class="face-preview-shell">
                <img :src="selectedImagePreviewUrl" alt="Face preview" class="face-preview-image" />
              </div>
              <div v-else class="face-preview-empty">
                Choose an image file to preview it here.
              </div>
            </div>

            <form class="panel-form face-form" @submit.prevent="handleRegisterFace">
              <label class="field">
                <span class="field-label">Image File</span>
                <input class="lab-input lab-input--file" type="file" accept="image/*" @change="handleFilePick" />
              </label>

              <button class="primary-btn" type="submit" :disabled="!studentToken || !selectedImageFile || isFaceSaving">
                {{ isFaceSaving ? 'Saving Face...' : 'Save Face Reference' }}
              </button>

              <button class="ghost-btn" type="button" :disabled="!studentToken || isFaceStatusLoading" @click="refreshStudentState">
                {{ isFaceStatusLoading ? 'Refreshing...' : 'Refresh Face Status' }}
              </button>
            </form>
          </div>

          <p v-if="faceError" class="panel-error">{{ faceError }}</p>

          <div v-if="faceSaveResult || faceStatus" class="response-grid">
            <div class="response-card" v-if="faceSaveResult">
              <p class="result-label">Face Save Response</p>
              <pre class="json-block">{{ formatJson(faceSaveResult) }}</pre>
            </div>

            <div class="response-card" v-if="faceStatus">
              <p class="result-label">Face Status</p>
              <pre class="json-block">{{ formatJson(faceStatus) }}</pre>
            </div>
          </div>
        </section>

        <section class="lab-panel lab-panel--wide">
          <div class="panel-head">
            <span class="panel-step">Trace</span>
            <div>
              <h2 class="panel-title">Request Trace</h2>
              <p class="panel-copy">Latest actions and backend responses from this temporary screen.</p>
            </div>
          </div>

          <div v-if="activityLog.length" class="trace-list">
            <article v-for="entry in activityLog" :key="entry.id" class="trace-item">
              <div class="trace-head">
                <strong>{{ entry.title }}</strong>
                <span>{{ entry.time }}</span>
              </div>
              <p class="trace-copy">{{ entry.message }}</p>
            </article>
          </div>
          <p v-else class="trace-empty">No requests made yet.</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import jrmsuLogoUrl from '@/data/jrmsu_icon.png'
import {
  createSchoolWithSchoolIt,
  createStudentProfile,
  createUser,
  getCurrentUserProfile,
  getDepartments,
  getFaceStatus,
  getPrograms,
  loginForAccessToken,
  resolveApiBaseUrl,
  saveFaceReference,
  updateSchoolSettings,
} from '@/services/backendApi.js'

const apiBaseUrl = ref(resolveApiBaseUrl())

const adminSession = reactive({
  email: '',
  password: '',
})

const schoolForm = reactive({
  schoolName: 'JRMSU Test School',
  schoolCode: 'JRMSU',
  firstName: 'School',
  middleName: '',
  lastName: 'IT',
  email: '',
  password: '',
  primaryColor: '#0057B8',
  secondaryColor: '#FFD400',
  accentColor: '#000000',
})

const userForm = reactive({
  firstName: '',
  middleName: '',
  lastName: '',
  email: '',
  password: '',
})

const studentProfileForm = reactive({
  userId: '',
  studentId: '',
  departmentId: '',
  programId: '',
  yearLevel: '',
})

const studentSession = reactive({
  email: '',
  password: '',
})

const departments = ref([])
const programs = ref([])

const adminToken = ref('')
const studentToken = ref('')
const adminIdentity = ref(null)
const schoolSetupResult = ref(null)
const schoolBrandingResult = ref(null)
const createdUser = ref(null)
const studentProfileResult = ref(null)
const studentIdentity = ref(null)
const faceStatus = ref(null)
const faceSaveResult = ref(null)
const selectedImageFile = ref(null)
const selectedImagePreviewUrl = ref('')

const activityLog = ref([])

const adminError = ref('')
const schoolError = ref('')
const userError = ref('')
const studentProfileError = ref('')
const studentError = ref('')
const faceError = ref('')

const isCatalogLoading = ref(false)
const isAdminLoggingIn = ref(false)
const isSchoolCreating = ref(false)
const isUserCreating = ref(false)
const isStudentProfileCreating = ref(false)
const isStudentLoggingIn = ref(false)
const isFaceSaving = ref(false)
const isFaceStatusLoading = ref(false)

const availablePrograms = computed(() => {
  const departmentId = Number(studentProfileForm.departmentId)
  if (!Number.isFinite(departmentId)) return programs.value

  return programs.value.filter((program) => {
    const ids = Array.isArray(program.department_ids) ? program.department_ids : []
    return ids.includes(departmentId)
  })
})

watch(
  () => studentProfileForm.departmentId,
  () => {
    const selectedProgramId = Number(studentProfileForm.programId)
    if (!selectedProgramId) return

    const isStillValid = availablePrograms.value.some((program) => program.id === selectedProgramId)
    if (!isStillValid) {
      studentProfileForm.programId = ''
    }
  }
)

watch(createdUser, (user) => {
  if (!user?.id) return
  studentProfileForm.userId = String(user.id)
  studentSession.email = user.email || studentSession.email
  studentSession.password = userForm.password || studentSession.password
})

onMounted(() => {
  loadCatalogData()
})

onBeforeUnmount(() => {
  if (selectedImagePreviewUrl.value) {
    URL.revokeObjectURL(selectedImagePreviewUrl.value)
  }
})

function pushLog(title, message) {
  activityLog.value.unshift({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title,
    message,
    time: new Date().toLocaleTimeString('en-PH', {
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
    }),
  })

  if (activityLog.value.length > 10) {
    activityLog.value.length = 10
  }
}

function formatJson(value) {
  return JSON.stringify(value, null, 2)
}

function formatUserName(user) {
  return [user?.first_name, user?.middle_name, user?.last_name].filter(Boolean).join(' ') || 'Unnamed user'
}

function formatRoles(user) {
  const roles = Array.isArray(user?.roles) ? user.roles : []
  const names = roles
    .map((entry) => entry?.role?.name || entry?.name)
    .filter(Boolean)

  return names.join(', ') || 'No roles returned'
}

async function loadCatalogData() {
  isCatalogLoading.value = true
  try {
    const [departmentList, programList] = await Promise.all([
      getDepartments(apiBaseUrl.value),
      getPrograms(apiBaseUrl.value),
    ])

    departments.value = Array.isArray(departmentList) ? departmentList : []
    programs.value = Array.isArray(programList) ? programList : []
    pushLog(
      'Catalog loaded',
      `Fetched ${departments.value.length} departments and ${programs.value.length} programs from the API.`
    )
  } catch (error) {
    pushLog('Catalog failed', extractErrorMessage(error))
  } finally {
    isCatalogLoading.value = false
  }
}

async function handleAdminLogin() {
  adminError.value = ''
  isAdminLoggingIn.value = true

  try {
    const tokenPayload = await loginForAccessToken(apiBaseUrl.value, {
      username: adminSession.email,
      password: adminSession.password,
    })

    adminToken.value = tokenPayload?.access_token || ''
    adminIdentity.value = await getCurrentUserProfile(apiBaseUrl.value, adminToken.value)
    pushLog('Admin session ready', `Signed in as ${adminIdentity.value?.email || adminSession.email}.`)
    await loadCatalogData()
  } catch (error) {
    adminError.value = extractErrorMessage(error)
    pushLog('Admin login failed', adminError.value)
  } finally {
    isAdminLoggingIn.value = false
  }
}

async function handleCreateUser() {
  userError.value = ''
  isUserCreating.value = true

  try {
    createdUser.value = await createUser(apiBaseUrl.value, adminToken.value, {
      email: userForm.email,
      first_name: userForm.firstName,
      middle_name: userForm.middleName || null,
      last_name: userForm.lastName,
      password: userForm.password || null,
      roles: ['student'],
    })

    pushLog('Student user created', `Created user ${createdUser.value.email} with id ${createdUser.value.id}.`)
  } catch (error) {
    userError.value = extractErrorMessage(error)
    pushLog('Create user failed', userError.value)
  } finally {
    isUserCreating.value = false
  }
}

async function handleCreateSchoolIt() {
  schoolError.value = ''
  schoolSetupResult.value = null
  schoolBrandingResult.value = null
  isSchoolCreating.value = true

  try {
    const logoBlob = await fetchBundledLogoBlob()

    schoolSetupResult.value = await createSchoolWithSchoolIt(apiBaseUrl.value, adminToken.value, {
      school_name: schoolForm.schoolName,
      school_code: schoolForm.schoolCode || null,
      primary_color: schoolForm.primaryColor,
      secondary_color: schoolForm.secondaryColor || null,
      school_it_email: schoolForm.email,
      school_it_first_name: schoolForm.firstName,
      school_it_middle_name: schoolForm.middleName || null,
      school_it_last_name: schoolForm.lastName,
      school_it_password: schoolForm.password || null,
      logo: logoBlob,
      logo_name: 'jrmsu_icon.png',
    })

    pushLog(
      'School created',
      `Created ${schoolSetupResult.value?.school?.school_name || schoolForm.schoolName} with school IT ${schoolSetupResult.value?.school_it_email || schoolForm.email}.`
    )

    const schoolItPassword = schoolForm.password || schoolSetupResult.value?.generated_temporary_password
    if (!schoolItPassword) {
      pushLog('Branding skipped', 'The backend did not return a password, so accent update must be done after a manual school IT login.')
      return
    }

    const schoolItSession = await loginForAccessToken(apiBaseUrl.value, {
      username: schoolSetupResult.value?.school_it_email || schoolForm.email,
      password: schoolItPassword,
    })

    schoolBrandingResult.value = await updateSchoolSettings(apiBaseUrl.value, schoolItSession?.access_token || '', {
      school_name: schoolForm.schoolName,
      logo_url: schoolSetupResult.value?.school?.logo_url || null,
      primary_color: schoolForm.primaryColor,
      secondary_color: schoolForm.secondaryColor,
      accent_color: schoolForm.accentColor,
    })

    pushLog(
      'School branding updated',
      `Applied primary ${schoolForm.primaryColor}, secondary ${schoolForm.secondaryColor}, and accent ${schoolForm.accentColor}.`
    )
  } catch (error) {
    schoolError.value = extractErrorMessage(error)
    pushLog('School setup failed', schoolError.value)
  } finally {
    isSchoolCreating.value = false
  }
}

async function handleCreateStudentProfile() {
  studentProfileError.value = ''
  isStudentProfileCreating.value = true

  try {
    studentProfileResult.value = await createStudentProfile(apiBaseUrl.value, adminToken.value, {
      user_id: Number(studentProfileForm.userId),
      student_id: studentProfileForm.studentId || null,
      department_id: parseNullableNumber(studentProfileForm.departmentId),
      program_id: parseNullableNumber(studentProfileForm.programId),
      year_level: parseNullableNumber(studentProfileForm.yearLevel),
    })

    pushLog(
      'Student profile created',
      `Attached student profile to user id ${studentProfileForm.userId}.`
    )
  } catch (error) {
    studentProfileError.value = extractErrorMessage(error)
    pushLog('Create student profile failed', studentProfileError.value)
  } finally {
    isStudentProfileCreating.value = false
  }
}

async function handleStudentLogin() {
  studentError.value = ''
  isStudentLoggingIn.value = true

  try {
    const tokenPayload = await loginForAccessToken(apiBaseUrl.value, {
      username: studentSession.email,
      password: studentSession.password,
    })

    studentToken.value = tokenPayload?.access_token || ''
    await refreshStudentState()
    pushLog('Student session ready', `Signed in as ${studentIdentity.value?.email || studentSession.email}.`)
  } catch (error) {
    studentError.value = extractErrorMessage(error)
    pushLog('Student login failed', studentError.value)
  } finally {
    isStudentLoggingIn.value = false
  }
}

async function refreshStudentState() {
  if (!studentToken.value) return

  isFaceStatusLoading.value = true
  try {
    const [user, status] = await Promise.all([
      getCurrentUserProfile(apiBaseUrl.value, studentToken.value),
      getFaceStatus(apiBaseUrl.value, studentToken.value),
    ])

    studentIdentity.value = user
    faceStatus.value = status
    pushLog(
      'Student state refreshed',
      `Face enrolled: ${status?.face_reference_enrolled ? 'yes' : 'no'}.`
    )
  } catch (error) {
    const message = extractErrorMessage(error)
    studentError.value = message
    pushLog('Refresh student state failed', message)
  } finally {
    isFaceStatusLoading.value = false
  }
}

function handleFilePick(event) {
  const file = event.target?.files?.[0] ?? null
  selectedImageFile.value = file
  faceError.value = ''

  if (selectedImagePreviewUrl.value) {
    URL.revokeObjectURL(selectedImagePreviewUrl.value)
    selectedImagePreviewUrl.value = ''
  }

  if (!file) return
  selectedImagePreviewUrl.value = URL.createObjectURL(file)
}

async function handleRegisterFace() {
  if (!selectedImageFile.value || !studentToken.value) return

  faceError.value = ''
  isFaceSaving.value = true

  try {
    const dataUrl = await readFileAsDataUrl(selectedImageFile.value)
    const rawBase64 = dataUrl.includes(',') ? dataUrl.split(',')[1] : dataUrl

    try {
      faceSaveResult.value = await saveFaceReference(apiBaseUrl.value, studentToken.value, dataUrl)
    } catch (primaryError) {
      faceSaveResult.value = await saveFaceReference(apiBaseUrl.value, studentToken.value, rawBase64)
      pushLog('Face save fallback', `Full data URL was rejected, raw base64 succeeded: ${extractErrorMessage(primaryError)}`)
    }

    await refreshStudentState()
    pushLog('Face reference saved', 'The selected student now has an enrolled face reference.')
  } catch (error) {
    faceError.value = extractErrorMessage(error)
    pushLog('Face registration failed', faceError.value)
  } finally {
    isFaceSaving.value = false
  }
}

function parseNullableNumber(value) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

async function fetchBundledLogoBlob() {
  const response = await fetch(jrmsuLogoUrl)

  if (!response.ok) {
    throw new Error('Unable to load the bundled JRMSU logo asset.')
  }

  return response.blob()
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('Unable to read the selected file.'))
    reader.readAsDataURL(file)
  })
}

function extractErrorMessage(error) {
  return error?.message || 'Request failed.'
}
</script>

<style scoped>
.api-lab-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(170, 255, 0, 0.18), transparent 28%),
    radial-gradient(circle at bottom right, rgba(10, 10, 10, 0.08), transparent 30%),
    #efeee8;
  padding: 32px 20px 56px;
}

.api-lab-shell {
  width: min(1180px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lab-hero,
.lab-banner,
.lab-panel {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(10, 10, 10, 0.08);
  box-shadow: 0 20px 40px rgba(10, 10, 10, 0.06);
  backdrop-filter: blur(14px);
}

.lab-hero {
  border-radius: 32px;
  padding: 28px;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
}

.lab-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6d8200;
}

.lab-title {
  margin: 0;
  max-width: 760px;
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1.02;
  letter-spacing: -0.05em;
  color: #101010;
}

.lab-copy {
  margin: 14px 0 0;
  max-width: 760px;
  font-size: 15px;
  line-height: 1.6;
  color: #44443e;
}

.lab-back-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 0 18px;
  border-radius: 999px;
  background: #0a0a0a;
  color: #ffffff;
  text-decoration: none;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.lab-banner {
  border-radius: 26px;
  padding: 22px;
}

.banner-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.banner-note {
  margin: 12px 0 0;
  font-size: 12px;
  color: #5f5f58;
}

.lab-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.lab-panel {
  border-radius: 28px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.lab-panel--wide {
  grid-column: 1 / -1;
}

.panel-head {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.panel-step {
  min-width: 42px;
  height: 42px;
  padding: 0 10px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary, #aaff00);
  color: #0a0a0a;
  font-size: 14px;
  font-weight: 800;
}

.panel-title {
  margin: 0;
  font-size: 22px;
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: #101010;
}

.panel-copy {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: #56564f;
}

.panel-form {
  display: grid;
  gap: 12px;
}

.field-row {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 6px;
}

.field-hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #56564f;
}

.field-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #5f5f58;
}

.lab-input {
  width: 100%;
  min-height: 48px;
  border-radius: 16px;
  border: 1px solid rgba(10, 10, 10, 0.12);
  background: rgba(255, 255, 255, 0.9);
  padding: 0 16px;
  font-size: 14px;
  color: #111111;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.lab-input:focus {
  border-color: rgba(109, 130, 0, 0.45);
  box-shadow: 0 0 0 4px rgba(170, 255, 0, 0.18);
}

.lab-input--file {
  padding-top: 12px;
  padding-bottom: 12px;
}

.primary-btn,
.ghost-btn {
  min-height: 48px;
  border-radius: 16px;
  border: none;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.14s ease, opacity 0.18s ease, background 0.18s ease;
}

.primary-btn {
  background: #0a0a0a;
  color: #ffffff;
  padding: 0 18px;
}

.ghost-btn {
  background: rgba(10, 10, 10, 0.06);
  color: #111111;
  padding: 0 18px;
}

.primary-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.primary-btn:not(:disabled):active,
.ghost-btn:not(:disabled):active,
.lab-back-link:active {
  transform: scale(0.98);
}

.panel-error {
  margin: 0;
  color: #b83d3d;
  font-size: 12px;
  font-weight: 700;
}

.panel-result,
.response-card {
  border-radius: 20px;
  border: 1px solid rgba(10, 10, 10, 0.08);
  background: rgba(248, 248, 244, 0.92);
  padding: 16px;
}

.result-label {
  margin: 0 0 6px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6d8200;
}

.result-value {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #101010;
}

.result-meta {
  margin: 4px 0 0;
  font-size: 13px;
  color: #4b4b45;
}

.result-meta--wrap {
  overflow-wrap: anywhere;
}

.school-setup-layout {
  display: grid;
  gap: 18px;
  grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
  align-items: start;
}

.school-setup-form {
  align-content: start;
}

.logo-card {
  border-radius: 20px;
  border: 1px solid rgba(10, 10, 10, 0.08);
  background: rgba(248, 248, 244, 0.92);
  padding: 16px;
}

.logo-preview-shell {
  margin-top: 10px;
  border-radius: 24px;
  overflow: hidden;
  border: 1px solid rgba(10, 10, 10, 0.08);
  background: linear-gradient(180deg, rgba(0, 87, 184, 0.08), rgba(255, 212, 0, 0.18));
  aspect-ratio: 1 / 1;
}

.logo-preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  padding: 20px;
}

.face-layout {
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(0, 1fr);
  gap: 18px;
  align-items: stretch;
}

.face-preview,
.face-preview-shell,
.face-preview-empty {
  min-height: 260px;
  border-radius: 26px;
}

.face-preview {
  background: linear-gradient(180deg, rgba(170, 255, 0, 0.16), rgba(255, 255, 255, 0.86));
  padding: 12px;
}

.face-preview-shell {
  overflow: hidden;
  border: 1px solid rgba(10, 10, 10, 0.08);
}

.face-preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.face-preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
  color: #5f5f58;
  border: 1px dashed rgba(10, 10, 10, 0.14);
  background: rgba(255, 255, 255, 0.7);
}

.face-form {
  align-content: start;
}

.response-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.json-block {
  margin: 0;
  padding: 14px;
  border-radius: 16px;
  background: #101010;
  color: #d8f9b2;
  font-size: 11px;
  line-height: 1.55;
  overflow: auto;
}

.trace-list {
  display: grid;
  gap: 12px;
}

.trace-item {
  border-radius: 18px;
  padding: 14px 16px;
  background: rgba(248, 248, 244, 0.92);
  border: 1px solid rgba(10, 10, 10, 0.08);
}

.trace-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #111111;
}

.trace-copy,
.trace-empty {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: #4b4b45;
}

@media (max-width: 980px) {
  .lab-grid,
  .response-grid,
  .face-layout,
  .school-setup-layout {
    grid-template-columns: 1fr;
  }

  .field-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .api-lab-page {
    padding: 18px 14px 40px;
  }

  .lab-hero {
    padding: 22px;
    flex-direction: column;
  }

  .lab-banner,
  .lab-panel {
    padding: 18px;
  }

  .banner-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
