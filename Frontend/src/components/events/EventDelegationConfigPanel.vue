<template>
  <section class="delegation-panel">
    <header class="delegation-panel__header">
      <h3 class="delegation-panel__title">Delegation</h3>
      <p class="delegation-panel__copy">
        Assign event sanction management downward from department councils to organizations.
      </p>
    </header>

    <div class="delegation-panel__grid">
      <label class="delegation-panel__field">
        <span>Department Council (SG)</span>
        <select
          :value="selectedSgId"
          :disabled="disabled"
          @change="handleSgChange"
        >
          <option value="">No SG delegation</option>
          <option
            v-for="unit in sgUnits"
            :key="unit.id"
            :value="String(unit.id)"
          >
            {{ unit.unit_name || unit.unit_code || `SG #${unit.id}` }}
          </option>
        </select>
      </label>

      <label class="delegation-panel__field">
        <span>Organization (ORG)</span>
        <select
          :value="selectedOrgId"
          :disabled="disabled || !filteredOrgUnits.length"
          @change="handleOrgChange"
        >
          <option value="">No ORG delegation</option>
          <option
            v-for="unit in filteredOrgUnits"
            :key="unit.id"
            :value="String(unit.id)"
          >
            {{ unit.unit_name || unit.unit_code || `ORG #${unit.id}` }}
          </option>
        </select>
      </label>
    </div>

    <p class="delegation-panel__note">
      Delegations are saved per event and scoped according to governance hierarchy rules.
    </p>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  governanceUnits: {
    type: Array,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const selectedSgId = ref('')
const selectedOrgId = ref('')

const normalizedUnits = computed(() => (
  Array.isArray(props.governanceUnits)
    ? props.governanceUnits
      .filter((unit) => Number.isFinite(Number(unit?.id)))
      .map((unit) => ({
        ...unit,
        id: Number(unit.id),
        parent_unit_id: Number.isFinite(Number(unit?.parent_unit_id))
          ? Number(unit.parent_unit_id)
          : null,
        department_id: Number.isFinite(Number(unit?.department_id))
          ? Number(unit.department_id)
          : null,
      }))
    : []
))

const sgUnits = computed(() => (
  normalizedUnits.value.filter((unit) => String(unit.unit_type || '').toUpperCase() === 'SG')
))

const orgUnits = computed(() => (
  normalizedUnits.value.filter((unit) => String(unit.unit_type || '').toUpperCase() === 'ORG')
))

const filteredOrgUnits = computed(() => {
  const sgId = Number(selectedSgId.value)
  if (!Number.isFinite(sgId)) {
    return orgUnits.value
  }

  const selectedSg = sgUnits.value.find((unit) => unit.id === sgId) || null
  if (!selectedSg) {
    return orgUnits.value
  }

  const byParent = orgUnits.value.filter((unit) => unit.parent_unit_id === selectedSg.id)
  if (byParent.length) return byParent

  if (selectedSg.department_id != null) {
    const byDepartment = orgUnits.value.filter((unit) => unit.department_id === selectedSg.department_id)
    if (byDepartment.length) return byDepartment
  }

  return orgUnits.value
})

watch(
  () => [props.modelValue, normalizedUnits.value.length],
  () => {
    hydrateSelectionsFromModel()
  },
  { immediate: true, deep: true }
)

function hydrateSelectionsFromModel() {
  const delegations = Array.isArray(props.modelValue) ? props.modelValue : []

  const currentSgDelegation = delegations.find((item) => {
    const delegatedUnitId = Number(item?.delegated_to_governance_unit_id)
    if (!Number.isFinite(delegatedUnitId)) return false
    return sgUnits.value.some((unit) => unit.id === delegatedUnitId)
  })
  const currentOrgDelegation = delegations.find((item) => {
    const delegatedUnitId = Number(item?.delegated_to_governance_unit_id)
    if (!Number.isFinite(delegatedUnitId)) return false
    return orgUnits.value.some((unit) => unit.id === delegatedUnitId)
  })

  selectedSgId.value = Number.isFinite(Number(currentSgDelegation?.delegated_to_governance_unit_id))
    ? String(currentSgDelegation.delegated_to_governance_unit_id)
    : ''
  selectedOrgId.value = Number.isFinite(Number(currentOrgDelegation?.delegated_to_governance_unit_id))
    ? String(currentOrgDelegation.delegated_to_governance_unit_id)
    : ''
}

function emitDelegations() {
  const nextDelegations = []
  const sgId = Number(selectedSgId.value)
  const orgId = Number(selectedOrgId.value)

  if (Number.isFinite(sgId)) {
    nextDelegations.push({
      delegated_to_governance_unit_id: sgId,
      scope_type: 'unit',
      is_active: true,
    })
  }

  if (Number.isFinite(orgId)) {
    nextDelegations.push({
      delegated_to_governance_unit_id: orgId,
      scope_type: 'unit',
      is_active: true,
    })
  }

  emit('update:modelValue', nextDelegations)
}

function handleSgChange(event) {
  selectedSgId.value = String(event?.target?.value || '')
  if (
    selectedOrgId.value
    && !filteredOrgUnits.value.some((unit) => unit.id === Number(selectedOrgId.value))
  ) {
    selectedOrgId.value = ''
  }
  emitDelegations()
}

function handleOrgChange(event) {
  selectedOrgId.value = String(event?.target?.value || '')
  emitDelegations()
}
</script>

<style scoped>
.delegation-panel {
  display: grid;
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-surface) 92%, transparent);
}

.delegation-panel__header {
  display: grid;
  gap: 4px;
}

.delegation-panel__title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: var(--color-text-primary);
}

.delegation-panel__copy {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-muted);
}

.delegation-panel__grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.delegation-panel__field {
  display: grid;
  gap: 6px;
}

.delegation-panel__field span {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.delegation-panel__field select {
  width: 100%;
  border: 1px solid color-mix(in srgb, var(--color-text-muted) 20%, transparent);
  border-radius: 12px;
  background: #fff;
  min-height: 42px;
  padding: 0 12px;
  font-family: inherit;
  font-size: 13px;
  color: var(--color-text-primary);
  outline: none;
  box-sizing: border-box;
}

.delegation-panel__note {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-muted);
}

@media (max-width: 760px) {
  .delegation-panel__grid {
    grid-template-columns: 1fr;
  }
}
</style>
