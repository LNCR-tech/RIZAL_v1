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
            placeholder="https://supervirulently-downless-keven.ngrok-free.dev"
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
            <p v-if="adminNeedsFaceSetup" class="result-meta">
              Protected access is blocked until this admin completes face setup.
            </p>
          </div>
        </section>

        <section v-if="adminToken" class="lab-panel lab-panel--wide">
          <div class="panel-head">
            <span class="panel-step">2</span>
            <div>
              <h2 class="panel-title">Admin Face Setup</h2>
              <p class="panel-copy">
                This admin account logs in successfully, but the backend marks the session as `face_pending`.
                Complete face enrollment and verification here before creating schools or users.
              </p>
            </div>
          </div>

          <div class="face-layout">
            <div class="face-preview">
              <div class="face-preview-shell">
                <video
                  v-show="adminCameraReady"
                  ref="adminVideoEl"
                  class="face-preview-video"
                  autoplay
                  playsinline
                  muted
                ></video>

                <div v-if="!adminCameraReady" class="face-preview-empty">
                  {{ adminCameraPlaceholderText }}
                </div>
              </div>
            </div>

            <form class="panel-form face-form" @submit.prevent="handleCompleteAdminFaceSetup">
              <div v-if="adminFaceStatus" class="response-card">
                <p class="result-label">Face Status</p>
                <p class="result-meta">Reference enrolled: {{ adminFaceStatus.face_reference_enrolled ? 'Yes' : 'No' }}</p>
                <p class="result-meta">Verification required: {{ adminFaceStatus.face_verification_required ? 'Yes' : 'No' }}</p>
                <p class="result-meta">Live capture required: {{ adminFaceStatus.live_capture_required ? 'Yes' : 'No' }}</p>
              </div>

              <p class="field-hint">
                Use the live camera capture for this admin account. The backend currently requires a live face capture.
              </p>

              <button
                class="primary-btn"
                type="submit"
                :disabled="!adminCameraReady || isAdminFaceSaving || isAdminLoggingIn || isAdminCameraStarting"
              >
                {{
                  isAdminFaceSaving
                    ? 'Completing Face Setup...'
                    : adminFaceStatus?.face_reference_enrolled
                      ? 'Verify with Live Camera'
                      : 'Capture, Register, and Verify'
                }}
              </button>

              <button
                class="ghost-btn"
                type="button"
                :disabled="isAdminFaceSaving || isAdminCameraStarting"
                @click="startAdminCamera"
              >
                {{
                  isAdminCameraStarting
                    ? 'Starting Camera...'
                    : adminCameraReady
                      ? 'Restart Camera'
                      : 'Start Camera'
                }}
              </button>

              <button
                class="ghost-btn"
                type="button"
                :disabled="!adminToken || isAdminFaceStatusLoading"
                @click="refreshAdminFaceState"
              >
                {{ isAdminFaceStatusLoading ? 'Refreshing...' : 'Refresh Admin Face Status' }}
              </button>
            </form>
          </div>

          <p v-if="adminFaceError" class="panel-error">{{ adminFaceError }}</p>

          <div v-if="adminFaceSaveResult || adminFaceVerifyResult" class="response-grid">
            <div v-if="adminFaceSaveResult" class="response-card">
              <p class="result-label">Face Reference Save</p>
              <pre class="json-block">{{ formatJson(adminFaceSaveResult) }}</pre>
            </div>

            <div v-if="adminFaceVerifyResult" class="response-card">
              <p class="result-label">Face Verification</p>
              <pre class="json-block">{{ formatJson(adminFaceVerifyResult) }}</pre>
            </div>
          </div>
        </section>

        <section class="lab-panel lab-panel--wide">
          <div class="panel-head">
            <span class="panel-step">3</span>
            <div>
              <h2 class="panel-title">Create School + School IT</h2>
              <p class="panel-copy">
                This creates the school with admin privileges, then signs in as the resulting `school_IT`
                account so student creation stays tied to the school-scoped session.
              </p>
            </div>
          </div>

          <div class="school-setup-layout">
            <div class="logo-card">
              <p class="result-label">Bundled Logo</p>
              <div class="logo-preview-shell">
                <img :src="jrmsuLogoUrl" alt="JRMSU logo preview" class="logo-preview-image" />
              </div>
              <p class="result-meta">Source: `/public/logos/aura.png`</p>
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
                  <span class="field-label">School IT Password</span>
                  <input
                    v-model="schoolForm.password"
                    class="lab-input"
                    type="text"
                    autocomplete="off"
                    required
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
                Default test branding is blue `#0057B8`, yellow `#FFD400`, and black `#000000`. The backend creates
                its own temporary password for School IT, so this screen immediately resets it to the password shown
                here after school creation.
              </p>

              <button class="primary-btn" type="submit" :disabled="!adminProtectedReady || isSchoolCreating">
                {{ isSchoolCreating ? 'Creating School...' : 'Create School IT Setup' }}
              </button>
            </form>
          </div>

          <p v-if="schoolError" class="panel-error">{{ schoolError }}</p>

          <div class="response-grid">
            <div v-if="schoolSetupResult" class="response-card">
              <p class="result-label">School Create Response</p>
              <p class="result-value">{{ schoolSetupResult.school?.school_name || schoolForm.schoolName }}</p>
              <p class="result-meta">School ID: {{ schoolSetupResult.school?.school_id ?? 'Missing' }}</p>
              <p class="result-meta">School IT: {{ schoolSetupResult.school_it_email }}</p>
              <p class="result-meta">User ID: {{ schoolSetupResult.school_it_user_id }}</p>
              <p class="result-meta">Known Password: {{ schoolItSession.password || 'Not set' }}</p>
              <p v-if="schoolSetupResult.school?.logo_url" class="result-meta result-meta--wrap">
                Logo URL: {{ schoolSetupResult.school.logo_url }}
              </p>
            </div>

            <div class="response-card">
              <p class="result-label">School IT Session</p>
              <p class="result-value">
                {{ schoolItIdentity ? formatUserName(schoolItIdentity) : 'School IT not connected yet' }}
              </p>
              <p class="result-meta">{{ schoolItIdentity?.email || schoolItSession.email || 'Enter a School IT email above' }}</p>
              <p class="result-meta">School ID: {{ schoolItIdentity?.school_id ?? schoolSetupResult?.school?.school_id ?? 'Missing' }}</p>
              <p class="result-meta">Roles: {{ schoolItIdentity ? formatRoles(schoolItIdentity) : 'No School IT session yet' }}</p>
              <p v-if="schoolItNeedsPasswordChange && schoolItNeedsFaceSetup" class="result-meta">
                First School IT login has two steps: 1) change the password, 2) capture and verify the School IT face.
              </p>
              <p v-else-if="schoolItNeedsPasswordChange" class="result-meta">
                Protected access is paused until this School IT account changes its password.
              </p>
              <p v-else-if="schoolItNeedsFaceSetup" class="result-meta">
                Password is accepted, but face verification must finish before student creation can use this account.
              </p>

              <form class="panel-form panel-form--compact" @submit.prevent="handleSchoolItLogin">
                <label class="field">
                  <span class="field-label">School IT Email</span>
                  <input v-model="schoolItSession.email" class="lab-input" type="email" autocomplete="username" required />
                </label>

                <label class="field">
                  <span class="field-label">School IT Password</span>
                  <input v-model="schoolItSession.password" class="lab-input" type="text" autocomplete="off" required />
                </label>

                <p class="field-hint">
                  Use this school-scoped session for all student creation below. If sign-in fails, reset the password
                  with admin and reconnect here.
                </p>

                <div
                  v-if="schoolItNeedsPasswordChange"
                  class="response-card response-card--compact school-it-password-card"
                  @keydown.enter.prevent="handleSchoolItPasswordChange"
                >
                  <p class="result-label">School IT Password Change</p>

                  <label class="field">
                    <span class="field-label">Current Password</span>
                    <input
                      v-model="schoolItPasswordChangeForm.currentPassword"
                      class="lab-input"
                      type="text"
                      autocomplete="off"
                    />
                  </label>

                  <label class="field">
                    <span class="field-label">New Password</span>
                    <input
                      v-model="schoolItPasswordChangeForm.newPassword"
                      class="lab-input"
                      type="text"
                      autocomplete="off"
                    />
                  </label>

                  <label class="field">
                    <span class="field-label">Confirm New Password</span>
                    <input
                      v-model="schoolItPasswordChangeForm.confirmPassword"
                      class="lab-input"
                      type="text"
                      autocomplete="off"
                    />
                  </label>

                  <p class="field-hint">
                    This backend requires one password change before the School IT account can reach face setup or
                    other protected resources. The password above will be replaced with this new one automatically.
                  </p>

                  <button
                    class="primary-btn"
                    type="button"
                    :disabled="!schoolItToken || isSchoolItPasswordChanging"
                    @click="handleSchoolItPasswordChange"
                  >
                    {{ isSchoolItPasswordChanging ? 'Changing Password...' : 'Change Password and Continue' }}
                  </button>
                </div>

                <div v-if="schoolItNeedsFaceSetup || schoolItCameraReady || schoolItFaceStatus" class="school-it-face-layout">
                  <div class="school-it-face-preview">
                    <div class="face-preview-shell face-preview-shell--compact">
                      <video
                        v-show="schoolItCameraReady"
                        ref="schoolItVideoEl"
                        class="face-preview-video"
                        autoplay
                        playsinline
                        muted
                      ></video>

                      <div v-if="!schoolItCameraReady" class="face-preview-empty face-preview-empty--compact">
                        {{ schoolItCameraPlaceholderText }}
                      </div>
                    </div>
                  </div>

                  <div class="panel-form panel-form--compact">
                    <div v-if="schoolItNeedsPasswordChange" class="response-card response-card--compact">
                      <p class="result-label">School IT Face Setup</p>
                      <p class="result-meta">
                        Face registration is still required for this first login, but the backend will not allow the
                        protected face endpoints to complete until the password change above is finished.
                      </p>
                    </div>

                    <div v-if="schoolItFaceStatus" class="response-card response-card--compact">
                      <p class="result-label">School IT Face Status</p>
                      <p class="result-meta">Reference enrolled: {{ schoolItFaceStatus.face_reference_enrolled ? 'Yes' : 'No' }}</p>
                      <p class="result-meta">Verification required: {{ schoolItFaceStatus.face_verification_required ? 'Yes' : 'No' }}</p>
                      <p class="result-meta">Live capture required: {{ schoolItFaceStatus.live_capture_required ? 'Yes' : 'No' }}</p>
                    </div>

                    <button
                      class="primary-btn"
                      type="button"
                      :disabled="schoolItNeedsPasswordChange || isSchoolItFaceSaving || isSchoolItLoggingIn || isSchoolItCameraStarting"
                      @click="handleCompleteSchoolItFaceSetup"
                    >
                      {{
                        isSchoolItFaceSaving
                          ? 'Completing School IT Face Setup...'
                          : schoolItFaceStatus?.face_reference_enrolled
                            ? 'Verify School IT with Live Camera'
                            : 'Capture, Register, and Verify School IT'
                      }}
                    </button>

                    <button
                      class="ghost-btn"
                      type="button"
                      :disabled="isSchoolItFaceSaving || isSchoolItCameraStarting"
                      @click="startSchoolItCamera"
                    >
                      {{
                        isSchoolItCameraStarting
                          ? 'Starting Camera...'
                          : schoolItCameraReady
                            ? 'Restart Camera'
                            : 'Start Camera'
                      }}
                    </button>

                    <button
                      class="ghost-btn"
                      type="button"
                      :disabled="schoolItNeedsPasswordChange || !schoolItToken || isSchoolItFaceStatusLoading"
                      @click="refreshSchoolItFaceState"
                    >
                      {{ isSchoolItFaceStatusLoading ? 'Refreshing...' : 'Refresh School IT Face Status' }}
                    </button>
                  </div>
                </div>

                <button class="primary-btn" type="submit" :disabled="isSchoolItLoggingIn">
                  {{ isSchoolItLoggingIn ? 'Signing In...' : schoolItReady ? 'Refresh School IT Session' : 'Sign In as School IT' }}
                </button>

                <button
                  class="ghost-btn"
                  type="button"
                  :disabled="!schoolItReady || isSchoolBrandingUpdating"
                  @click="handleApplySchoolBranding"
                >
                  {{ isSchoolBrandingUpdating ? 'Applying Branding...' : 'Apply Branding with School IT' }}
                </button>

                <button
                  class="ghost-btn"
                  type="button"
                  :disabled="!canResetSchoolItPassword || isSchoolItResetting"
                  @click="handleResetSchoolItPassword"
                >
                  {{ isSchoolItResetting ? 'Resetting Password...' : 'Reset Password + Reconnect' }}
                </button>
              </form>

              <p v-if="schoolItError" class="panel-error">{{ schoolItError }}</p>
              <p v-if="schoolItPasswordChangeError" class="panel-error">{{ schoolItPasswordChangeError }}</p>
              <p v-if="schoolItFaceError" class="panel-error">{{ schoolItFaceError }}</p>
              <p v-if="schoolBrandingError" class="panel-error">{{ schoolBrandingError }}</p>

              <div v-if="schoolItFaceSaveResult || schoolItFaceVerifyResult" class="response-grid">
                <div v-if="schoolItFaceSaveResult" class="response-card response-card--compact">
                  <p class="result-label">School IT Face Save</p>
                  <pre class="json-block">{{ formatJson(schoolItFaceSaveResult) }}</pre>
                </div>

                <div v-if="schoolItFaceVerifyResult" class="response-card response-card--compact">
                  <p class="result-label">School IT Face Verify</p>
                  <pre class="json-block">{{ formatJson(schoolItFaceVerifyResult) }}</pre>
                </div>
              </div>
            </div>

            <div v-if="schoolBrandingResult" class="response-card">
              <p class="result-label">School Branding</p>
              <pre class="json-block">{{ formatJson(schoolBrandingResult) }}</pre>
            </div>
          </div>
        </section>

        <section class="lab-panel">
          <div class="panel-head">
            <span class="panel-step">4</span>
            <div>
              <h2 class="panel-title">Create Student User</h2>
              <p class="panel-copy">
                This hits `POST /users/` with the `school_IT` token so the new student inherits the correct `school_id`.
                The backend generates its own temporary password, so this screen immediately resets the student to the
                password entered here.
              </p>
            </div>
          </div>

          <form class="panel-form" @submit.prevent="handleCreateUser">
            <p class="field-hint">{{ studentProvisioningHint }}</p>

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
              <input v-model="userForm.password" class="lab-input" type="text" autocomplete="off" required />
            </label>

            <button class="primary-btn" type="submit" :disabled="!schoolItReady || isUserCreating">
              {{ isUserCreating ? 'Creating...' : 'Create Student User' }}
            </button>
          </form>

          <p v-if="userError" class="panel-error">{{ userError }}</p>

          <div v-if="createdUser" class="panel-result">
            <p class="result-label">Created User</p>
            <p class="result-value">{{ formatUserName(createdUser) }}</p>
            <p class="result-meta">{{ createdUser.email }}</p>
            <p class="result-meta">User ID: {{ createdUser.id }}</p>
            <p class="result-meta">School ID: {{ createdUser.school_id ?? 'Missing' }}</p>
            <p class="result-meta">Roles: {{ formatRoles(createdUser) }}</p>
            <p class="result-meta">Known Login Password: {{ studentSession.password || 'Not set' }}</p>
          </div>
        </section>

        <section class="lab-panel">
          <div class="panel-head">
            <span class="panel-step">5</span>
            <div>
              <h2 class="panel-title">Attach Student Profile</h2>
              <p class="panel-copy">
                This tries the School IT session first, then falls back to the admin token only if the School IT
                scope is rejected by the backend.
              </p>
            </div>
          </div>

          <form class="panel-form" @submit.prevent="handleCreateStudentProfile">
            <p class="field-hint">{{ studentProvisioningHint }}</p>

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

            <button class="primary-btn" type="submit" :disabled="!schoolItReady || isStudentProfileCreating">
              {{ isStudentProfileCreating ? 'Saving...' : 'Create Student Profile' }}
            </button>
          </form>

          <p v-if="studentProfileError" class="panel-error">{{ studentProfileError }}</p>

          <div v-if="studentProfileResult" class="panel-result">
            <p class="result-label">Student Profile Ready</p>
            <p class="result-value">{{ formatUserName(studentProfileResult) }}</p>
            <p class="result-meta">Created via: {{ studentProfileCreateSource || 'Unknown source' }}</p>
            <p class="result-meta">School ID: {{ studentProfileResult.school_id ?? 'Missing' }}</p>
            <p class="result-meta">Student ID: {{ studentProfileResult.student_profile?.student_id || 'No student id returned' }}</p>
          </div>
        </section>

        <section class="lab-panel">
          <div class="panel-head">
            <span class="panel-step">6</span>
            <div>
              <h2 class="panel-title">Student Session</h2>
              <p class="panel-copy">
                Sign in as the school-linked student. If the account is still using a temporary password, change it
                here before saving the student face.
              </p>
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

          <div
            v-if="studentNeedsPasswordChange"
            class="response-card response-card--compact school-it-password-card"
            @keydown.enter.prevent="handleStudentPasswordChange"
          >
            <p class="result-label">Student Password Change</p>

            <label class="field">
              <span class="field-label">Current Password</span>
              <input
                v-model="studentPasswordChangeForm.currentPassword"
                class="lab-input"
                type="password"
                autocomplete="current-password"
              />
            </label>

            <label class="field">
              <span class="field-label">New Password</span>
              <input
                v-model="studentPasswordChangeForm.newPassword"
                class="lab-input"
                type="password"
                autocomplete="new-password"
              />
            </label>

            <label class="field">
              <span class="field-label">Confirm New Password</span>
              <input
                v-model="studentPasswordChangeForm.confirmPassword"
                class="lab-input"
                type="password"
                autocomplete="new-password"
              />
            </label>

            <button
              class="primary-btn"
              type="button"
              :disabled="!studentToken || isStudentPasswordChanging"
              @click="handleStudentPasswordChange"
            >
              {{ isStudentPasswordChanging ? 'Changing Password...' : 'Change Student Password' }}
            </button>
          </div>

          <p v-if="studentError" class="panel-error">{{ studentError }}</p>
          <p v-if="studentPasswordChangeError" class="panel-error">{{ studentPasswordChangeError }}</p>

          <div v-if="studentIdentity" class="panel-result">
            <p class="result-label">Current Student</p>
            <p class="result-value">{{ formatUserName(studentIdentity) }}</p>
            <p class="result-meta">{{ studentIdentity.email }}</p>
            <p class="result-meta">School ID: {{ studentIdentity.school_id ?? 'Missing' }}</p>
            <p class="result-meta">Roles: {{ formatRoles(studentIdentity) }}</p>
            <p class="result-meta">Student profile attached: {{ studentIdentity.student_profile ? 'Yes' : 'No' }}</p>
            <p class="result-meta">Student ID: {{ studentIdentity.student_profile?.student_id || 'Missing' }}</p>
            <p class="result-meta">
              Face enrolled:
              {{ faceStatus?.face_reference_enrolled ? 'Yes' : 'No' }}
            </p>
          </div>
        </section>

        <section class="lab-panel lab-panel--wide">
          <div class="panel-head">
            <span class="panel-step">7</span>
            <div>
              <h2 class="panel-title">Register Face Reference</h2>
              <p class="panel-copy">
                Upload a clear front-facing image. Student face enrollment uses the `/face/register` endpoint from the
                original backend, not the privileged security endpoint.
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

              <button
                class="primary-btn"
                type="submit"
                :disabled="!studentToken || studentNeedsPasswordChange || !selectedImageFile || isFaceSaving"
              >
                {{ isFaceSaving ? 'Saving Face...' : 'Save Face Reference' }}
              </button>

              <button
                class="ghost-btn"
                type="button"
                :disabled="!studentToken || studentNeedsPasswordChange || isFaceStatusLoading"
                @click="refreshStudentState"
              >
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
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  changePassword,
  createSchoolWithSchoolIt,
  createStudentProfile,
  createUser,
  getCurrentUserProfile,
  getDepartments,
  getFaceStatus,
  getPrograms,
  getUserById,
  loginForAccessToken,
  registerStudentFace,
  resetUserPassword,
  resolveApiBaseUrl,
  updateSchoolSettings,
  verifyFaceReference,
} from '@/services/backendApi.js'
import { withBase } from '@/services/appPath.js'

const jrmsuLogoUrl = withBase('logos/aura.png')

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

const schoolItSession = reactive({
  email: '',
  password: '',
})

const schoolItPasswordChangeForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
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

const studentPasswordChangeForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const departments = ref([])
const programs = ref([])

const adminToken = ref('')
const schoolItToken = ref('')
const studentToken = ref('')
const adminIdentity = ref(null)
const schoolItIdentity = ref(null)
const adminProtectedReady = ref(false)
const adminNeedsFaceSetup = ref(false)
const schoolItNeedsFaceSetup = ref(false)
const schoolItNeedsPasswordChange = ref(false)
const schoolItPasswordChangeEndpoint = ref('/auth/change-password')
const adminFaceStatus = ref(null)
const schoolItFaceStatus = ref(null)
const adminFaceSaveResult = ref(null)
const adminFaceVerifyResult = ref(null)
const schoolItFaceSaveResult = ref(null)
const schoolItFaceVerifyResult = ref(null)
const adminVideoEl = ref(null)
const adminMediaStream = ref(null)
const adminVideoReady = ref(false)
const adminCameraState = ref('idle')
const schoolItVideoEl = ref(null)
const schoolItMediaStream = ref(null)
const schoolItVideoReady = ref(false)
const schoolItCameraState = ref('idle')
const schoolSetupResult = ref(null)
const schoolBrandingResult = ref(null)
const createdUser = ref(null)
const studentProfileResult = ref(null)
const studentProfileCreateSource = ref('')
const studentIdentity = ref(null)
const studentNeedsPasswordChange = ref(false)
const faceStatus = ref(null)
const faceSaveResult = ref(null)
const selectedImageFile = ref(null)
const selectedImagePreviewUrl = ref('')

const activityLog = ref([])

const adminError = ref('')
const adminFaceError = ref('')
const schoolError = ref('')
const schoolItError = ref('')
const schoolBrandingError = ref('')
const schoolItPasswordChangeError = ref('')
const schoolItFaceError = ref('')
const userError = ref('')
const studentProfileError = ref('')
const studentError = ref('')
const studentPasswordChangeError = ref('')
const faceError = ref('')

const isCatalogLoading = ref(false)
const isAdminLoggingIn = ref(false)
const isAdminFaceSaving = ref(false)
const isAdminFaceStatusLoading = ref(false)
const isAdminCameraStarting = ref(false)
const isSchoolCreating = ref(false)
const isSchoolItLoggingIn = ref(false)
const isSchoolItResetting = ref(false)
const isSchoolBrandingUpdating = ref(false)
const isSchoolItPasswordChanging = ref(false)
const isSchoolItFaceSaving = ref(false)
const isSchoolItFaceStatusLoading = ref(false)
const isSchoolItCameraStarting = ref(false)
const isUserCreating = ref(false)
const isStudentProfileCreating = ref(false)
const isStudentLoggingIn = ref(false)
const isStudentPasswordChanging = ref(false)
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

const adminCameraReady = computed(() => adminVideoReady.value && adminCameraState.value === 'ready')
const schoolItCameraReady = computed(() => schoolItVideoReady.value && schoolItCameraState.value === 'ready')
const schoolItReady = computed(() => Boolean(schoolItToken.value && schoolItIdentity.value))
const schoolItUserId = computed(() => {
  const numeric = Number(schoolSetupResult.value?.school_it_user_id || schoolItIdentity.value?.id)
  return Number.isFinite(numeric) ? numeric : null
})
const studentProvisioningHint = computed(() => {
  if (!adminProtectedReady.value) return 'Complete the admin session first.'
  if (schoolItNeedsPasswordChange.value && schoolItNeedsFaceSetup.value) {
    return 'School IT first login requires both a password change and face verification before student creation can inherit the school scope.'
  }
  if (schoolItNeedsPasswordChange.value) return 'School IT is signed in but must change its password before student creation can inherit the school scope.'
  if (schoolItNeedsFaceSetup.value) return 'School IT is signed in but must complete face verification before student creation can inherit the school scope.'
  if (!schoolItReady.value) return 'Sign in as School IT first so created student users inherit the school scope.'
  return `School IT is connected to school id ${schoolItIdentity.value?.school_id ?? 'unknown'}. Student accounts created below will inherit that scope.`
})
const canResetSchoolItPassword = computed(() => {
  return Boolean(adminProtectedReady.value && schoolItUserId.value && String(schoolItSession.password || '').trim())
})
const adminCameraPlaceholderText = computed(() => {
  if (adminCameraState.value === 'denied') return 'Camera access is required for live face setup.'
  if (adminCameraState.value === 'unsupported') return 'Camera is unavailable on this device.'
  if (isAdminCameraStarting.value) return 'Starting camera...'
  if (isAdminFaceSaving.value) return 'Capturing live face...'
  return 'Start the camera to capture the admin face live.'
})
const schoolItCameraPlaceholderText = computed(() => {
  if (schoolItCameraState.value === 'denied') return 'Camera access is required for School IT face setup.'
  if (schoolItCameraState.value === 'unsupported') return 'Camera is unavailable on this device.'
  if (isSchoolItCameraStarting.value) return 'Starting camera...'
  if (isSchoolItFaceSaving.value) return 'Capturing School IT face...'
  return 'Start the camera to capture the School IT face live.'
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
  stopAdminCamera()
  stopSchoolItCamera()

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
    .map((entry) => (typeof entry === 'string' ? entry : entry?.role?.name || entry?.name))
    .filter(Boolean)

  return names.join(', ') || 'No roles returned'
}

function clearSelectedFacePreview() {
  selectedImageFile.value = null

  if (!selectedImagePreviewUrl.value) return

  URL.revokeObjectURL(selectedImagePreviewUrl.value)
  selectedImagePreviewUrl.value = ''
}

function isPasswordChangeRequiredMessage(message) {
  return /password change is required/i.test(String(message || ''))
}

function beginSchoolItPasswordChange(
  tokenPayload = null,
  message = 'Password change is required before accessing protected resources.',
  { faceRequired = schoolItNeedsFaceSetup.value } = {}
) {
  schoolItNeedsPasswordChange.value = true
  schoolItNeedsFaceSetup.value = Boolean(faceRequired)
  schoolItError.value = ''
  schoolItFaceError.value = ''
  schoolItPasswordChangeError.value = message
  schoolItPasswordChangeEndpoint.value = tokenPayload?.change_password_endpoint || schoolItPasswordChangeEndpoint.value || '/auth/change-password'
  schoolItPasswordChangeForm.currentPassword = schoolItSession.password || schoolItPasswordChangeForm.currentPassword
  schoolItFaceStatus.value = null
  schoolItFaceSaveResult.value = null
  schoolItFaceVerifyResult.value = null

  if (schoolItPasswordChangeForm.newPassword === schoolItPasswordChangeForm.currentPassword) {
    schoolItPasswordChangeForm.newPassword = ''
    schoolItPasswordChangeForm.confirmPassword = ''
  }

  stopSchoolItCamera()
}

function resetSchoolItState({ preserveCredentials = true } = {}) {
  stopSchoolItCamera()
  schoolItToken.value = ''
  schoolItIdentity.value = null
  schoolItNeedsFaceSetup.value = false
  schoolItNeedsPasswordChange.value = false
  schoolItPasswordChangeEndpoint.value = '/auth/change-password'
  schoolItError.value = ''
  schoolBrandingError.value = ''
  schoolItPasswordChangeError.value = ''
  schoolItFaceError.value = ''
  schoolItFaceStatus.value = null
  schoolItFaceSaveResult.value = null
  schoolItFaceVerifyResult.value = null
  schoolItPasswordChangeForm.currentPassword = ''
  schoolItPasswordChangeForm.newPassword = ''
  schoolItPasswordChangeForm.confirmPassword = ''

  if (!preserveCredentials) {
    schoolItSession.email = ''
    schoolItSession.password = ''
  }
}

function resetStudentWorkflow() {
  createdUser.value = null
  studentProfileResult.value = null
  studentProfileCreateSource.value = ''
  studentProfileForm.userId = ''
  studentProfileForm.studentId = ''
  studentToken.value = ''
  studentIdentity.value = null
  studentNeedsPasswordChange.value = false
  studentSession.email = ''
  studentSession.password = userForm.password || ''
  studentPasswordChangeForm.currentPassword = ''
  studentPasswordChangeForm.newPassword = ''
  studentPasswordChangeForm.confirmPassword = ''
  faceStatus.value = null
  faceSaveResult.value = null
  userError.value = ''
  studentProfileError.value = ''
  studentError.value = ''
  studentPasswordChangeError.value = ''
  faceError.value = ''
  clearSelectedFacePreview()
}

async function hydrateUserRecord(userId, token, fallbackValue = null) {
  const numericUserId = Number(userId)
  if (!token || !Number.isFinite(numericUserId)) return fallbackValue

  try {
    return await getUserById(apiBaseUrl.value, token, numericUserId)
  } catch {
    return fallbackValue
  }
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
  adminFaceError.value = ''
  schoolError.value = ''
  schoolSetupResult.value = null
  schoolBrandingResult.value = null
  stopAdminCamera()
  resetSchoolItState()
  resetStudentWorkflow()
  isAdminLoggingIn.value = true

  try {
    const tokenPayload = await loginForAccessToken(apiBaseUrl.value, {
      username: adminSession.email,
      password: adminSession.password,
    })

    adminToken.value = tokenPayload?.access_token || ''
    adminProtectedReady.value = false
    adminNeedsFaceSetup.value = false
    adminIdentity.value = {
      email: tokenPayload?.email || adminSession.email,
      first_name: tokenPayload?.first_name || 'Admin',
      last_name: tokenPayload?.last_name || '',
      roles: (tokenPayload?.roles || []).map((role) => ({ name: role })),
    }
    adminFaceStatus.value = null
    adminFaceSaveResult.value = null
    adminFaceVerifyResult.value = null

    if (tokenPayload?.face_verification_required) {
      adminNeedsFaceSetup.value = true
      await refreshAdminFaceState()
      await nextTick()
      await startAdminCamera()
      pushLog(
        'Admin face required',
        `Signed in as ${tokenPayload?.email || adminSession.email}, but the backend requires face setup before protected access.`
      )
      return
    }

    adminIdentity.value = await getCurrentUserProfile(apiBaseUrl.value, adminToken.value)
    adminProtectedReady.value = true
    pushLog('Admin session ready', `Signed in as ${adminIdentity.value?.email || adminSession.email}.`)
    await loadCatalogData()
  } catch (error) {
    adminError.value = extractErrorMessage(error)
    pushLog('Admin login failed', adminError.value)
  } finally {
    isAdminLoggingIn.value = false
  }
}

async function handleSchoolItLogin(options = {}) {
  schoolItError.value = ''
  schoolItPasswordChangeError.value = ''
  schoolItFaceError.value = ''

  if (!schoolItSession.email || !schoolItSession.password) {
    schoolItError.value = 'Enter the School IT email and password first.'
    return null
  }

  isSchoolItLoggingIn.value = true

  try {
    const tokenPayload = await loginForAccessToken(apiBaseUrl.value, {
      username: schoolItSession.email,
      password: schoolItSession.password,
    })

    schoolItToken.value = tokenPayload?.access_token || ''
    if (!schoolItToken.value) {
      throw new Error('The API did not return a School IT access token.')
    }

    schoolItNeedsPasswordChange.value = false
    schoolItNeedsFaceSetup.value = false
    schoolItFaceSaveResult.value = null
    schoolItFaceVerifyResult.value = null
    schoolItPasswordChangeEndpoint.value = tokenPayload?.change_password_endpoint || '/auth/change-password'
    const schoolItFaceRequired = Boolean(tokenPayload?.face_verification_required)

    if (tokenPayload?.must_change_password) {
      beginSchoolItPasswordChange(
        tokenPayload,
        schoolItFaceRequired
          ? 'School IT signed in. First login needs two steps before protected resources are unlocked: change the password, then complete face verification.'
          : 'School IT signed in, but the backend requires a password change before face verification or other protected resources.',
        { faceRequired: schoolItFaceRequired }
      )
      if (options?.applyBranding) {
        schoolBrandingError.value = 'Change the School IT password first, then click Apply Branding with School IT.'
      }
      pushLog(
        'School IT password change required',
        schoolItFaceRequired
          ? `Signed in as ${tokenPayload?.email || schoolItSession.email}, but the backend requires both a password change and School IT face setup before the session can continue.`
          : `Signed in as ${tokenPayload?.email || schoolItSession.email}, but the backend requires one password change before the session can continue.`
      )
      return null
    }

    if (schoolItFaceRequired) {
      schoolItNeedsPasswordChange.value = false
      schoolItPasswordChangeError.value = ''
      schoolItNeedsFaceSetup.value = true
      await refreshSchoolItFaceState()
      await nextTick()
      await startSchoolItCamera()

      schoolItFaceError.value = 'School IT signed in, but face verification is required before protected resources can be used.'
      if (options?.applyBranding) {
        schoolBrandingError.value = 'Finish School IT face verification first, then click Apply Branding with School IT.'
      }

      pushLog(
        'School IT face required',
        `Signed in as ${tokenPayload?.email || schoolItSession.email}, but the backend requires School IT face setup before protected access.`
      )
      return null
    }

    schoolItIdentity.value = await getCurrentUserProfile(apiBaseUrl.value, schoolItToken.value)
    schoolItNeedsFaceSetup.value = false
    stopSchoolItCamera()
    pushLog(
      'School IT session ready',
      `Signed in as ${schoolItIdentity.value?.email || schoolItSession.email} for school id ${schoolItIdentity.value?.school_id ?? 'unknown'}.`
    )

    if (options?.applyBranding) {
      await handleApplySchoolBranding()
    }

    return schoolItIdentity.value
  } catch (error) {
    const message = extractErrorMessage(error)

    if (schoolItToken.value && isPasswordChangeRequiredMessage(message)) {
      beginSchoolItPasswordChange(null, message)
      if (options?.applyBranding) {
        schoolBrandingError.value = 'Change the School IT password first, then click Apply Branding with School IT.'
      }
      pushLog(
        'School IT password change required',
        'School IT credentials were accepted, but the backend requires a password change before protected access.'
      )
      return null
    }

    if (schoolItToken.value && /face verification is required/i.test(message)) {
      schoolItNeedsPasswordChange.value = false
      schoolItPasswordChangeError.value = ''
      schoolItNeedsFaceSetup.value = true
      schoolItFaceError.value = message
      if (options?.applyBranding) {
        schoolBrandingError.value = 'Finish School IT face verification first, then click Apply Branding with School IT.'
      }
      await refreshSchoolItFaceState()
      await nextTick()
      await startSchoolItCamera()

      pushLog(
        'School IT face required',
        `School IT credentials were accepted, but the backend requires face verification before protected access.`
      )
      return null
    }

    schoolItToken.value = ''
    schoolItIdentity.value = null
    schoolItNeedsFaceSetup.value = false
    schoolItNeedsPasswordChange.value = false
    stopSchoolItCamera()
    schoolItError.value = message
    pushLog('School IT login failed', schoolItError.value)
    return null
  } finally {
    isSchoolItLoggingIn.value = false
  }
}

async function handleSchoolItPasswordChange() {
  schoolItPasswordChangeError.value = ''
  schoolItFaceError.value = ''
  schoolBrandingError.value = ''

  if (!schoolItToken.value) {
    schoolItPasswordChangeError.value = 'Sign in as School IT first so the password-change token is available.'
    return null
  }

  if (!schoolItPasswordChangeForm.currentPassword || !schoolItPasswordChangeForm.newPassword) {
    schoolItPasswordChangeError.value = 'Enter both the current password and a new School IT password.'
    return null
  }

  if (schoolItPasswordChangeForm.newPassword !== schoolItPasswordChangeForm.confirmPassword) {
    schoolItPasswordChangeError.value = 'The new School IT passwords do not match yet.'
    return null
  }

  if (schoolItPasswordChangeForm.currentPassword === schoolItPasswordChangeForm.newPassword) {
    schoolItPasswordChangeError.value = 'Choose a new School IT password that is different from the current one.'
    return null
  }

  isSchoolItPasswordChanging.value = true

  const nextPassword = schoolItPasswordChangeForm.newPassword

  try {
    await changePassword(
      apiBaseUrl.value,
      schoolItToken.value,
      {
        current_password: schoolItPasswordChangeForm.currentPassword,
        new_password: nextPassword,
      },
      schoolItPasswordChangeEndpoint.value || '/auth/change-password'
    )
  } catch (error) {
    const message = extractErrorMessage(error)

    if (/face verification is required/i.test(message)) {
      schoolItFaceError.value = message
      schoolItPasswordChangeError.value = 'The backend did not confirm the password change. Keep using the old password, then retry the password step.'

      pushLog(
        'School IT password change blocked',
        'The backend returned face verification before confirming the password change, so the old password is still the active one.'
      )
      return null
    }

    schoolItPasswordChangeError.value = message
    pushLog('School IT password change failed', schoolItPasswordChangeError.value)
    return null
  } finally {
    isSchoolItPasswordChanging.value = false
  }

  schoolItSession.password = nextPassword
  schoolItPasswordChangeForm.currentPassword = nextPassword
  schoolItPasswordChangeForm.newPassword = ''
  schoolItPasswordChangeForm.confirmPassword = ''
  schoolItNeedsPasswordChange.value = false
  schoolItPasswordChangeError.value = ''

  pushLog(
    'School IT password changed',
    'Password update succeeded. Reconnecting the School IT session now so face setup or student creation can continue.'
  )

  return await handleSchoolItLogin()
}

async function handleApplySchoolBranding() {
  schoolBrandingError.value = ''

  if (!schoolItToken.value) {
    schoolBrandingError.value = 'Sign in as School IT first to update school branding.'
    return null
  }

  isSchoolBrandingUpdating.value = true

  try {
    schoolBrandingResult.value = await updateSchoolSettings(apiBaseUrl.value, schoolItToken.value, {
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

    return schoolBrandingResult.value
  } catch (error) {
    const message = extractErrorMessage(error)

    if (isPasswordChangeRequiredMessage(message)) {
      beginSchoolItPasswordChange(null, message)
      schoolBrandingError.value = 'Change the School IT password first, then apply branding again.'
      pushLog('School IT password change required', 'Branding is blocked until School IT completes its required password change.')
      return null
    }

    schoolBrandingError.value = message
    pushLog('School branding failed', schoolBrandingError.value)
    return null
  } finally {
    isSchoolBrandingUpdating.value = false
  }
}

async function handleResetSchoolItPassword() {
  schoolItError.value = ''
  schoolItPasswordChangeError.value = ''
  schoolItFaceError.value = ''

  if (!schoolItUserId.value) {
    schoolItError.value = 'Create a school first so there is a School IT account to reset.'
    return
  }

  if (!schoolItSession.password) {
    schoolItError.value = 'Enter the School IT password you want to set first.'
    return
  }

  isSchoolItResetting.value = true

  try {
    await resetUserPassword(apiBaseUrl.value, adminToken.value, schoolItUserId.value, schoolItSession.password)
    pushLog(
      'School IT password reset',
      `Reset user id ${schoolItUserId.value} and reconnected the School IT session with the password shown in this panel.`
    )

    return await handleSchoolItLogin({ applyBranding: true })
  } catch (error) {
    schoolItError.value = extractErrorMessage(error)
    pushLog('School IT password reset failed', schoolItError.value)
    return null
  } finally {
    isSchoolItResetting.value = false
  }
}

async function refreshSchoolItFaceState() {
  if (!schoolItToken.value) return

  isSchoolItFaceStatusLoading.value = true
  try {
    schoolItFaceStatus.value = await getFaceStatus(apiBaseUrl.value, schoolItToken.value)
    pushLog(
      'School IT face status refreshed',
      `Reference enrolled: ${schoolItFaceStatus.value?.face_reference_enrolled ? 'yes' : 'no'}.`
    )
  } catch (error) {
    const message = extractErrorMessage(error)

    if (isPasswordChangeRequiredMessage(message)) {
      beginSchoolItPasswordChange(null, message)
      pushLog('School IT password change required', 'Face status is blocked until School IT completes the required password change.')
      return
    }

    schoolItFaceError.value = message
    pushLog('School IT face status failed', schoolItFaceError.value)
  } finally {
    isSchoolItFaceStatusLoading.value = false
  }
}

async function startSchoolItCamera() {
  schoolItFaceError.value = ''
  stopSchoolItCamera()

  if (!navigator?.mediaDevices?.getUserMedia) {
    schoolItCameraState.value = 'unsupported'
    return false
  }

  isSchoolItCameraStarting.value = true
  schoolItCameraState.value = 'requesting'

  try {
    schoolItMediaStream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'user',
        width: { ideal: 720 },
        height: { ideal: 720 },
      },
      audio: false,
    })
  } catch {
    schoolItCameraState.value = 'denied'
    isSchoolItCameraStarting.value = false
    return false
  }

  const el = schoolItVideoEl.value
  if (!el) {
    stopSchoolItCamera()
    schoolItCameraState.value = 'unsupported'
    isSchoolItCameraStarting.value = false
    return false
  }

  el.srcObject = schoolItMediaStream.value
  el.muted = true
  el.autoplay = true
  el.playsInline = true

  try {
    await el.play().catch(() => null)
  } catch {
    // ignore autoplay issues; ready-state check below handles availability
  }

  const isReady = await waitForVideoReady(el)
  if (!isReady) {
    stopSchoolItCamera()
    schoolItCameraState.value = 'unsupported'
    isSchoolItCameraStarting.value = false
    return false
  }

  schoolItVideoReady.value = true
  schoolItCameraState.value = 'ready'
  isSchoolItCameraStarting.value = false
  return true
}

function stopSchoolItCamera() {
  if (schoolItMediaStream.value) {
    schoolItMediaStream.value.getTracks().forEach((track) => track.stop())
    schoolItMediaStream.value = null
  }

  if (schoolItVideoEl.value) {
    schoolItVideoEl.value.srcObject = null
  }

  schoolItVideoReady.value = false
  schoolItCameraState.value = 'idle'
  isSchoolItCameraStarting.value = false
}

async function handleCompleteSchoolItFaceSetup() {
  if (!schoolItToken.value) return

  if (!schoolItCameraReady.value) {
    const cameraReady = await startSchoolItCamera()
    if (!cameraReady) {
      schoolItFaceError.value = 'Camera access is required to complete School IT face setup.'
      return
    }
  }

  schoolItFaceError.value = ''
  isSchoolItFaceSaving.value = true

  try {
    const dataUrl = captureSquareVideoFrame(schoolItVideoEl.value)
    const imageBase64 = normalizeImagePayload(dataUrl)

    if (!schoolItFaceStatus.value?.face_reference_enrolled) {
      schoolItFaceSaveResult.value = await saveFaceReference(apiBaseUrl.value, schoolItToken.value, imageBase64)
    }

    schoolItFaceVerifyResult.value = await verifyFaceReference(apiBaseUrl.value, schoolItToken.value, {
      image_base64: imageBase64,
    })

    if (schoolItFaceVerifyResult.value?.access_token) {
      schoolItToken.value = schoolItFaceVerifyResult.value.access_token
    }

    schoolItIdentity.value = await getCurrentUserProfile(apiBaseUrl.value, schoolItToken.value)
    schoolItNeedsFaceSetup.value = false
    await refreshSchoolItFaceState()
    stopSchoolItCamera()
    pushLog('School IT face setup complete', 'Protected School IT resources are now unlocked for this session.')
  } catch (error) {
    const message = extractErrorMessage(error)

    if (isPasswordChangeRequiredMessage(message)) {
      beginSchoolItPasswordChange(null, message)
      pushLog('School IT password change required', 'Face enrollment cannot continue until School IT changes its password.')
      return
    }

    schoolItFaceError.value = message
    pushLog('School IT face setup failed', schoolItFaceError.value)
  } finally {
    isSchoolItFaceSaving.value = false
  }
}

async function refreshAdminFaceState() {
  if (!adminToken.value) return

  isAdminFaceStatusLoading.value = true
  try {
    adminFaceStatus.value = await getFaceStatus(apiBaseUrl.value, adminToken.value)
    pushLog(
      'Admin face status refreshed',
      `Reference enrolled: ${adminFaceStatus.value?.face_reference_enrolled ? 'yes' : 'no'}.`
    )
  } catch (error) {
    adminFaceError.value = extractErrorMessage(error)
    pushLog('Admin face status failed', adminFaceError.value)
  } finally {
    isAdminFaceStatusLoading.value = false
  }
}

async function startAdminCamera() {
  adminFaceError.value = ''
  stopAdminCamera()

  if (!navigator?.mediaDevices?.getUserMedia) {
    adminCameraState.value = 'unsupported'
    return false
  }

  isAdminCameraStarting.value = true
  adminCameraState.value = 'requesting'

  try {
    adminMediaStream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'user',
        width: { ideal: 720 },
        height: { ideal: 720 },
      },
      audio: false,
    })
  } catch {
    adminCameraState.value = 'denied'
    isAdminCameraStarting.value = false
    return false
  }

  const el = adminVideoEl.value
  if (!el) {
    stopAdminCamera()
    adminCameraState.value = 'unsupported'
    isAdminCameraStarting.value = false
    return false
  }

  el.srcObject = adminMediaStream.value
  el.muted = true
  el.autoplay = true
  el.playsInline = true

  try {
    await el.play().catch(() => null)
  } catch {
    // ignore autoplay issues; ready-state check below handles availability
  }

  const isReady = await waitForVideoReady(el)
  if (!isReady) {
    stopAdminCamera()
    adminCameraState.value = 'unsupported'
    isAdminCameraStarting.value = false
    return false
  }

  adminVideoReady.value = true
  adminCameraState.value = 'ready'
  isAdminCameraStarting.value = false
  return true
}

function stopAdminCamera() {
  if (adminMediaStream.value) {
    adminMediaStream.value.getTracks().forEach((track) => track.stop())
    adminMediaStream.value = null
  }

  if (adminVideoEl.value) {
    adminVideoEl.value.srcObject = null
  }

  adminVideoReady.value = false
  adminCameraState.value = 'idle'
  isAdminCameraStarting.value = false
}

async function handleCompleteAdminFaceSetup() {
  if (!adminToken.value) return

  if (!adminCameraReady.value) {
    const cameraReady = await startAdminCamera()
    if (!cameraReady) {
      adminFaceError.value = 'Camera access is required to complete admin face setup.'
      return
    }
  }

  adminFaceError.value = ''
  isAdminFaceSaving.value = true

  try {
    const dataUrl = captureSquareVideoFrame(adminVideoEl.value)
    const imageBase64 = normalizeImagePayload(dataUrl)

    if (!adminFaceStatus.value?.face_reference_enrolled) {
      adminFaceSaveResult.value = await saveFaceReference(apiBaseUrl.value, adminToken.value, imageBase64)
    }

    adminFaceVerifyResult.value = await verifyFaceReference(apiBaseUrl.value, adminToken.value, {
      image_base64: imageBase64,
    })

    if (adminFaceVerifyResult.value?.access_token) {
      adminToken.value = adminFaceVerifyResult.value.access_token
    }

    adminIdentity.value = await getCurrentUserProfile(apiBaseUrl.value, adminToken.value)
    adminProtectedReady.value = true
    adminNeedsFaceSetup.value = false
    await refreshAdminFaceState()
    await loadCatalogData()
    stopAdminCamera()
    pushLog('Admin face setup complete', 'Protected admin resources are now unlocked for this session.')
  } catch (error) {
    adminFaceError.value = extractErrorMessage(error)
    pushLog('Admin face setup failed', adminFaceError.value)
  } finally {
    isAdminFaceSaving.value = false
  }
}

async function handleCreateUser() {
  userError.value = ''
  isUserCreating.value = true

  if (!schoolItReady.value) {
    userError.value = 'Sign in as School IT first so the new student inherits a school_id.'
    isUserCreating.value = false
    return
  }

  try {
    const created = await createUser(apiBaseUrl.value, schoolItToken.value, {
      email: userForm.email,
      first_name: userForm.firstName,
      middle_name: userForm.middleName || null,
      last_name: userForm.lastName,
      password: userForm.password || null,
      roles: ['student'],
    })

    createdUser.value = await hydrateUserRecord(created?.id, schoolItToken.value, created)

    if (createdUser.value?.id && userForm.password) {
      await resetUserPassword(apiBaseUrl.value, schoolItToken.value, createdUser.value.id, userForm.password)
      pushLog(
        'Student password reset',
        `Reset user id ${createdUser.value.id} to the password shown in this form because the backend ignores the submitted password during user creation.`
      )
    }

    studentProfileResult.value = null
    studentProfileCreateSource.value = ''

    pushLog(
      'Student user created',
      `Created user ${createdUser.value.email} with id ${createdUser.value.id} for school id ${createdUser.value?.school_id ?? 'missing'}.`
    )
  } catch (error) {
    userError.value = extractErrorMessage(error)
    pushLog('Create user failed', userError.value)
  } finally {
    isUserCreating.value = false
  }
}

async function handleCreateSchoolIt() {
  schoolError.value = ''
  schoolItError.value = ''
  schoolBrandingError.value = ''
  schoolSetupResult.value = null
  schoolBrandingResult.value = null
  resetSchoolItState()
  resetStudentWorkflow()
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
      logo_name: 'aura.png',
    })

    pushLog(
      'School created',
      `Created ${schoolSetupResult.value?.school?.school_name || schoolForm.schoolName} with school IT ${schoolSetupResult.value?.school_it_email || schoolForm.email}.`
    )

    schoolItSession.email = schoolSetupResult.value?.school_it_email || schoolForm.email
    const schoolItPassword = schoolForm.password || schoolSetupResult.value?.generated_temporary_password || schoolItSession.password
    schoolItSession.password = schoolItPassword || schoolItSession.password

    if (!schoolItPassword) {
      schoolItError.value = 'School created, but no School IT password is available yet. Enter one in the School IT session card, reset it with admin, then sign in.'
      pushLog('School IT follow-up required', schoolItError.value)
      return
    }

    pushLog(
      'School IT password reset scheduled',
      'The backend ignores the submitted School IT password during school creation, so admin reset will set the known password shown in this screen.'
    )

    const signedInSchoolIt = await handleResetSchoolItPassword()
    if (!signedInSchoolIt && schoolItError.value) {
      schoolItError.value = `School created, but the follow-up School IT sign-in failed: ${schoolItError.value}`
      pushLog('School IT follow-up required', 'Use the School IT session card to sign in or reset the password before creating students.')
    }
  } catch (error) {
    schoolError.value = `School creation failed: ${extractErrorMessage(error)}`
    pushLog('School setup failed', schoolError.value)
  } finally {
    isSchoolCreating.value = false
  }
}

async function handleCreateStudentProfile() {
  studentProfileError.value = ''
  studentProfileCreateSource.value = ''
  isStudentProfileCreating.value = true

  if (!schoolItReady.value) {
    studentProfileError.value = 'Sign in as School IT first so profile creation stays tied to the school-scoped user.'
    isStudentProfileCreating.value = false
    return
  }

  const payload = {
    user_id: Number(studentProfileForm.userId),
    student_id: studentProfileForm.studentId || null,
    department_id: parseNullableNumber(studentProfileForm.departmentId),
    program_id: parseNullableNumber(studentProfileForm.programId),
    year_level: parseNullableNumber(studentProfileForm.yearLevel),
  }

  try {
    studentProfileResult.value = await createStudentProfile(apiBaseUrl.value, schoolItToken.value, payload)
    studentProfileCreateSource.value = 'School IT session'
    pushLog('Student profile created', `Attached student profile to user id ${studentProfileForm.userId} with School IT scope.`)
  } catch (error) {
    const schoolItMessage = extractErrorMessage(error)
    pushLog('School IT profile attach failed', schoolItMessage)

    if (!adminProtectedReady.value || !adminToken.value) {
      studentProfileError.value = schoolItMessage
      pushLog('Create student profile failed', studentProfileError.value)
      return
    }

    try {
      studentProfileResult.value = await createStudentProfile(apiBaseUrl.value, adminToken.value, payload)
      studentProfileCreateSource.value = 'Admin fallback after School IT rejection'
      pushLog(
        'Student profile created via admin fallback',
        `School IT could not attach the profile, so admin fallback attached user id ${studentProfileForm.userId}.`
      )
    } catch (fallbackError) {
      studentProfileError.value = `${schoolItMessage} | Admin fallback failed: ${extractErrorMessage(fallbackError)}`
      pushLog('Create student profile failed', studentProfileError.value)
    }
  } finally {
    isStudentProfileCreating.value = false
  }
}

async function handleStudentLogin() {
  studentError.value = ''
  studentPasswordChangeError.value = ''
  isStudentLoggingIn.value = true

  try {
    const tokenPayload = await loginForAccessToken(apiBaseUrl.value, {
      username: studentSession.email,
      password: studentSession.password,
    })

    studentToken.value = tokenPayload?.access_token || ''
    studentNeedsPasswordChange.value = Boolean(tokenPayload?.must_change_password)

    if (studentNeedsPasswordChange.value) {
      studentIdentity.value = null
      faceStatus.value = null
      studentPasswordChangeForm.currentPassword = studentSession.password
      studentPasswordChangeForm.newPassword = ''
      studentPasswordChangeForm.confirmPassword = ''
      studentError.value = 'Student sign-in succeeded, but the backend requires one password change before profile or face requests can continue.'
      pushLog('Student password change required', studentError.value)
      return
    }

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
    const user = await getCurrentUserProfile(apiBaseUrl.value, studentToken.value)

    studentIdentity.value = user
    faceStatus.value = {
      face_reference_enrolled: Boolean(user?.student_profile?.is_face_registered),
    }
    studentNeedsPasswordChange.value = false
    pushLog(
      'Student state refreshed',
      `Face enrolled: ${faceStatus.value?.face_reference_enrolled ? 'yes' : 'no'}.`
    )
  } catch (error) {
    const message = extractErrorMessage(error)
    studentError.value = message
    pushLog('Refresh student state failed', message)
  } finally {
    isFaceStatusLoading.value = false
  }
}

async function handleStudentPasswordChange() {
  studentPasswordChangeError.value = ''
  studentError.value = ''

  if (!studentToken.value) {
    studentPasswordChangeError.value = 'Sign in as the student first so the password-change token is available.'
    return null
  }

  if (!studentPasswordChangeForm.currentPassword || !studentPasswordChangeForm.newPassword) {
    studentPasswordChangeError.value = 'Enter both the current student password and a new password.'
    return null
  }

  if (studentPasswordChangeForm.newPassword !== studentPasswordChangeForm.confirmPassword) {
    studentPasswordChangeError.value = 'The new student passwords do not match yet.'
    return null
  }

  if (studentPasswordChangeForm.currentPassword === studentPasswordChangeForm.newPassword) {
    studentPasswordChangeError.value = 'Choose a new password that is different from the temporary one.'
    return null
  }

  isStudentPasswordChanging.value = true

  try {
    await changePassword(apiBaseUrl.value, studentToken.value, {
      current_password: studentPasswordChangeForm.currentPassword,
      new_password: studentPasswordChangeForm.newPassword,
    })

    studentSession.password = studentPasswordChangeForm.newPassword
    studentPasswordChangeForm.currentPassword = studentSession.password
    studentPasswordChangeForm.newPassword = ''
    studentPasswordChangeForm.confirmPassword = ''
    studentNeedsPasswordChange.value = false

    await refreshStudentState()
    pushLog('Student password changed', `Updated ${studentSession.email || 'the student account'} to its new login password.`)
    return studentIdentity.value
  } catch (error) {
    studentPasswordChangeError.value = extractErrorMessage(error)
    pushLog('Student password change failed', studentPasswordChangeError.value)
    return null
  } finally {
    isStudentPasswordChanging.value = false
  }
}

function handleFilePick(event) {
  const file = event.target?.files?.[0] ?? null
  faceError.value = ''
  clearSelectedFacePreview()

  if (!file) return
  selectedImageFile.value = file
  selectedImagePreviewUrl.value = URL.createObjectURL(file)
}

async function handleRegisterFace() {
  if (!selectedImageFile.value || !studentToken.value) return

  faceError.value = ''
  isFaceSaving.value = true

  try {
    const dataUrl = await readFileAsDataUrl(selectedImageFile.value)
    const rawBase64 = normalizeImagePayload(dataUrl)

    try {
      faceSaveResult.value = await registerStudentFace(apiBaseUrl.value, studentToken.value, dataUrl)
    } catch (primaryError) {
      faceSaveResult.value = await registerStudentFace(apiBaseUrl.value, studentToken.value, rawBase64)
      pushLog('Face save fallback', `Full data URL was rejected, raw base64 succeeded: ${extractErrorMessage(primaryError)}`)
    }

    await refreshStudentState()
    pushLog('Face reference saved', 'The selected student now has an enrolled face reference through the student face endpoint.')
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

function normalizeImagePayload(dataUrl) {
  return dataUrl.includes(',') ? dataUrl.split(',')[1] : dataUrl
}

function waitForVideoReady(el) {
  if (el.readyState >= 2) return Promise.resolve(true)

  return new Promise((resolve) => {
    let settled = false
    const finish = (value) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      el.removeEventListener('loadeddata', handleReady)
      el.removeEventListener('canplay', handleReady)
      el.removeEventListener('error', handleError)
      resolve(value)
    }

    const handleReady = () => finish(true)
    const handleError = () => finish(false)
    const timer = setTimeout(() => finish(false), 8000)

    el.addEventListener('loadeddata', handleReady, { once: true })
    el.addEventListener('canplay', handleReady, { once: true })
    el.addEventListener('error', handleError, { once: true })
  })
}

function captureSquareVideoFrame(el) {
  if (!el || el.videoWidth <= 0 || el.videoHeight <= 0) {
    throw new Error('Unable to capture a live face image.')
  }

  const size = Math.min(el.videoWidth, el.videoHeight)
  const sx = Math.max(0, (el.videoWidth - size) / 2)
  const sy = Math.max(0, (el.videoHeight - size) / 2)
  const canvas = document.createElement('canvas')
  canvas.width = 720
  canvas.height = 720

  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('Unable to prepare the live face image.')
  }

  ctx.drawImage(el, sx, sy, size, size, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL('image/jpeg', 0.92)
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

.panel-form--compact {
  margin-top: 14px;
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

.response-card--compact {
  padding: 14px;
}

.school-it-password-card {
  display: grid;
  gap: 12px;
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
  background: #111111;
}

.face-preview-shell--compact {
  min-height: 220px;
}

.face-preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.face-preview-video {
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

.face-preview-empty--compact {
  min-height: 220px;
}

.face-form {
  align-content: start;
}

.school-it-face-layout {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(180px, 240px) minmax(0, 1fr);
  align-items: stretch;
}

.school-it-face-preview {
  background: linear-gradient(180deg, rgba(170, 255, 0, 0.16), rgba(255, 255, 255, 0.86));
  padding: 10px;
  border-radius: 22px;
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
  .school-setup-layout,
  .school-it-face-layout {
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
