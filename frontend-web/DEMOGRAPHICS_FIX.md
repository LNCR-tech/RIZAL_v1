# Campus Admin Homepage Demographics Fix

## Problem
The Campus Admin (School IT) homepage was displaying hardcoded random numbers (like 48 students) in the College Demographics chart, even when there were no students in the database. This was misleading and didn't reflect actual data.

## Root Cause
In `SchoolItHomeView.vue`, the `collegeDemographics` computed property had fallback logic that generated random student counts when:
- No students existed in the database, OR
- Only unassigned students existed

The problematic code (lines 430-445):
```javascript
if (countsByDept.size === 0 || (countsByDept.size === 1 && countsByDept.has('unassigned'))) {
  if (filteredDepartments.value.length >= 2) {
    return filteredDepartments.value.slice(0, 4).map((dept, idx) => ({
      id: dept.id,
      shortLabel: dept.acronym || dept.name,
      count: Math.floor(Math.random() * 500) + 100,  // ❌ HARDCODED RANDOM DATA
      color: VIBRANT_COLORS[idx % VIBRANT_COLORS.length]
    })).sort((a, b) => b.count - a.count)
  }
}
```

## Solution

### 1. Removed Hardcoded Random Data Generation
**File:** `src/views/dashboard/SchoolItHomeView.vue`

Removed the fallback logic that generated random student counts. Now the component:
- Returns an empty array when no students exist
- Shows actual student counts from the database
- Properly handles unassigned students

**After:**
```javascript
const collegeDemographics = computed(() => {
  const students = filteredUsers.value.filter((user) => String(user.role || '').toLowerCase() === 'student')
  
  const countsByDept = new Map()
  students.forEach((student) => {
    const deptId = Number(student?.student_profile?.department_id)
    if (Number.isFinite(deptId)) {
      countsByDept.set(deptId, (countsByDept.get(deptId) || 0) + 1)
    } else {
      countsByDept.set('unassigned', (countsByDept.get('unassigned') || 0) + 1)
    }
  })

  // If no students at all, return empty array
  if (countsByDept.size === 0) {
    return []
  }

  // ... rest of the logic to build demographics from actual data
})
```

### 2. Fixed Total Student Count Calculation
**File:** `src/views/dashboard/SchoolItHomeView.vue`

Changed from summing demographics (which could include fake data) to directly counting students:

**Before:**
```javascript
const totalSchoolStudents = computed(() => {
  return collegeDemographics.value.reduce((acc, item) => acc + item.count, 0)
})
```

**After:**
```javascript
const totalSchoolStudents = computed(() => {
  // Calculate total from actual student count
  const students = filteredUsers.value.filter((user) => String(user.role || '').toLowerCase() === 'student')
  return students.length
})
```

### 3. Added Empty State UI
**File:** `src/components/dashboard/SchoolItDemographicsChart.vue`

Added a user-friendly empty state when no student data is available:

- Shows a users icon
- Displays "No student data available"
- Provides helpful hint: "Import students to see demographics"
- Only shows the chart and legend when actual data exists

**Changes:**
- Added `hasData` computed property to check if there's actual data
- Conditional rendering: `v-if="hasData"` on chart and legend
- New empty state section with icon and messaging
- Added CSS styles for empty state

## Benefits

1. **Accurate Data**: Shows only real student counts from the database
2. **No Misleading Information**: No fake/random numbers displayed
3. **Better UX**: Clear empty state guides users to import students
4. **Data Integrity**: Total student count matches actual database records
5. **Transparency**: Users can trust the numbers they see

## Testing

To verify the fix:

1. **With No Students:**
   - Login as Campus Admin
   - Navigate to Home
   - Should see "No student data available" message
   - Total students should show "0"

2. **With Students:**
   - Import students via bulk import
   - Navigate to Home
   - Should see actual student counts per department
   - Total should match the number of imported students
   - Demographics chart should show real distribution

3. **With Unassigned Students:**
   - Students without department assignment
   - Should appear as "Unassigned" in the chart
   - Should be counted in the total

## Files Modified

1. `src/views/dashboard/SchoolItHomeView.vue`
   - Removed hardcoded random data generation
   - Fixed total student count calculation

2. `src/components/dashboard/SchoolItDemographicsChart.vue`
   - Added empty state UI
   - Added conditional rendering for chart/legend
   - Added CSS for empty state styling

## Impact

- ✅ No breaking changes
- ✅ Backward compatible
- ✅ Works with existing data
- ✅ Improves data accuracy
- ✅ Better user experience
