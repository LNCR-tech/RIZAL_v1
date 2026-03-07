<script setup>
// Pure animated CSS loader component
</script>

<template>
  <div class="loader-overlay fixed inset-0 z-[1000] flex items-center justify-center backdrop-blur-[6px] bg-black/10">
    <div class="spinner"></div>
  </div>
</template>

<style scoped>
.loader-overlay {
  animation: fadeIn 0.3s ease-in-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.spinner {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
}

.spinner::before,
.spinner::after {
  content: "";
  position: absolute;
  border-radius: inherit;
}

.spinner::before {
  width: 100%;
  height: 100%;
  /* Swapped #ff00cc to the requested #1906c7 brand color */
  background-image: linear-gradient(0deg, #1906c7 0%, transparent 50%);
  animation: spin .5s infinite linear;
}

.spinner::after {
  width: 85%;
  height: 85%;
  background-color: #000; /* Matching the black void of the app instead of grey */
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
