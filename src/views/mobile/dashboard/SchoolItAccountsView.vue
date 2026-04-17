<template>
  <section class="accounts-view">
    <div class="accounts-view__shell">
      <SchoolItTopHeader
        :avatar-url="avatarUrl"
        :school-name="schoolName"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <header class="accounts-view__hero">
        <div>
          <p class="accounts-view__eyebrow">School Administration</p>
          <h1 class="accounts-view__title">Admins</h1>
          <p class="accounts-view__subtitle">Manage fellow campus administrators.</p>
        </div>
      </header>

      <section class="accounts-view__toolbar">
        <label class="accounts-view__search">
          <input
            v-model.trim="searchQuery"
            class="accounts-view__search-input"
            placeholder="Search admins..."
            type="search"
          >
          <Search :size="18" class="accounts-view__search-icon" />
        </label>

        <button class="accounts-view__pill" type="button" @click="refreshAccounts">
          <RefreshCw :size="18" :class="{ 'accounts-view__spinner': statuses.itAccounts === 'loading' }" />
        </button>
      </section>

      <p v-if="feedback.message" class="accounts-view__feedback" :class="`accounts-view__feedback--${feedback.type}`">
        {{ feedback.message }}
      </p>

      <div class="accounts-view__stack">
        <article v-for="account in filteredAccounts" :key="account.user_id" class="accounts-view__card">
          <div class="accounts-view__card-head">
            <div>
              <h2>{{ formatPersonName(account.first_name, account.last_name) }}</h2>
              <p class="accounts-view__muted">{{ account.email }}</p>
            </div>
            <span class="accounts-view__badge" :class="{ 'accounts-view__badge--muted': !account.is_active }">
              {{ account.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>

          <div class="accounts-view__actions">
            <button class="accounts-view__ghost accounts-view__ghost--primary" type="button" @click="handleResetPassword(account)">
              <KeyRound :size="16" />
              <span>Reset Password</span>
            </button>
          </div>
        </article>
      </div>

      <div v-if="!filteredAccounts.length && statuses.itAccounts === 'ready'" class="accounts-view__empty">
        <Users :size="48" />
        <p>No administrators found</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { KeyRound, RefreshCw, Search, Users } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/mobile/dashboard/SchoolItTopHeader.vue'
import { useSchoolItAccountsLogic } from '@/composables/useSchoolItAccountsLogic.js'

const {
  searchQuery,
  feedback,
  filteredAccounts,
  displayName,
  avatarUrl,
  initials,
  schoolName,
  statuses,
  refreshAccounts,
  handleResetPassword,
  handleLogout,
  formatPersonName
} = useSchoolItAccountsLogic()
</script>

<style scoped>
.accounts-view{min-height:100vh;padding:26px 18px 120px;font-family:'Manrope',sans-serif}
.accounts-view__shell{width:100%;max-width:1180px;margin:0 auto}
.accounts-view__hero{margin-top:24px}
.accounts-view__eyebrow{margin:0 0 6px;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--color-text-muted)}
.accounts-view__title{margin:0;font-size:38px;line-height:.96;letter-spacing:-.06em;color:var(--color-text-primary)}
.accounts-view__subtitle{margin:10px 0 0;font-size:15px;line-height:1.6;color:var(--color-text-secondary)}
.accounts-view__toolbar{margin-top:18px;display:flex;gap:12px}
.accounts-view__search{flex:1;display:flex;align-items:center;gap:12px;min-height:58px;padding:0 18px;border-radius:999px;background:var(--color-surface);box-shadow:0 8px 24px rgba(15,23,42,.04)}
.accounts-view__search-input{flex:1;border:none;outline:none;background:transparent;color:var(--color-text-primary);font:inherit;font-size:15px}
.accounts-view__search-icon{color:var(--color-primary)}
.accounts-view__pill{width:58px;height:58px;border-radius:999px;border:none;background:var(--color-secondary);color:var(--color-secondary-text);display:grid;place-items:center}
.accounts-view__feedback{margin:16px 0 0;padding:14px 18px;border-radius:20px;background:rgba(255,255,255,.9);font-size:14px;font-weight:600;box-shadow:0 4px 12px rgba(0,0,0,0.05)}
.accounts-view__feedback--success{color:#166534;border-left:4px solid #166534}
.accounts-view__feedback--error{color:#B42318;border-left:4px solid #B42318}
.accounts-view__stack{display:flex;flex-direction:column;gap:16px;margin-top:24px}
.accounts-view__card{background:var(--color-surface);border-radius:28px;padding:20px;box-shadow:0 12px 32px rgba(15,23,42,.04)}
.accounts-view__card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.accounts-view__card h2{margin:0;font-size:22px;color:var(--color-text-primary);line-height:1.1}
.accounts-view__muted{margin:4px 0 0;font-size:14px;color:var(--color-text-secondary)}
.accounts-view__badge{font-size:11px;font-weight:800;text-transform:uppercase;padding:4px 10px;border-radius:999px;background:var(--color-primary);color:var(--color-primary-text)}
.accounts-view__badge--muted{background:var(--color-field-surface);color:var(--color-text-muted)}
.accounts-view__actions{margin-top:16px;padding-top:16px;border-top:1px solid var(--color-field-surface)}
.accounts-view__ghost{width:100%;min-height:48px;border-radius:999px;border:none;background:var(--color-field-surface);color:var(--color-text-primary);display:flex;align-items:center;justify-content:center;gap:8px;font-weight:700}
.accounts-view__ghost--primary{background:var(--color-secondary);color:var(--color-secondary-text)}
.accounts-view__empty{display:flex;flex-direction:column;align-items:center;padding:60px 0;color:var(--color-text-muted)}
.accounts-view__spinner{animation:accounts-view-spin .9s linear infinite}
@keyframes accounts-view-spin{to{transform:rotate(360deg)}}
</style>
