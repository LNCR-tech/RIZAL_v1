<script setup>
</script>

<template>
  <div class="app-boot-loader">
    <div class="app-boot-spinner"></div>
  </div>
</template>

<style scoped>
.app-boot-loader {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.app-boot-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top-color: var(--color-primary, #0A0A0A);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
