/**
 * ============================================================
 * MOCK DATABASE — Based on db_sample.json
 * ============================================================
 * 
 * This file contains all mock data.
 * It mirrors the structure from db_sample.json but with
 * expanded sample data for testing all dashboard pages.
 * 
 * 🔴 BACKEND TEAM: When the real API is ready, this file
 *    will no longer be used. The frontend will fetch data
 *    from your REST API endpoints instead.
 *    See: src/services/api.js for the switch.
 * ============================================================
 */

// =====================
// USERS (from db_sample.json → users[])
// =====================
export const users = [
    {
        id: 'ADMIN-01',
        name: 'System Administrator',
        email: 'admin@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'admin',
        college: 'Admin Office',
        phone: '+63 912 345 6789',
        department: 'IT Department',
        bio: 'System Administrator for the R.I.Z.A.L. Attendance Recognition System at JRMSU College of Engineering.',
        status: 'Active',
        createdAt: '2024-01-01T08:00:00Z'
    },
    {
        id: 'SG-01',
        name: 'Carlos Santos',
        email: 'sg_president@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'sg',
        college: 'College of Engineering',
        phone: '+63 917 111 2233',
        department: 'Student Government',
        bio: 'SG President for the College of Engineering. Overseeing student activities and event management.',
        status: 'Active',
        createdAt: '2024-01-02T09:00:00Z'
    },
    {
        id: 'SG-02',
        name: 'Ana Lopez',
        email: 'sg_vp@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'sg',
        college: 'College of Arts and Sciences',
        phone: '+63 918 222 3344',
        department: 'Student Government',
        bio: 'SG Vice President for the College of Arts and Sciences.',
        status: 'Active',
        createdAt: '2024-01-05T10:00:00Z'
    },
    {
        id: 'SG-03',
        name: 'Rico Mendoza',
        email: 'sg_sec@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'sg',
        college: 'College of Business',
        phone: '+63 919 333 4455',
        department: 'Student Government',
        bio: 'SG Secretary for the College of Business.',
        status: 'Active',
        createdAt: '2024-01-06T10:00:00Z'
    },
    {
        id: 'SG-04',
        name: 'Lisa Ramos',
        email: 'sg_ed@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'sg',
        college: 'College of Education',
        phone: '+63 920 444 5566',
        department: 'Student Government',
        bio: 'SG Education Officer for the College of Education.',
        status: 'Active',
        createdAt: '2024-01-07T10:00:00Z'
    },
    {
        id: '24-A-00123',
        name: 'Jose Rizal',
        email: 'jose.rizal@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'student',
        studentId: '24-A-00123',
        college: 'College of Engineering',
        program: 'BS Computer Engineering',
        phone: '+63 921 555 6677',
        department: 'College of Engineering',
        bio: 'BS Computer Engineering student at JRMSU.',
        faceScanRegistered: true,
        status: 'Active',
        createdAt: '2024-02-14T10:30:00Z'
    },
    {
        id: '24-B-00456',
        name: 'Maria Clara',
        email: 'maria.clara@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'student',
        studentId: '24-B-00456',
        college: 'College of Arts and Sciences',
        program: 'BA Psychology',
        phone: '+63 922 666 7788',
        department: 'College of Arts and Sciences',
        bio: 'BA Psychology student at JRMSU.',
        faceScanRegistered: false,
        status: 'Pending',
        createdAt: '2024-02-15T11:45:00Z'
    },
    {
        id: '24-A-00789',
        name: 'Juan Luna',
        email: 'juan.luna@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'student',
        studentId: '24-A-00789',
        college: 'College of Engineering',
        program: 'BS Civil Engineering',
        phone: '+63 923 777 8899',
        department: 'College of Engineering',
        bio: 'BS Civil Engineering student at JRMSU.',
        faceScanRegistered: true,
        status: 'Active',
        createdAt: '2024-02-16T09:00:00Z'
    },
    {
        id: '24-C-01024',
        name: 'Andres Bonifacio',
        email: 'andres.b@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'student',
        studentId: '24-C-01024',
        college: 'College of Business',
        program: 'BS Accountancy',
        phone: '+63 924 888 9900',
        department: 'College of Business',
        bio: 'BS Accountancy student at JRMSU.',
        faceScanRegistered: true,
        status: 'Active',
        createdAt: '2024-02-17T08:30:00Z'
    },
    {
        id: '24-D-00567',
        name: 'Gabriela Silang',
        email: 'gab.silang@rizal.edu',
        password: 'password123',
        rememberMe: true,
        role: 'student',
        studentId: '24-D-00567',
        college: 'College of Education',
        program: 'B Secondary Education',
        phone: '+63 925 999 0011',
        department: 'College of Education',
        bio: 'B Secondary Education student at JRMSU.',
        faceScanRegistered: true,
        status: 'Active',
        createdAt: '2024-02-18T07:15:00Z'
    },
    {
        id: '24-B-00890',
        name: 'Emilio Aguinaldo',
        email: 'emilio.a@rizal.edu',
        password: 'password123',
        rememberMe: false,
        role: 'student',
        studentId: '24-B-00890',
        college: 'College of Arts and Sciences',
        program: 'BS Biology',
        phone: '+63 926 000 1122',
        department: 'College of Arts and Sciences',
        bio: 'BS Biology student at JRMSU.',
        faceScanRegistered: false,
        status: 'Pending',
        createdAt: '2024-02-19T14:00:00Z'
    }
];

// =====================
// REGISTRATIONS (from db_sample.json → registrations[])
// =====================
export const registrations = [
    {
        registrationId: 'REG-001',
        studentId: '24-B-00456',
        status: 'pending_approval',
        submissionDate: '2024-02-15T11:45:00Z'
    },
    {
        registrationId: 'REG-002',
        studentId: '24-B-00890',
        status: 'pending_approval',
        submissionDate: '2024-02-19T14:00:00Z'
    }
];

// =====================
// METADATA (from db_sample.json → metadata)
// =====================
export const metadata = {
    colleges: [
        'College of Engineering',
        'College of Arts and Sciences',
        'College of Business',
        'College of Education'
    ],
    programs: {
        'College of Engineering': ['BS Computer Engineering', 'BS Civil Engineering', 'BS Electronics Engineering'],
        'College of Arts and Sciences': ['BA Psychology', 'BS Biology', 'BA Communication'],
        'College of Business': ['BS Accountancy', 'BS Business Administration'],
        'College of Education': ['B Secondary Education', 'B Elementary Education']
    }
};

// =====================
// EVENTS (extra mock data for Events page)
// 🔴 BACKEND: GET /api/events
//    Each event has GPS coordinates for geofencing attendance verification.
//    `radiusMeters` defines how close the student must be to mark attendance.
//    `attendanceOpen` controls whether attendance can be marked right now.
// =====================
export const events = [
    {
        id: 1, name: 'Engineering Summit 2026',
        date: '2026-02-25', time: '08:00 AM',
        location: 'Main Auditorium',
        description: 'Annual engineering summit featuring keynote speakers and workshops.',
        college: 'College of Engineering', status: 'Upcoming', attendees: 245,
        attendanceOpen: true,
        latitude: 8.6557, longitude: 123.3827, radiusMeters: 150
    },
    {
        id: 2, name: 'College Week Kick-off',
        date: '2026-02-20', time: '09:00 AM',
        location: 'Campus Grounds',
        description: 'Campus-wide celebration opening with a parade and program.',
        college: null, status: 'Ongoing', attendees: 412,
        attendanceOpen: true,
        latitude: 8.652718, longitude: 123.421833, radiusMeters: 200
    },
    {
        id: 3, name: 'Tech Talk: AI in Education',
        date: '2026-03-10', time: '02:00 PM',
        location: 'Room 302, Engineering Bldg',
        description: 'Seminar on how AI is shaping the future of education.',
        college: 'College of Engineering', status: 'Planning', attendees: 0,
        attendanceOpen: false,
        latitude: 8.6555, longitude: 123.3825, radiusMeters: 100
    },
    {
        id: 4, name: 'Intramurals Opening',
        date: '2026-01-15', time: '07:00 AM',
        location: 'Sports Complex',
        description: 'Opening ceremony of the annual intramurals with all colleges.',
        college: null, status: 'Completed', attendees: 1280,
        attendanceOpen: false,
        latitude: 8.6562, longitude: 123.3835, radiusMeters: 250
    },
    {
        id: 5, name: 'Research Colloquium',
        date: '2026-01-20', time: '01:00 PM',
        location: 'Conference Hall',
        description: 'Presentation of research papers from various college departments.',
        college: 'College of Arts and Sciences', status: 'Completed', attendees: 89,
        attendanceOpen: false,
        latitude: 8.6558, longitude: 123.3828, radiusMeters: 100
    },
];

// =====================
// ANNOUNCEMENTS (mock data for Student Announcements page)
// =====================
export const announcements = [
    {
        id: 1,
        title: 'Midterm Examination Schedule Released',
        content: 'The midterm examination schedule for the 2nd semester, A.Y. 2025-2026 has been released. Please check your respective departmental boards and student portals for the complete schedule. Examinations will be held from March 10-14, 2026.',
        date: '2026-02-20',
        college: null,
        type: 'Academic',
        priority: 'high'
    },
    {
        id: 2,
        title: 'Engineering Summit 2026 — Call for Participants',
        content: 'The College of Engineering is hosting the annual Engineering Summit on February 25, 2026. All engineering students are required to attend. Non-engineering students are welcome to join as participants. Register at the College of Engineering Office.',
        date: '2026-02-18',
        college: 'College of Engineering',
        type: 'Event',
        priority: 'normal'
    },
    {
        id: 3,
        title: 'URGENT: Campus Power Interruption on Feb 22',
        content: 'Due to scheduled maintenance by the local electric cooperative, there will be no power supply on campus from 6:00 AM to 5:00 PM on Saturday, February 22, 2026. All air-conditioned rooms and computer laboratories will be unavailable during this period.',
        date: '2026-02-19',
        college: null,
        type: 'General',
        priority: 'urgent'
    },
    {
        id: 4,
        title: 'Psychology Dept: Research Paper Submission Deadline',
        content: 'All BA Psychology students enrolled in Research Methods (PSY 301) are reminded that the final research paper submission deadline is March 5, 2026. Late submissions will not be accepted. Submit your papers to Dr. Reyes\' office or via the online portal.',
        date: '2026-02-17',
        college: 'College of Arts and Sciences',
        type: 'Academic',
        priority: 'normal'
    },
    {
        id: 5,
        title: 'Intramurals 2026 — Team Registration Now Open',
        content: 'Registration for the annual JRMSU Intramurals 2026 is now open! Form your teams and register at the Sports Development Office before March 1, 2026. Sports include basketball, volleyball, badminton, table tennis, and chess.',
        date: '2026-02-16',
        college: null,
        type: 'Event',
        priority: 'normal'
    },
    {
        id: 6,
        title: 'Business Week 2026 Announced',
        content: 'The College of Business will host Business Week from March 17-21, 2026. Activities include entrepreneurship workshops, case study competitions, and a job fair with partner companies. All CoB students are expected to participate.',
        date: '2026-02-15',
        college: 'College of Business',
        type: 'Event',
        priority: 'normal'
    },
    {
        id: 7,
        title: 'Library Hours Extended for Midterms',
        content: 'The university library will extend its operating hours during the midterm examination period. New hours: Monday to Saturday, 7:00 AM to 9:00 PM. Sunday: 8:00 AM to 5:00 PM. Valid student ID is required for entry.',
        date: '2026-02-14',
        college: null,
        type: 'General',
        priority: 'normal'
    },
    {
        id: 8,
        title: 'Education Practicum Orientation',
        content: 'All 4th year College of Education students enrolled in practicum courses are required to attend the orientation on February 28, 2026 at 9:00 AM in the College of Education Auditorium. Attendance is mandatory.',
        date: '2026-02-13',
        college: 'College of Education',
        type: 'Academic',
        priority: 'high'
    },
];

// =====================
// COLLEGES (extra mock data for Colleges page)
// =====================
export const colleges = [
    {
        name: 'College of Engineering',
        dean: 'Dr. Juan Dela Cruz',
        students: 856,
        sgOfficer: 'Carlos Santos',
        color: 'from-blue-500 to-cyan-400',
        programs: [
            { name: 'BS Computer Engineering', students: 312 },
            { name: 'BS Civil Engineering', students: 280 },
            { name: 'BS Electronics Engineering', students: 264 },
        ]
    },
    {
        name: 'College of Arts and Sciences',
        dean: 'Dr. Maria Reyes',
        students: 724,
        sgOfficer: 'Ana Lopez',
        color: 'from-purple-500 to-violet-400',
        programs: [
            { name: 'BA Psychology', students: 290 },
            { name: 'BS Biology', students: 215 },
            { name: 'BA Communication', students: 219 },
        ]
    },
    {
        name: 'College of Business',
        dean: 'Dr. Pedro Garcia',
        students: 680,
        sgOfficer: 'Rico Mendoza',
        color: 'from-emerald-500 to-teal-400',
        programs: [
            { name: 'BS Accountancy', students: 350 },
            { name: 'BS Business Administration', students: 330 },
        ]
    },
    {
        name: 'College of Education',
        dean: 'Dr. Teresa Bautista',
        students: 587,
        sgOfficer: 'Lisa Ramos',
        color: 'from-amber-500 to-orange-400',
        programs: [
            { name: 'B Secondary Education', students: 310 },
            { name: 'B Elementary Education', students: 277 },
        ]
    },
];

// =====================
// ATTENDANCE RECORDS (extra mock data for Attendance page)
// =====================
export const attendanceRecords = [
    { id: 1, studentId: '24-A-00123', student: 'Jose Rizal', event: 'Engineering Summit 2026', date: '2026-02-25', checkIn: '08:05 AM', checkOut: '04:30 PM', status: 'Present' },
    { id: 2, studentId: '24-B-00456', student: 'Maria Clara', event: 'Engineering Summit 2026', date: '2026-02-25', checkIn: '08:45 AM', checkOut: '04:30 PM', status: 'Late' },
    { id: 3, studentId: '24-A-00789', student: 'Juan Luna', event: 'Engineering Summit 2026', date: '2026-02-25', checkIn: '-', checkOut: '-', status: 'Absent' },
    { id: 4, studentId: '24-C-01024', student: 'Andres Bonifacio', event: 'Intramurals Opening', date: '2026-01-15', checkIn: '06:55 AM', checkOut: '12:00 PM', status: 'Present' },
    { id: 5, studentId: '24-A-00123', student: 'Jose Rizal', event: 'Intramurals Opening', date: '2026-01-15', checkIn: '07:10 AM', checkOut: '12:00 PM', status: 'Present' },
    { id: 6, studentId: '24-B-00456', student: 'Maria Clara', event: 'Intramurals Opening', date: '2026-01-15', checkIn: '-', checkOut: '-', status: 'Absent' },
    { id: 7, studentId: '24-D-00567', student: 'Gabriela Silang', event: 'Intramurals Opening', date: '2026-01-15', checkIn: '07:00 AM', checkOut: '12:00 PM', status: 'Present' },
];

// =====================
// LOGIN RECORDS (extra mock data for LoggedInRecords page)
// =====================
export const loginRecords = [
    { id: 1, userId: 'ADMIN-01', user: 'System Admin', email: 'admin@rizal.edu', role: 'Admin', device: 'Desktop', browser: 'Firefox', ip: '192.168.1.10', loginTime: '2026-02-18 07:55 AM', status: 'Active' },
    { id: 2, userId: 'SG-01', user: 'Carlos Santos', email: 'sg_president@rizal.edu', role: 'SG', device: 'Desktop', browser: 'Chrome', ip: '192.168.1.22', loginTime: '2026-02-18 07:30 AM', status: 'Active' },
    { id: 3, userId: '24-A-00123', user: 'Jose Rizal', email: 'jose.rizal@rizal.edu', role: 'Student', device: 'Mobile', browser: 'Chrome', ip: '192.168.1.45', loginTime: '2026-02-18 08:12 AM', status: 'Active' },
    { id: 4, userId: '24-B-00456', user: 'Maria Clara', email: 'maria.clara@rizal.edu', role: 'Student', device: 'Mobile', browser: 'Safari', ip: '192.168.1.67', loginTime: '2026-02-17 06:45 PM', status: 'Expired' },
    { id: 5, userId: '24-A-00789', user: 'Juan Luna', email: 'juan.luna@rizal.edu', role: 'Student', device: 'Desktop', browser: 'Edge', ip: '192.168.1.88', loginTime: '2026-02-17 04:20 PM', status: 'Expired' },
    { id: 6, userId: 'SG-02', user: 'Ana Lopez', email: 'sg_vp@rizal.edu', role: 'SG', device: 'Mobile', browser: 'Chrome', ip: '192.168.1.33', loginTime: '2026-02-17 02:10 PM', status: 'Expired' },
    { id: 7, userId: '24-C-01024', user: 'Andres Bonifacio', email: 'andres.b@rizal.edu', role: 'Student', device: 'Mobile', browser: 'Chrome', ip: '192.168.1.90', loginTime: '2026-02-17 11:05 AM', status: 'Expired' },
];

// =====================
// DASHBOARD STATS (computed from above data)
// =====================
export const dashboardStats = {
    totalStudents: users.filter(u => u.role === 'student').length,
    activeEvents: events.filter(e => e.status === 'Upcoming').length,
    totalColleges: colleges.length,
    attendanceRate: 89 // percentage
};

export const recentActivity = [
    { userId: '24-A-00123', user: 'Jose Rizal', action: 'Checked in at Engineering Summit', time: '2 min ago', type: 'checkin' },
    { userId: '24-B-00456', user: 'Maria Clara', action: 'Account approved by SG', time: '15 min ago', type: 'approval' },
    { userId: '24-A-00789', user: 'Juan Luna', action: 'Registered for Tech Talk', time: '1 hr ago', type: 'registration' },
    { userId: '24-C-01024', user: 'Andres Bonifacio', action: 'New account created', time: '3 hrs ago', type: 'account' },
    { userId: '24-D-00567', user: 'Gabriela Silang', action: 'Checked in at Intramurals', time: '5 hrs ago', type: 'checkin' },
];

export const weeklyAttendance = [
    { day: 'Mon', value: 72 },
    { day: 'Tue', value: 85 },
    { day: 'Wed', value: 60 },
    { day: 'Thu', value: 90 },
    { day: 'Fri', value: 78 },
    { day: 'Sat', value: 40 },
    { day: 'Sun', value: 20 },
];
