<template>
  <div
    class="app-boot-loader"
    role="status"
    aria-live="polite"
    aria-label="Loading application"
  >
    <svg class="app-boot-loader__filter" aria-hidden="true" focusable="false">
      <defs>
        <filter id="app-boot-loader-goo">
          <feGaussianBlur in="SourceGraphic" stdDeviation="12" />
          <feColorMatrix
            values="0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 48 -7"
          />
        </filter>
      </defs>
    </svg>

    <div class="app-boot-loader__animation" aria-hidden="true"></div>
    <span class="app-boot-loader__sr-only">Loading application</span>
  </div>
</template>

<style scoped>
.app-boot-loader {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  background: #ffffff;
}

.app-boot-loader__filter {
  position: absolute;
  width: 0;
  height: 0;
  pointer-events: none;
}

.app-boot-loader__animation {
  position: relative;
  width: clamp(10rem, 26vw, 12rem);
  height: clamp(2.5rem, 7vw, 3rem);
  overflow: hidden;
  border-bottom: 8px solid var(--color-text-primary, #0a0a0a);
  filter: url(#app-boot-loader-goo);
}

.app-boot-loader__animation::before,
.app-boot-loader__animation::after {
  content: '';
  position: absolute;
  border-radius: 999px;
  will-change: transform;
}

.app-boot-loader__animation::before {
  width: 22em;
  height: 18em;
  left: -2em;
  bottom: -18em;
  background: color-mix(in srgb, var(--color-primary, #111111) 88%, white);
  animation: app-boot-loader-wave-primary 2s linear infinite;
}

.app-boot-loader__animation::after {
  width: 16em;
  height: 12em;
  left: -4em;
  bottom: -12em;
  background: color-mix(in srgb, var(--color-secondary, #5f5f5f) 84%, white);
  animation: app-boot-loader-wave-secondary 2s linear infinite 0.75s;
}

.app-boot-loader__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@keyframes app-boot-loader-wave-primary {
  0% {
    transform: translateX(-10em) rotate(0deg);
  }

  100% {
    transform: translateX(7em) rotate(180deg);
  }
}

@keyframes app-boot-loader-wave-secondary {
  0% {
    transform: translateX(-8em) rotate(0deg);
  }

  100% {
    transform: translateX(8em) rotate(180deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-boot-loader__animation::before,
  .app-boot-loader__animation::after {
    animation-duration: 0.01ms;
    animation-iteration-count: 1;
  }
}
</style>
