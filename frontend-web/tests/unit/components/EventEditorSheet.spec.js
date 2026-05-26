import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import EventEditorSheet from '@/components/events/EventEditorSheet.vue'

const LocationPickerStub = {
  props: ['locationLabel'],
  emits: ['update:locationLabel'],
  template: `
    <label data-testid="location-picker-stub">
      <span>Location</span>
      <input
        name="event_location"
        :value="locationLabel"
        @input="$emit('update:locationLabel', $event.target.value)"
      >
    </label>
  `,
}

function mountSheet(extraProps = {}) {
  return mount(EventEditorSheet, {
    props: {
      isOpen: true,
      departments: [{ id: 10, name: 'College of Computing' }],
      programs: [{ id: 20, name: 'BS Information Systems' }],
      ...extraProps,
    },
    global: {
      stubs: {
        EventLocationPicker: LocationPickerStub,
      },
    },
  })
}

async function fillRequiredEventFields(wrapper) {
  await wrapper.find('input[name="event_name"]').setValue('Automated Year Filter Event')
  await wrapper.find('input[name="event_start_datetime"]').setValue('2099-01-01T09:00')
  await wrapper.find('input[name="event_end_datetime"]').setValue('2099-01-01T11:00')
  await wrapper.find('input[name="event_location"]').setValue('Automation Hall')
}

describe('EventEditorSheet audience year filters', () => {
  it('shows only the year-level field for YEAR_LEVEL and emits the expected event target', async () => {
    // This component test verifies the create/edit sheet turns a year-only
    // audience selection into the backend event_targets payload.
    const wrapper = mountSheet()
    await fillRequiredEventFields(wrapper)

    await wrapper.get('[data-testid="audience-scope-select"]').setValue('YEAR_LEVEL')
    expect(wrapper.find('[data-testid="year-level-field"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="department-field"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="course-field"]').exists()).toBe(false)

    await wrapper.get('[data-testid="year-level-select"]').setValue('4')
    await wrapper.get('form').trigger('submit')

    const payload = wrapper.emitted('save')?.[0]?.[0]
    expect(payload.event_targets).toEqual([{ scope_type: 'YEAR_LEVEL', year_level: 4 }])
  })

  it('shows department plus year for DEPARTMENT_YEAR and emits both filters', async () => {
    // This component test protects the combined department + year audience
    // path so the UI cannot drop either required backend field.
    const wrapper = mountSheet()
    await fillRequiredEventFields(wrapper)

    await wrapper.get('[data-testid="audience-scope-select"]').setValue('DEPARTMENT_YEAR')
    expect(wrapper.find('[data-testid="year-level-field"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="department-field"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="course-field"]').exists()).toBe(false)

    await wrapper.get('[data-testid="year-level-select"]').setValue('3')
    await wrapper.get('[data-testid="department-select"]').setValue('10')
    await wrapper.get('form').trigger('submit')

    const payload = wrapper.emitted('save')?.[0]?.[0]
    expect(payload.event_targets).toEqual([
      { scope_type: 'DEPARTMENT_YEAR', department_id: 10, year_level: 3 },
    ])
  })

  it('shows course plus year for COURSE_YEAR and emits both filters', async () => {
    // This component test protects the combined course + year audience path
    // used by organization-scoped events.
    const wrapper = mountSheet()
    await fillRequiredEventFields(wrapper)

    await wrapper.get('[data-testid="audience-scope-select"]').setValue('COURSE_YEAR')
    expect(wrapper.find('[data-testid="year-level-field"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="course-field"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="department-field"]').exists()).toBe(false)

    await wrapper.get('[data-testid="year-level-select"]').setValue('2')
    await wrapper.get('[data-testid="course-select"]').setValue('20')
    await wrapper.get('form').trigger('submit')

    const payload = wrapper.emitted('save')?.[0]?.[0]
    expect(payload.event_targets).toEqual([
      { scope_type: 'COURSE_YEAR', course_id: 20, year_level: 2 },
    ])
  })
})
