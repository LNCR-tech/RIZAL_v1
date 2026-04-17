<template>
  <section class="accounts-view">
    <div class="accounts-view__shell">
      <StandardHeader
        :avatar-url="avatarUrl"
        :school-name="schoolName"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />
      <div class="accounts-view__breadcrumbs">
        <Breadcrumbs />
      </div>

      <header class="accounts-view__hero">
        <div>
          <p class="accounts-view__eyebrow">School Administration</p>
          <h1 class="accounts-view__title">Campus Admin Accounts</h1>
          <p class="accounts-view__subtitle">Manage fellow administrators and reset credentials for your campus.</p>
        </div>
      </header>

      <section class="accounts-view__toolbar">
        <AuraSearch
          v-model="searchQuery"
          placeholder="Search administrators by name or email..."
          class="accounts-view__search"
        />

        <button class="accounts-view__pill" type="button" @click="refreshAccounts">
          <span class="accounts-view__pill-icon">
            <RefreshCw :size="16" :class="{ 'accounts-view__spinner': statuses.itAccounts === 'loading' }" />
          </span>
          <span>Refresh List</span>
        </button>
      </section>

      <p v-if="feedback.message" class="accounts-view__feedback" :class="`accounts-view__feedback--${feedback.type}`">
        {{ feedback.message }}
      </p>

      <div class="accounts-view__grid">
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
             <div class="accounts-view__status-info">
                <ShieldCheck v-if="account.is_active" :size="16" />
                <Lock v-else :size="16" />
                <span>{{ account.is_active ? 'Authorized Access' : 'Access Suspended' }}</span>
             </div>
            <button class="accounts-view__ghost accounts-view__ghost--primary" type="button" @click="handleResetPassword(account)">
              <KeyRound :size="16" />
              <span>Reset Password</span>
            </button>
          </div>
        </article>
      </div>

      <div v-if="!filteredAccounts.length && statuses.itAccounts === 'ready'" class="accounts-view__empty">
        <Users :size="48" />
        <h3>No administrators found</h3>
        <p>Try adjusting your search query.</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { KeyRound, Lock, RefreshCw, ShieldCheck, Users } from 'lucide-vue-next'
import StandardHeader from '@/components/desktop/dashboard/StandardHeader.vue'
import Breadcrumbs from '@/components/desktop/dashboard/Breadcrumbs.vue'
import AuraSearch from '@/components/desktop/dashboard/AuraSearch.vue'
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
.accounts-view{min-height:100vh;padding:30px 28px 120px;font-family:'Manrope',sans-serif}
.accounts-view__shell{width:100%;max-width:1180px;margin:0 auto}
.accounts-view__hero,.accounts-view__toolbar,.accounts-view__card-head,.accounts-view__actions{display:flex;align-items:center;justify-content:space-between;gap:14px}
.accounts-view__hero{margin-top:24px;align-items:flex-end}
.accounts-view__eyebrow{margin:0 0 6px;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--color-text-muted)}
.accounts-view__title{margin:0;font-size:clamp(34px,4vw,52px);line-height:.96;letter-spacing:-.06em;color:var(--color-text-primary)}
.accounts-view__subtitle{margin:10px 0 0;max-width:620px;font-size:15px;line-height:1.6;color:var(--color-text-secondary)}
.accounts-view__toolbar{margin-top:24px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px}
.accounts-view__search{flex:1;min-width:0}
.accounts-view__pill,.accounts-view__ghost{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:none;border-radius:999px;font-weight:700}
.accounts-view__pill{min-height:62px;padding:0 24px;background:var(--color-secondary);color:var(--color-secondary-text);cursor:pointer}
.accounts-view__pill-icon{width:36px;height:36px;border-radius:999px;display:grid;place-items:center;background:#0A0A0A;color:#fff}
.accounts-view__ghost{min-height:42px;padding:0 16px;background:var(--color-field-surface);color:var(--color-text-primary);cursor:pointer}
.accounts-view__ghost--primary{background:var(--color-secondary);color:var(--color-secondary-text)}
.accounts-view__feedback{margin:16px 0 0;padding:16px 20px;border-radius:22px;background:rgba(255,255,255,.8);font-size:15px;font-weight:600;box-shadow: 0 4px 12px rgba(0,0,0,0.05)}
.accounts-view__feedback--success{color:#166534;border-left: 4px solid #22c55e}
.accounts-view__feedback--error{color:#B42318;border-left: 4px solid #ef4444}
.accounts-view__grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:32px}
.accounts-view__card{background:var(--color-surface);border-radius:32px;padding:26px;box-shadow:0 18px 40px rgba(15,23,42,.04)}
.accounts-view__card h2{margin:0;color:var(--color-text-primary);line-height:1.05;letter-spacing:-.04em;font-size:26px}
.accounts-view__muted{margin:6px 0 0;font-size:14px;line-height:1.5;color:var(--color-text-secondary)}
.accounts-view__badge{display:inline-flex;align-items:center;justify-content:center;min-height:32px;padding:0 14px;border-radius:999px;background:var(--color-primary);color:var(--color-primary-text);font-size:12px;font-weight:700}
.accounts-view__badge--muted{background:var(--color-field-surface);color:var(--color-text-secondary)}
.accounts-view__actions{margin-top:24px;padding-top:20px;border-top:1px solid var(--color-field-surface)}
.accounts-view__status-info{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:var(--color-text-secondary)}
.accounts-view__empty{grid-column:1 / -1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 0;color:var(--color-text-muted);text-align:center}
.accounts-view__empty h3{margin:16px 0 4px;color:var(--color-text-primary)}
.accounts-view__spinner{animation:accounts-view-spin .9s linear infinite}
@keyframes accounts-view-spin{to{transform:rotate(360deg)}}
.accounts-view__breadcrumbs { margin: 12px 0; padding: 0 4px; }

@media (max-width:900px){.accounts-view__grid{grid-template-columns:1fr}}
@media (max-width:600px){
  .accounts-view{padding:26px 18px 118px}
  .accounts-view__toolbar{grid-template-columns:1fr}
  .accounts-view__hero,.accounts-view__card-head,.accounts-view__actions{flex-direction:column;align-items:stretch}
  .accounts-view__pill{width:100%}
}
</style>
