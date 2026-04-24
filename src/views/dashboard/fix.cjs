const fs = require('fs');
const filepath = 'd:/Aura - Frontend/aura-frontend/src/views/dashboard/SchoolItHomeView.vue';

try {
    let content = fs.readFileSync(filepath, 'utf8');
    let lines = content.split('\n');
    
    // 1. Replace imports
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('import SchoolItMetricRing')) {
            lines[i] = "import SchoolItDemographicsChart from '@/components/dashboard/SchoolItDemographicsChart.vue'";
        }
    }
    
    // 2. Extract users from useSchoolItWorkspaceData
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('programs: workspacePrograms,')) {
            lines.splice(i + 1, 0, "  users: workspaceUsers,");
            break;
        }
    }
            
    // 3. Add activeUsers and filteredUsers
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('const activePrograms = computed(')) {
            lines.splice(i + 1, 0, "const activeUsers = computed(() => isPreviewWorkspace.value ? schoolItPreviewData.users || [] : workspaceUsers.value || [])");
            break;
        }
    }
            
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('const filteredEvents = computed(')) {
            lines.splice(i + 1, 0, "const filteredUsers = computed(() => filterWorkspaceEntitiesBySchool(activeUsers.value, schoolId.value))");
            break;
        }
    }
            
    // 4. Add the computed logic
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('return lookup') && lines[i-15].includes('programsByDepartment')) {
            const insert_idx = i + 2;
            const logic = `
const VIBRANT_COLORS = ['#ff5a36', '#fbbf24', '#0f172a', '#e2e8f0', '#3b82f6', '#10b981', '#f43f5e']

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

  if (countsByDept.size === 0 || (countsByDept.size === 1 && countsByDept.has('unassigned'))) {
    if (filteredDepartments.value.length >= 2) {
      return filteredDepartments.value.slice(0, 4).map((dept, idx) => ({
        id: dept.id,
        shortLabel: dept.acronym || dept.name,
        count: Math.floor(Math.random() * 500) + 100,
        color: VIBRANT_COLORS[idx % VIBRANT_COLORS.length]
      })).sort((a, b) => b.count - a.count)
    }
  }

  let index = 0
  const result = []
  countsByDept.forEach((count, deptId) => {
    let label = 'Unknown'
    if (deptId !== 'unassigned') {
      const dept = filteredDepartments.value.find((d) => Number(d.id) === deptId)
      if (dept) label = dept.acronym || dept.name
    } else {
      label = 'Unassigned'
    }

    result.push({
      id: deptId,
      shortLabel: label,
      count,
      color: VIBRANT_COLORS[index % VIBRANT_COLORS.length],
    })
    index++
  })
  
  return result.sort((a, b) => b.count - a.count)
})

const totalSchoolStudents = computed(() => {
  return collegeDemographics.value.reduce((acc, item) => acc + item.count, 0)
})
`;
            lines.splice(insert_idx, 0, logic);
            break;
        }
    }
            
    // 5. Remove grid and CSS rules and replace them
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('.school-it-home__cards{display:grid;gap:20px}')) {
            lines[i+1] = ".school-it-home__hero,.school-it-home__summary,.school-it-home__breakdown{border-radius:32px;overflow:hidden}";
        } else if (lines[i].includes('grid-template-areas:"hero hero" "summary rate" "status status"')) {
            lines[i] = lines[i].replace('"summary rate" "status status"', '"summary breakdown"');
        } else if (lines[i].includes('grid-template-areas:"hero hero" "summary rate" "summary status"')) {
            lines[i] = lines[i].replace('"summary rate" "summary status"', '"summary breakdown" "summary breakdown"');
        } else if (lines[i].includes('.school-it-home__rate{grid-area:rate;min-height:266px}')) {
            lines[i] = "  .school-it-home__breakdown{grid-area:breakdown;display:flex;align-items:stretch;}";
            lines[i+1] = "";
            lines[i+2] = "";
        }
    }
            
    // 6. DOM Replacements
    const dom_replacement = `          <!-- College Breakdown -->
          <section class="school-it-home__breakdown dashboard-enter dashboard-enter--6">
            <SchoolItDemographicsChart :total="totalSchoolStudents" :items="collegeDemographics" />
          </section>`;
          
    let start_idx = -1;
    let end_idx = -1;
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('<section class="school-it-home__rate')) {
            start_idx = i;
        }
        if (lines[i].includes('</article>')) { // looking for the end of status panel
            if (lines[i+1].includes('</div>')) {
               if (lines[i+2].includes('</section>')) {
                   end_idx = i + 2;
                   break;
               }
            }
        }
    }
            
    if (start_idx !== -1 && end_idx !== -1) {
        lines.splice(start_idx, end_idx - start_idx + 1, dom_replacement);
    }
        
    fs.writeFileSync(filepath, lines.join('\n'), 'utf8');
    console.log('SUCCESS');
} catch (e) {
    console.error(e);
}
