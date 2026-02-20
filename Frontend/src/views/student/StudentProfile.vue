<script setup>
import { ref, computed, onMounted } from 'vue';
import { UserCircle, Mail, Shield, Phone, Building2, BookOpen, QrCode, Download, GraduationCap, WifiOff, Wifi } from 'lucide-vue-next';
import { getProfile, getCurrentUser, cacheOfflineQR, getOfflineQR, isRememberMe } from '../../services/api.js';
import QrcodeVue from 'qrcode.vue';

const isLoading = ref(true);
const isOffline = ref(!navigator.onLine);
const hasRememberMe = ref(isRememberMe());

const profile = ref({
  name: '', email: '', role: '', phone: '', department: '',
  bio: '', college: '', studentId: '', program: '', status: '', faceScanRegistered: false,
});

// Get current logged-in user
const currentUser = getCurrentUser();
const userId = currentUser?.id || '24-A-00123';

onMounted(async () => {
  // Listen for online/offline changes
  window.addEventListener('online', () => { isOffline.value = false; });
  window.addEventListener('offline', () => { isOffline.value = true; });

  if (isOffline.value) {
    // OFFLINE: Load from cache if Remember Me is on
    const cached = getOfflineQR();
    if (cached && hasRememberMe.value) {
      profile.value = {
        name: cached.name || '',
        email: cached.email || '',
        role: '',
        phone: '',
        department: '',
        bio: '',
        college: cached.college || '',
        studentId: cached.id || '',
        program: cached.program || '',
        status: 'Active',
        faceScanRegistered: true,
      };
    }
    isLoading.value = false;
    return;
  }

  // ONLINE: Fetch fresh profile from API
  try {
    const data = await getProfile(userId);
    profile.value = {
      name: data.name || '',
      email: data.email || '',
      role: data.role ? data.role.charAt(0).toUpperCase() + data.role.slice(1) : '',
      phone: data.phone || '',
      department: data.department || '',
      bio: data.bio || '',
      college: data.college || '',
      studentId: data.studentId || data.id || '',
      program: data.program || '',
      status: data.status || '',
      faceScanRegistered: data.faceScanRegistered || false,
    };

    // Cache QR data for offline use (only works if Remember Me is on)
    cacheOfflineQR({
      id: profile.value.studentId,
      name: profile.value.name,
      email: profile.value.email,
      college: profile.value.college,
      program: profile.value.program,
      type: 'student_attendance'
    });

  } catch (err) {
    console.error('Failed to load profile:', err);
  } finally {
    isLoading.value = false;
  }
});

// ===== QR CODE DATA =====
// JSON payload that the SG officer's scanner will read.
// This is the SAME data whether online or offline — fixed to the user.
// 🔴 BACKEND: When real API is ready, this could be a signed JWT
//    or encrypted token from GET /api/student/qr-token instead.
const qrValue = computed(() => {
  if (!profile.value.studentId) return '';
  return JSON.stringify({
    id: profile.value.studentId,
    name: profile.value.name,
    college: profile.value.college,
    program: profile.value.program,
    type: 'student_attendance'
  });
});

// Download QR as PNG image
const downloadQR = () => {
  const svgEl = document.querySelector('#student-qr-container svg');
  if (!svgEl) return;

  const svgData = new XMLSerializer().serializeToString(svgEl);
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const img = new Image();

  img.onload = () => {
    canvas.width = 400;
    canvas.height = 400;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 400, 400);
    ctx.drawImage(img, 0, 0, 400, 400);

    const link = document.createElement('a');
    link.download = `QR_${profile.value.studentId || 'student'}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
};

const statusBadge = computed(() => {
  switch (profile.value.status) {
    case 'Active': return 'badge-green';
    case 'Pending': return 'badge-amber';
    case 'Inactive': return 'badge-red';
    default: return 'badge-gray';
  }
});
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6 animate-fade-in">

    <!-- Offline Banner -->
    <div v-if="isOffline" class="flex items-center gap-3 px-4 py-3 bg-amber-50 dark:bg-amber-500/10 rounded-xl border border-amber-200 dark:border-amber-500/20">
      <WifiOff class="w-5 h-5 text-amber-500 shrink-0" />
      <div>
        <p class="text-sm font-semibold text-amber-700 dark:text-amber-400">You're Offline</p>
        <p class="text-xs text-amber-600 dark:text-amber-500">Showing your cached QR code for offline attendance</p>
      </div>
    </div>

    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ isOffline ? 'Offline QR Code' : 'My Profile' }}
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        {{ isOffline ? 'Present this QR to SG officers for attendance' : 'Your account information & QR code' }}
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"></div>
    </div>

    <!-- OFFLINE MODE: If offline + no Remember Me = show error -->
    <div v-else-if="isOffline && !hasRememberMe" class="glass-card p-12 text-center">
      <WifiOff class="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Offline QR Not Available</h3>
      <p class="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
        To use offline QR, you need to enable <strong>"Remember Me"</strong> when logging in. This caches your QR code for offline access.
      </p>
    </div>

    <!-- OFFLINE MODE: If offline + no cached QR -->
    <div v-else-if="isOffline && !qrValue" class="glass-card p-12 text-center">
      <QrCode class="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Cached QR Found</h3>
      <p class="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
        Please connect to the internet and open your profile once to cache your QR code for offline use.
      </p>
    </div>

    <template v-else>
      <!-- OFFLINE MODE: Show only QR card (centered, large) -->
      <div v-if="isOffline" class="flex flex-col items-center">
        <div class="glass-card p-8 w-full max-w-sm flex flex-col items-center">
          <div class="flex items-center gap-2 mb-5">
            <QrCode class="w-5 h-5 text-brand-500" />
            <h3 class="font-semibold text-gray-900 dark:text-white">Attendance QR</h3>
          </div>

          <!-- Real QR Code -->
          <div id="student-qr-container" class="bg-white p-5 rounded-xl shadow-inner">
            <QrcodeVue :value="qrValue" :size="220" level="H" render-as="svg" class="mx-auto" />
          </div>

          <div class="mt-4 text-center">
            <p class="font-semibold text-gray-900 dark:text-white">{{ profile.name }}</p>
            <p class="text-sm font-mono text-brand-500 mt-0.5">{{ profile.studentId }}</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ profile.college }}</p>
          </div>

          <button @click="downloadQR" class="btn-ghost border border-gray-200 dark:border-gray-700 mt-5 text-sm flex items-center gap-2">
            <Download class="w-4 h-4" /> Download QR
          </button>
        </div>
      </div>

      <!-- ONLINE MODE: Full profile view -->
      <template v-else>
        <!-- Profile Header Card -->
        <div class="glass-card p-8">
          <div class="flex flex-col sm:flex-row items-center gap-6">
            <!-- Avatar -->
            <div class="relative">
              <div class="w-24 h-24 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center text-white text-3xl font-bold shadow-lg shadow-brand-500/30">
                {{ profile.name.charAt(0) }}
              </div>
            </div>

            <div class="text-center sm:text-left flex-1">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ profile.name }}</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400 flex items-center justify-center sm:justify-start gap-1.5 mt-1">
                <Mail class="w-4 h-4" /> {{ profile.email }}
              </p>
              <div class="flex flex-wrap items-center justify-center sm:justify-start gap-2 mt-2">
                <span class="badge badge-blue">
                  <GraduationCap class="w-3 h-3" /> {{ profile.studentId }}
                </span>
                <span :class="['badge', statusBadge]">
                  <Shield class="w-3 h-3" /> {{ profile.status }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- QR Code + Details Row -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <!-- QR Code Card -->
          <div class="glass-card p-6 flex flex-col items-center">
            <div class="flex items-center gap-2 mb-4">
              <QrCode class="w-5 h-5 text-brand-500" />
              <h3 class="font-semibold text-gray-900 dark:text-white">My QR Code</h3>
            </div>

            <!-- Real QR Code via qrcode.vue -->
            <div id="student-qr-container" class="bg-white p-4 rounded-xl shadow-inner">
              <QrcodeVue
                v-if="qrValue"
                :value="qrValue"
                :size="200"
                level="H"
                render-as="svg"
                class="mx-auto"
              />
              <div v-else class="w-[200px] h-[200px] flex items-center justify-center text-gray-400 text-sm">
                Generating QR...
              </div>
            </div>

            <p class="text-xs text-gray-400 dark:text-gray-500 mt-3 text-center">
              Student ID: <span class="font-semibold text-gray-600 dark:text-gray-300">{{ profile.studentId }}</span>
            </p>
            <p class="text-[0.65rem] text-gray-400 dark:text-gray-500 mt-1 text-center">
              Present this QR to SG officers for offline attendance
            </p>

            <!-- Offline cache indicator -->
            <div v-if="hasRememberMe" class="flex items-center gap-1.5 mt-3 text-[0.65rem] text-emerald-500">
              <Wifi class="w-3 h-3" />
              <span>QR cached for offline use</span>
            </div>

            <button @click="downloadQR" class="btn-ghost border border-gray-200 dark:border-gray-700 mt-4 text-sm flex items-center gap-2">
              <Download class="w-4 h-4" /> Download QR
            </button>
          </div>

          <!-- Account Details -->
          <div class="lg:col-span-2 glass-card p-8">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-6">Account Details</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label class="form-label">Full Name</label>
                <input :value="profile.name" disabled class="form-input opacity-70 cursor-default" />
              </div>
              <div>
                <label class="form-label">Student ID</label>
                <input :value="profile.studentId" disabled class="form-input opacity-70 cursor-default" />
              </div>
              <div>
                <label class="form-label">Email Address</label>
                <input :value="profile.email" disabled class="form-input opacity-70 cursor-default" />
              </div>
              <div>
                <label class="form-label">Phone Number</label>
                <input :value="profile.phone" disabled class="form-input opacity-70 cursor-default" />
              </div>
              <div>
                <label class="form-label flex items-center gap-1.5"><Building2 class="w-3.5 h-3.5" /> College</label>
                <input :value="profile.college" disabled class="form-input opacity-70 cursor-default" />
              </div>
              <div>
                <label class="form-label flex items-center gap-1.5"><BookOpen class="w-3.5 h-3.5" /> Program</label>
                <input :value="profile.program" disabled class="form-input opacity-70 cursor-default" />
              </div>
              <div class="md:col-span-2">
                <label class="form-label">Bio</label>
                <textarea :value="profile.bio" rows="3" disabled class="form-input resize-none opacity-70 cursor-default"></textarea>
              </div>
            </div>

            <!-- Face Scan Status -->
            <div class="mt-6 pt-5 border-t border-gray-100 dark:border-white/[0.06]">
              <div class="flex items-center gap-3">
                <div :class="[
                  'w-10 h-10 rounded-xl flex items-center justify-center',
                  profile.faceScanRegistered
                    ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                    : 'bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400'
                ]">
                  <UserCircle class="w-5 h-5" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-gray-900 dark:text-white">
                    Face Scan {{ profile.faceScanRegistered ? 'Registered' : 'Not Registered' }}
                  </p>
                  <p class="text-xs text-gray-400">
                    {{ profile.faceScanRegistered ? 'Your face is registered for attendance scanning.' : 'Contact your SG officer to register your face scan.' }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>
