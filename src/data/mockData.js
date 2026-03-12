/**
 * Mock Data - Mirrors backend API response shapes EXACTLY.
 * Replace with real API calls when backend is connected.
 *
 * API Endpoints:
 *   GET /users/me                  → mockCurrentUser  (UserWithRelations schema)
 *   GET /events/                   → mockEvents       (Event schema)
 *   GET /school-settings/me        → mockSchoolSettings (SchoolSettingsResponse schema)
 */

// ─── User ────────────────────────────────────────────────────────────────────
// Matches: UserWithRelations schema from GET /users/me
// Key fields: id, email, first_name, last_name, middle_name, school_id,
//             is_active, created_at, roles[], ssg_profile, student_profile
// School 1 Student (RTU)
export const mockRtuUser = {
    id: 101,
    email: 'zann@example.edu',
    first_name: 'Zann',
    last_name: 'Doe',
    middle_name: null,
    is_active: true,
    created_at: '2026-03-11T08:00:00Z',
    school_id: 1, // RTU
    roles: [
        { role: { id: 2, name: 'student' } },
    ],
    ssg_profile: null,
    student_profile: {
        id: 55,
        student_id: 'CS-2026-001',
        department_id: 3,
        program_id: 7,
        year_level: 2,
        attendances: [],
    },
}

// School 2 Student (JRMSU)
export const mockJrmsuUser = {
    id: 102,
    email: 'maria@example.edu',
    first_name: 'Maria',
    last_name: 'Clara',
    middle_name: null,
    is_active: true,
    created_at: '2026-03-11T08:00:00Z',
    school_id: 2, // JRMSU
    roles: [
        { role: { id: 2, name: 'student' } },
    ],
    ssg_profile: null,
    student_profile: {
        id: 56,
        student_id: 'IT-2026-002',
        department_id: 4,
        program_id: 8,
        year_level: 1,
        attendances: [],
    },
}

// Super Admin User
export const mockSuperAdminUser = {
    id: 1,
    email: 'superadmin@aura.edu',
    first_name: 'Super',
    last_name: 'Admin',
    middle_name: null,
    is_active: true,
    created_at: '2026-03-11T08:00:00Z',
    school_id: null, // Global
    roles: [
        { role: { id: 1, name: 'super_admin' } },
    ],
    ssg_profile: null,
    student_profile: null,
}

// 👉 To test different roles, change 'mockCurrentUser' below:
// mockRtuUser, mockJrmsuUser, or mockSuperAdminUser
export const mockCurrentUser = mockSuperAdminUser

// ─── Events ──────────────────────────────────────────────────────────────────
// Matches: Event schema
// Key fields: id, name, location, start_datetime, end_datetime, status,
//             school_id, department_ids[], program_ids[], ssg_member_ids[]
export const mockEvents = [
    {
        id: 1,
        name: 'Foundation Day Celebration',
        location: 'Main Gymnasium, Building A',
        start_datetime: '2026-03-15T08:00:00',
        end_datetime: '2026-03-15T17:00:00',
        status: 'upcoming',
        school_id: 1,
        department_ids: [1],
        program_ids: [],
        ssg_member_ids: [1, 2],
        departments: [{ id: 1, name: 'All Departments' }],
        programs: [],
        ssg_members: [],
        description: 'Annual Foundation Day with special performances, food stalls, and awarding ceremonies.',
    },
    {
        id: 2,
        name: 'Engineering Week Summit',
        location: 'College of Engineering Amphitheater',
        start_datetime: '2026-03-20T09:00:00',
        end_datetime: '2026-03-22T18:00:00',
        status: 'upcoming',
        school_id: 1,
        department_ids: [2],
        program_ids: [],
        ssg_member_ids: [],
        departments: [{ id: 2, name: 'College of Engineering' }],
        programs: [],
        ssg_members: [],
        description: 'Showcase of student engineering projects, technical competitions, and career talks.',
    },
    {
        id: 3,
        name: 'IT Skills Competition',
        location: 'Computer Laboratory 3',
        start_datetime: '2026-03-25T13:00:00',
        end_datetime: '2026-03-25T17:00:00',
        status: 'upcoming',
        school_id: 1,
        department_ids: [3],
        program_ids: [7],
        ssg_member_ids: [],
        departments: [{ id: 3, name: 'College of IT' }],
        programs: [{ id: 7, name: 'BSCS' }],
        ssg_members: [],
        description: 'Annual IT Skills Competition for all IT and CS students.',
    },
]

// ─── School Settings ─────────────────────────────────────────────────────────
// Matches: SchoolSettingsResponse schema from GET /school-settings/me
// School 1 (Default Lime Green Theme)
export const mockRtuSettings = {
    school_id: 1,
    school_name: 'Rizal Technological University',
    primary_color: '#6366F1', // Indigo
    secondary_color: '#0A0A0A',
    accent_color: '#4F46E5',
    logo_url: '/src/data/jrmsu_icon.png',
}

// School 2 (Example Blue/Gold Theme)
export const mockJrmsuSettings = {
    school_id: 2,
    school_name: 'Jose Rizal Memorial State University',
    primary_color: '#00205B', // Deep Blue
    secondary_color: '#FFFFFF',
    accent_color: '#FFB81C', // Gold
    logo_url: '/src/data/jrmsu_main_icon.png',
}

// 👉 To test a different school, change 'mockRtuSettings' below to 'mockJrmsuSettings'
export const mockSchoolSettings = mockRtuSettings

// ─── Announcements ───────────────────────────────────────────────────────────
// Flexible shape — endpoint TBD in backend (for future connection)
export const mockAnnouncements = [
    {
        id: 1,
        title: 'Class Suspension – March 14',
        body: 'All classes are suspended on March 14 due to Foundation Day preparations.',
        created_at: '2026-03-10T08:00:00Z',
        is_read: false,
        type: 'announcement',
    },
    {
        id: 2,
        title: 'Scholarship Applications Open',
        body: 'Applications for the University Scholarship Program are now open until March 31.',
        created_at: '2026-03-09T10:00:00Z',
        is_read: true,
        type: 'announcement',
    },
]
// ─── Campuses (Super Admin View) ───────────────────────────────────────────
export const mockCampuses = [
    { 
        id: 1, 
        name: 'Rizal Technological University', 
        location: 'Mandaluyong, PH', 
        students: 28450, 
        staff: 1100,
        logo: '/src/data/jrmsu_icon.png',
        status: 'Active',
        plan: 'Enterprise Elite',
        admin: { name: 'Dr. Ricardo Garcia', email: 'r.garcia@rtu.edu.ph' }
    },
    { 
        id: 2, 
        name: 'Jose Rizal Memorial State University', 
        location: 'Dapitan City, PH', 
        students: 12100, 
        staff: 650,
        logo: '/src/data/jrmsu_icon.png',
        status: 'Active',
        plan: 'Advanced',
        admin: { name: 'Engr. Maria Santos', email: 'm.santos@jrmsu.edu.ph' }
    },
    { 
        id: 3, 
        name: 'Philippine Normal University', 
        location: 'Manila, PH', 
        students: 8400, 
        staff: 400,
        logo: '/src/data/jrmsu_icon.png',
        status: 'Active',
        plan: 'Standard',
        admin: { name: 'Prof. John Doe', email: 'j.doe@pnu.edu.ph' }
    },
    { 
        id: 4, 
        name: 'Bulacan State University', 
        location: 'Malolos, PH', 
        students: 35000, 
        staff: 1500,
        logo: '/src/data/jrmsu_icon.png',
        status: 'Active',
        plan: 'Enterprise Elite'
    },
    { 
        id: 5, 
        name: 'Mindanao State University', 
        location: 'Marawi, PH', 
        students: 18000, 
        staff: 900,
        logo: '/src/data/jrmsu_icon.png',
        status: 'Inactive',
        plan: 'Advanced'
    }
]
