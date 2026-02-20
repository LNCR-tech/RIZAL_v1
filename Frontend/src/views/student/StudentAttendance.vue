<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import {
  MapPin, Camera, CheckCircle2, ChevronLeft, Clock, Building2,
  Users, Navigation, AlertCircle, Loader2, ScanLine
} from 'lucide-vue-next';
import {
  getStudentEvents, getCurrentUser, verifyEventLocation,
  getStudentAttendanceForEvent, markAttendance
} from '../../services/api.js';
import FaceScanAnimation from '../../components/FaceScanAnimation.vue';

// ===== STATE =====
const step = ref('events'); // 'events' | 'location' | 'facescan' | 'success'
const isLoading = ref(true);
const events = ref([]);
const selectedEvent = ref(null);
const attendanceStatuses = ref({});

// Location state
const locationStatus = ref('checking'); // 'checking' | 'verified' | 'denied' | 'too_far' | 'error'
const locationDistance = ref(0);
const locationMaxRadius = ref(0);

// Face scan state
const videoRef = ref(null);
const scanState = ref('scanning'); // 'scanning' | 'success' | 'error'
const statusText = ref('Initializing Camera...');
let detectionInterval = null;
let noFaceTimer = null;

// Success state
const checkInTime = ref('');

// Current user
const currentUser = getCurrentUser();
const studentId = currentUser?.id || '';

// ===== LOAD EVENTS =====
onMounted(async () => {
  try {
    const allEvents = await getStudentEvents(currentUser?.college || '');
    events.value = allEvents;

    // Check attendance status for each event
    for (const event of allEvents) {
      const status = await getStudentAttendanceForEvent(event.id, studentId);
      attendanceStatuses.value[event.id] = status;
    }
  } catch (err) {
    console.error('Failed to load events:', err);
  } finally {
    isLoading.value = false;
  }
});

onUnmounted(() => {
  stopCamera();
});

// ===== COMPUTED =====
const upcomingEvents = computed(() =>
  events.value.filter(e => (e.status === 'Upcoming' || e.status === 'Ongoing') && e.attendanceOpen)
);

const otherEvents = computed(() =>
  events.value.filter(e => !e.attendanceOpen || e.status !== 'Upcoming')
);

// ===== STEP 1: SELECT EVENT =====
const selectEvent = async (event) => {
  selectedEvent.value = event;
  step.value = 'location';
  locationStatus.value = 'checking';
  checkLocation();
};

// ===== STEP 2: LOCATION VERIFICATION =====
const checkLocation = () => {
  if (!navigator.geolocation) {
    locationStatus.value = 'error';
    return;
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const result = await verifyEventLocation(
          selectedEvent.value.id,
          position.coords.latitude,
          position.coords.longitude
        );
        locationDistance.value = result.distance;
        locationMaxRadius.value = result.maxRadius;
        locationStatus.value = result.verified ? 'verified' : 'too_far';
      } catch (err) {
        locationStatus.value = 'error';
      }
    },
    (err) => {
      locationStatus.value = 'denied';
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
};

// ===== STEP 3: FACE SCAN =====
const proceedToFaceScan = () => {
  step.value = 'facescan';
  scanState.value = 'scanning';
  statusText.value = 'Loading AI Models...';
  startDetection();
};

const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: {} });
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      statusText.value = 'Position your face in the frame...';
      resetNoFaceTimer();
    }
  } catch (err) {
    console.error(err);
    statusText.value = 'Error accessing camera.';
    scanState.value = 'error';
  }
};

const resetNoFaceTimer = () => {
  if (noFaceTimer) clearTimeout(noFaceTimer);
  if (scanState.value === 'success') return;

  noFaceTimer = setTimeout(() => {
    if (scanState.value !== 'success') {
      scanState.value = 'error';
      statusText.value = 'No face detected. Try again in better lighting.';
    }
  }, 8000);
};

const startDetection = async () => {
  if (!window.faceapi) {
    statusText.value = 'Face API not loaded.';
    scanState.value = 'error';
    return;
  }
  try {
    await window.faceapi.nets.tinyFaceDetector.loadFromUri('https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights');
    startCamera();
  } catch (err) {
    console.error(err);
    statusText.value = 'Error loading AI models.';
    scanState.value = 'error';
  }
};

const onPlay = () => {
  const video = videoRef.value;
  if (!video || !window.faceapi) return;

  detectionInterval = setInterval(async () => {
    if (scanState.value === 'success') return;

    const detections = await window.faceapi.detectAllFaces(video, new window.faceapi.TinyFaceDetectorOptions());

    if (detections.length > 0) {
      if (noFaceTimer) clearTimeout(noFaceTimer);

      if (scanState.value !== 'success') {
        scanState.value = 'success';
        statusText.value = 'Face Detected!';
        clearInterval(detectionInterval);
        stopCamera();

        // Auto-proceed to mark attendance after 1.5s
        setTimeout(() => handleMarkAttendance(), 1500);
      }
    }
  }, 100);
};

const stopCamera = () => {
  if (detectionInterval) clearInterval(detectionInterval);
  if (noFaceTimer) clearTimeout(noFaceTimer);
  if (videoRef.value && videoRef.value.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(track => track.stop());
  }
};

const retryFaceScan = () => {
  scanState.value = 'scanning';
  statusText.value = 'Retrying...';
  startCamera();
  resetNoFaceTimer();
};

// ===== STEP 4: MARK ATTENDANCE =====
const handleMarkAttendance = async () => {
  try {
    const result = await markAttendance(selectedEvent.value.id, studentId, true);
    checkInTime.value = result.checkIn;

    // Update local status so button changes to "Already Checked In"
    attendanceStatuses.value[selectedEvent.value.id] = {
      hasAttendance: true,
      record: result.record
    };

    step.value = 'success';
  } catch (err) {
    console.error('Failed to mark attendance:', err);
    statusText.value = 'Failed to mark attendance. Please try again.';
  }
};

// ===== NAVIGATION =====
const goBack = () => {
  stopCamera();
  if (step.value === 'success') {
    step.value = 'events';
    selectedEvent.value = null;
  } else if (step.value === 'facescan') {
    step.value = 'location';
  } else if (step.value === 'location') {
    step.value = 'events';
    selectedEvent.value = null;
  }
};
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6 animate-fade-in">

    <!-- Page Header -->
    <div class="flex items-center gap-3">
      <button
        v-if="step !== 'events'"
        @click="goBack"
        class="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-white/[0.06] text-gray-500 dark:text-gray-400 transition-colors"
      >
        <ChevronLeft class="w-5 h-5" />
      </button>
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ step === 'events' ? 'Mark Attendance' : step === 'location' ? 'Location Check' : step === 'facescan' ? 'Face Verification' : 'Attendance Confirmed' }}
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          {{ step === 'events' ? 'Select an event to check in' : step === 'location' ? 'Verifying your location' : step === 'facescan' ? 'Look at the camera' : 'You\'re all set!' }}
        </p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"></div>
    </div>

    <!-- ============================================ -->
    <!-- STEP 1: EVENT LIST -->
    <!-- ============================================ -->
    <template v-else-if="step === 'events'">

      <!-- Progress Steps Indicator -->
      <div class="glass-card p-3 sm:p-4">
        <div class="flex items-center justify-between text-xs">
          <div class="flex items-center gap-2 text-brand-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-brand-500 text-white flex items-center justify-center text-[0.65rem] font-bold">1</div>
            <span class="block whitespace-nowrap">Select Event</span>
          </div>
          <div class="flex-1 h-px bg-gray-200 dark:bg-white/10 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-gray-400">
            <div class="w-6 h-6 shrink-0 rounded-full bg-gray-200 dark:bg-white/10 text-gray-400 flex items-center justify-center text-[0.65rem] font-bold">2</div>
            <span class="hidden sm:block whitespace-nowrap">Location</span>
          </div>
          <div class="flex-1 h-px bg-gray-200 dark:bg-white/10 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-gray-400">
            <div class="w-6 h-6 shrink-0 rounded-full bg-gray-200 dark:bg-white/10 text-gray-400 flex items-center justify-center text-[0.65rem] font-bold">3</div>
            <span class="hidden sm:block whitespace-nowrap">Face Scan</span>
          </div>
          <div class="flex-1 h-px bg-gray-200 dark:bg-white/10 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-gray-400">
            <div class="w-6 h-6 shrink-0 rounded-full bg-gray-200 dark:bg-white/10 text-gray-400 flex items-center justify-center text-[0.65rem] font-bold">4</div>
            <span class="hidden sm:block whitespace-nowrap">Done</span>
          </div>
        </div>
      </div>

      <!-- Open for Attendance -->
      <div v-if="upcomingEvents.length">
        <h2 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Open for Attendance</h2>
        <div class="space-y-3">
          <div
            v-for="event in upcomingEvents"
            :key="event.id"
            class="glass-card p-5 hover:border-brand-500/30 dark:hover:border-brand-500/20 transition-all cursor-pointer"
            @click="!attendanceStatuses[event.id]?.hasAttendance && selectEvent(event)"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span class="text-[0.65rem] font-semibold uppercase tracking-wider text-emerald-500">Open</span>
                </div>
                <h3 class="font-semibold text-gray-900 dark:text-white">{{ event.name }}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ event.description }}</p>
                <div class="flex flex-wrap gap-3 mt-3 text-xs text-gray-500 dark:text-gray-400">
                  <span class="flex items-center gap-1"><Clock class="w-3.5 h-3.5" /> {{ event.date }} • {{ event.time }}</span>
                  <span class="flex items-center gap-1"><MapPin class="w-3.5 h-3.5" /> {{ event.location }}</span>
                  <span v-if="event.college" class="flex items-center gap-1"><Building2 class="w-3.5 h-3.5" /> {{ event.college }}</span>
                </div>
              </div>
              <div class="shrink-0">
                <span
                  v-if="attendanceStatuses[event.id]?.hasAttendance"
                  class="badge badge-green text-xs"
                >
                  <CheckCircle2 class="w-3 h-3" /> Checked In
                </span>
                <button
                  v-else
                  class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold rounded-xl transition-colors shadow-md shadow-brand-500/20"
                  @click.stop="selectEvent(event)"
                >
                  <ScanLine class="w-4 h-4 inline mr-1.5" />
                  Mark Attendance
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No Open Events -->
      <div v-else class="glass-card p-12 text-center">
        <Clock class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
        <h3 class="font-semibold text-gray-900 dark:text-white mb-1">No Events Open</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">There are no events accepting attendance right now.</p>
      </div>

      <!-- Other Events -->
      <div v-if="otherEvents.length">
        <h2 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Other Events</h2>
        <div class="space-y-2">
          <div
            v-for="event in otherEvents"
            :key="event.id"
            class="glass-card p-4 opacity-60"
          >
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-medium text-gray-900 dark:text-white text-sm">{{ event.name }}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ event.date }} • {{ event.location }}</p>
              </div>
              <span class="badge badge-gray text-[0.65rem]">{{ event.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ============================================ -->
    <!-- STEP 2: LOCATION CHECK -->
    <!-- ============================================ -->
    <template v-else-if="step === 'location'">

      <!-- Progress (step 2 active) -->
      <div class="glass-card p-3 sm:p-4">
        <div class="flex items-center justify-between text-xs">
          <div class="flex items-center gap-2 text-emerald-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[0.65rem] font-bold">✓</div>
            <span class="hidden sm:block whitespace-nowrap">Event</span>
          </div>
          <div class="flex-1 h-px bg-emerald-500 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-brand-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-brand-500 text-white flex items-center justify-center text-[0.65rem] font-bold">2</div>
            <span class="block whitespace-nowrap">Location</span>
          </div>
          <div class="flex-1 h-px bg-gray-200 dark:bg-white/10 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-gray-400">
            <div class="w-6 h-6 shrink-0 rounded-full bg-gray-200 dark:bg-white/10 text-gray-400 flex items-center justify-center text-[0.65rem] font-bold">3</div>
            <span class="hidden sm:block whitespace-nowrap">Face Scan</span>
          </div>
          <div class="flex-1 h-px bg-gray-200 dark:bg-white/10 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-gray-400">
            <div class="w-6 h-6 shrink-0 rounded-full bg-gray-200 dark:bg-white/10 text-gray-400 flex items-center justify-center text-[0.65rem] font-bold">4</div>
            <span class="hidden sm:block whitespace-nowrap">Done</span>
          </div>
        </div>
      </div>

      <!-- Event Info Card -->
      <div class="glass-card p-5">
        <h3 class="font-semibold text-gray-900 dark:text-white">{{ selectedEvent.name }}</h3>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1">
          <MapPin class="w-3.5 h-3.5" /> {{ selectedEvent.location }}
        </p>
      </div>

      <!-- Location Status -->
      <div class="glass-card p-8 flex flex-col items-center text-center">

        <!-- Checking -->
        <template v-if="locationStatus === 'checking'">
          <div class="w-20 h-20 rounded-full bg-brand-500/10 dark:bg-brand-500/20 flex items-center justify-center mb-4">
            <Loader2 class="w-10 h-10 text-brand-500 animate-spin" />
          </div>
          <h3 class="font-semibold text-gray-900 dark:text-white mb-1">Checking Location...</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">Please allow location access when prompted.</p>
        </template>

        <!-- Verified -->
        <template v-else-if="locationStatus === 'verified'">
          <div class="w-20 h-20 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 flex items-center justify-center mb-4">
            <CheckCircle2 class="w-10 h-10 text-emerald-500" />
          </div>
          <h3 class="font-semibold text-emerald-600 dark:text-emerald-400 mb-1">Location Verified!</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
            You're <strong class="text-gray-900 dark:text-white">{{ locationDistance }}m</strong> from {{ selectedEvent.location }}
          </p>
          <p class="text-xs text-gray-400">(within {{ locationMaxRadius }}m radius)</p>
          <button
            @click="proceedToFaceScan"
            class="mt-6 px-6 py-3 bg-brand-500 hover:bg-brand-600 text-white font-semibold rounded-xl transition-colors shadow-lg shadow-brand-500/25 flex items-center gap-2"
          >
            <Camera class="w-5 h-5" /> Proceed to Face Scan
          </button>
        </template>

        <!-- Too Far -->
        <template v-else-if="locationStatus === 'too_far'">
          <div class="w-20 h-20 rounded-full bg-amber-500/10 dark:bg-amber-500/20 flex items-center justify-center mb-4">
            <Navigation class="w-10 h-10 text-amber-500" />
          </div>
          <h3 class="font-semibold text-amber-600 dark:text-amber-400 mb-1">You're Too Far</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
            You're <strong class="text-gray-900 dark:text-white">{{ locationDistance }}m</strong> away from the event.
          </p>
          <p class="text-xs text-gray-400">You need to be within {{ locationMaxRadius }}m of {{ selectedEvent.location }}</p>
          <button @click="checkLocation(); locationStatus = 'checking'" class="mt-5 btn-ghost border border-gray-200 dark:border-gray-700 text-sm">
            Retry Location
          </button>
        </template>

        <!-- GPS Denied -->
        <template v-else-if="locationStatus === 'denied'">
          <div class="w-20 h-20 rounded-full bg-red-500/10 dark:bg-red-500/20 flex items-center justify-center mb-4">
            <AlertCircle class="w-10 h-10 text-red-500" />
          </div>
          <h3 class="font-semibold text-red-600 dark:text-red-400 mb-1">Location Access Denied</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 max-w-xs">
            Please enable location permissions in your browser settings and try again.
          </p>
          <button @click="checkLocation(); locationStatus = 'checking'" class="mt-5 btn-ghost border border-gray-200 dark:border-gray-700 text-sm">
            Retry
          </button>
        </template>

        <!-- Error -->
        <template v-else>
          <div class="w-20 h-20 rounded-full bg-red-500/10 dark:bg-red-500/20 flex items-center justify-center mb-4">
            <AlertCircle class="w-10 h-10 text-red-500" />
          </div>
          <h3 class="font-semibold text-red-600 dark:text-red-400 mb-1">Location Error</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">Unable to verify your location. Geolocation may not be supported.</p>
          <button @click="checkLocation(); locationStatus = 'checking'" class="mt-5 btn-ghost border border-gray-200 dark:border-gray-700 text-sm">
            Retry
          </button>
        </template>
      </div>
    </template>

    <!-- ============================================ -->
    <!-- STEP 3: FACE SCAN -->
    <!-- ============================================ -->
    <template v-else-if="step === 'facescan'">

      <!-- Progress (step 3 active) -->
      <div class="glass-card p-3 sm:p-4">
        <div class="flex items-center justify-between text-xs">
          <div class="flex items-center gap-2 text-emerald-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[0.65rem] font-bold">✓</div>
            <span class="hidden sm:block whitespace-nowrap">Event</span>
          </div>
          <div class="flex-1 h-px bg-emerald-500 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-emerald-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[0.65rem] font-bold">✓</div>
            <span class="hidden sm:block whitespace-nowrap">Location</span>
          </div>
          <div class="flex-1 h-px bg-emerald-500 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-brand-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-brand-500 text-white flex items-center justify-center text-[0.65rem] font-bold">3</div>
            <span class="block whitespace-nowrap">Face Scan</span>
          </div>
          <div class="flex-1 h-px bg-gray-200 dark:bg-white/10 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-gray-400">
            <div class="w-6 h-6 shrink-0 rounded-full bg-gray-200 dark:bg-white/10 text-gray-400 flex items-center justify-center text-[0.65rem] font-bold">4</div>
            <span class="hidden sm:block whitespace-nowrap">Done</span>
          </div>
        </div>
      </div>

      <!-- Face Scan Card -->
      <div class="glass-card p-8 flex flex-col items-center">

        <!-- Animation -->
        <FaceScanAnimation :state="scanState" />

        <!-- Camera Preview -->
        <div
          class="relative w-[200px] h-[200px] sm:w-[240px] sm:h-[240px] mx-auto rounded-full border-4 overflow-hidden shadow-lg bg-black transition-all duration-500"
          :class="{
            'border-gray-600/30 shadow-[0_0_30px_rgba(75,78,255,0.2)]': scanState === 'scanning',
            'border-emerald-500 shadow-[0_0_40px_rgba(0,230,118,0.3)] opacity-50': scanState === 'success',
            'border-red-500 shadow-[0_0_40px_rgba(239,68,68,0.3)]': scanState === 'error'
          }"
        >
          <video
            ref="videoRef"
            autoplay playsinline muted
            class="w-full h-full object-cover transform -scale-x-100"
            @play="onPlay"
          ></video>

          <!-- Scan Line -->
          <div v-if="scanState === 'scanning'" class="absolute top-0 left-0 w-full h-full rounded-full z-10 shadow-[inset_0_0_20px_#000]">
            <div class="w-full h-[4px] bg-brand-500 shadow-[0_0_15px_var(--brand-500)] absolute top-0 animate-scanMove"></div>
          </div>
        </div>

        <!-- Status -->
        <p
          class="mt-5 text-center font-medium transition-colors duration-300"
          :class="{
            'text-gray-500 dark:text-gray-400': scanState === 'scanning',
            'text-emerald-500': scanState === 'success',
            'text-red-500 animate-pulse': scanState === 'error'
          }"
        >
          {{ statusText }}
        </p>

        <!-- Retry -->
        <button
          v-if="scanState === 'error'"
          @click="retryFaceScan"
          class="mt-4 px-5 py-2 btn-ghost border border-gray-200 dark:border-gray-700 text-sm flex items-center gap-2"
        >
          Try Again
        </button>

        <p v-if="scanState === 'success'" class="text-xs text-gray-400 mt-2">Marking attendance...</p>
      </div>
    </template>

    <!-- ============================================ -->
    <!-- STEP 4: SUCCESS -->
    <!-- ============================================ -->
    <template v-else-if="step === 'success'">

      <!-- Progress (all done) -->
      <div class="glass-card p-3 sm:p-4">
        <div class="flex items-center justify-between text-xs">
          <div class="flex items-center gap-2 text-emerald-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[0.65rem] font-bold">✓</div>
            <span class="hidden sm:block whitespace-nowrap">Event</span>
          </div>
          <div class="flex-1 h-px bg-emerald-500 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-emerald-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[0.65rem] font-bold">✓</div>
            <span class="hidden sm:block whitespace-nowrap">Location</span>
          </div>
          <div class="flex-1 h-px bg-emerald-500 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-emerald-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[0.65rem] font-bold">✓</div>
            <span class="hidden sm:block whitespace-nowrap">Face Scan</span>
          </div>
          <div class="flex-1 h-px bg-emerald-500 mx-2 sm:mx-3"></div>
          <div class="flex items-center gap-2 text-emerald-500 font-semibold">
            <div class="w-6 h-6 shrink-0 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[0.65rem] font-bold">✓</div>
            <span class="block whitespace-nowrap">Done</span>
          </div>
        </div>
      </div>

      <!-- Success Card -->
      <div class="glass-card p-10 flex flex-col items-center text-center">
        <div class="w-24 h-24 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 flex items-center justify-center mb-5 animate-bounce-once">
          <CheckCircle2 class="w-14 h-14 text-emerald-500" />
        </div>

        <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">Attendance Marked!</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          You've successfully checked in for <strong class="text-gray-900 dark:text-white">{{ selectedEvent.name }}</strong>
        </p>

        <div class="bg-gray-50 dark:bg-white/[0.03] rounded-xl p-5 w-full max-w-sm border border-gray-100 dark:border-white/[0.06]">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Student</p>
              <p class="font-semibold text-gray-900 dark:text-white">{{ currentUser?.name }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Student ID</p>
              <p class="font-semibold text-gray-900 dark:text-white">{{ studentId }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Check-in Time</p>
              <p class="font-semibold text-emerald-600 dark:text-emerald-400">{{ checkInTime }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-0.5">Status</p>
              <span class="badge badge-green text-xs">Present</span>
            </div>
          </div>
        </div>

        <button
          @click="goBack"
          class="mt-6 px-6 py-2.5 btn-ghost border border-gray-200 dark:border-gray-700 text-sm font-semibold"
        >
          Back to Events
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
@keyframes scanMove {
  0% { top: 0%; opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

.animate-scanMove {
  animation: scanMove 2s infinite ease-in-out;
}

@keyframes bounceOnce {
  0% { transform: scale(0.3); opacity: 0; }
  50% { transform: scale(1.1); }
  70% { transform: scale(0.95); }
  100% { transform: scale(1); opacity: 1; }
}

.animate-bounce-once {
  animation: bounceOnce 0.6s ease-out;
}
</style>
