import { existsSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Busboy from 'busboy';
import { App } from '@tinyhttp/app';
import { cors } from '@tinyhttp/cors';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';
import { NormalizedAdapter } from 'json-server/lib/adapters/normalized-adapter.js';
import { Observer } from 'json-server/lib/adapters/observer.js';
import { Service } from 'json-server/lib/service.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const dbPath = path.join(__dirname, 'db.json');

if (!existsSync(dbPath)) {
  console.log('Error: db.json not found');
  process.exit(1);
}

if (readFileSync(dbPath, 'utf-8').trim() === '') {
  writeFileSync(dbPath, '{}');
}

const adapter = new JSONFile(dbPath);
const observer = new Observer(new NormalizedAdapter(adapter));
const db = new Low(observer, {});
await db.read();

const service = new Service(db);
const app = new App();

async function parseBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      const contentType = req.headers['content-type'] || '';
      if (contentType.includes('application/json')) {
        try {
          req.body = JSON.parse(body || '{}');
        } catch {
          req.body = {};
        }
      } else if (contentType.includes('application/x-www-form-urlencoded')) {
        const params = new URLSearchParams(body);
        req.body = {
          username: params.get('username'),
          password: params.get('password'),
        };
      } else {
        try {
          req.body = JSON.parse(body || '{}');
        } catch {
          req.body = {};
        }
      }
      resolve();
    });
  });
}

async function parseMultipartBody(req) {
  return new Promise((resolve, reject) => {
    const busboy = Busboy({ headers: req.headers });
    const fields = {};
    busboy.on('field', (name, val) => {
      fields[name] = val;
    });
    busboy.on('file', (name, file, info) => {
      // Just ignore files for now, or store minimal info
      fields[name] = { filename: info.filename, mimeType: info.mimeType };
      file.resume();
    });
    busboy.on('finish', () => {
      req.body = fields;
      resolve();
    });
    busboy.on('error', (err) => reject(err));
    req.pipe(busboy);
  });
}

app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept', 'Origin', 'X-Requested-With'],
  credentials: true,
}));

// Static file server middleware for /public
app.use((req, res, next) => {
  const urlPath = req.url.split('?')[0];
  const publicPath = path.join(__dirname, 'public', urlPath);

  if (existsSync(publicPath) && !statSync(publicPath).isDirectory()) {
    const ext = path.extname(publicPath).toLowerCase();
    const mimeTypes = {
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.gif': 'image/gif',
      '.svg': 'image/svg+xml',
      '.ico': 'image/x-icon',
      '.css': 'text/css',
      '.js': 'application/javascript',
      '.json': 'application/json',
    };
    res.setHeader('Content-Type', mimeTypes[ext] || 'application/octet-stream');
    return res.send(readFileSync(publicPath));
  }
  next();
});

app.options('*', (req, res) => {
  res.writeHead(204, {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept, Origin, X-Requested-With',
    'Access-Control-Max-Age': '86400',
  });
  res.end();
});

app.use((req, res, next) => {
  const oldUrl = req.url;
  // Handle double /api/api/ prefix
  if (req.url.startsWith('/api/api/')) {
    req.url = req.url.replace('/api/api/', '/');
  } else if (req.url.startsWith('/api/')) {
    req.url = req.url.replace('/api/', '/');
  } else if (req.url.startsWith('/__backend__/')) {
    req.url = req.url.replace('/__backend__/', '/');
  }

  // Handle slashes at the end
  if (req.url !== '/' && req.url.endsWith('/')) {
    req.url = req.url.slice(0, -1);
  }

  // Generic hyphenated to underscore rewrite for database resources
  const pathParts = req.url.split('?')[0].split('/');
  const nameCandidate = pathParts[1];
  if (nameCandidate && nameCandidate.includes('-')) {
    const underscored = nameCandidate.replace(/-/g, '_');
    if (db.data[underscored]) {
      req.url = req.url.replace(`/${nameCandidate}`, `/${underscored}`);
    }
  }

  if (oldUrl !== req.url) {
    console.log(`[REWRITE] ${oldUrl} -> ${req.url}`);
  }
  next();
});

const MOCK_TOKEN_SECRET = 'mock-jwt-secret-key';

function base64Encode(str) {
  return Buffer.from(str).toString('base64');
}

function createMockToken(payload) {
  const header = { alg: 'HS256', typ: 'JWT' };
  const headerB64 = base64Encode(JSON.stringify(header)).replace(/=/g, '');
  const payloadB64 = base64Encode(JSON.stringify(payload)).replace(/=/g, '');
  const signature = base64Encode(`${headerB64}.${payloadB64}.${MOCK_TOKEN_SECRET}`).replace(/=/g, '');
  return `${headerB64}.${payloadB64}.${signature}`;
}

function getSchoolById(schoolId) {
  if (!schoolId) return null;
  const schools = db.data.schools || [];
  return schools.find(s => String(s.school_id) === String(schoolId)) || null;
}

function buildTokenPayload(user) {
  const school = getSchoolById(user.school_id) || {
    school_id: null,
    school_name: "Aura System Admin",
    school_code: "SYSTEM",
    primary_color: "#000000",
    secondary_color: "#FFFFFF",
    accent_color: "#666666"
  };
  return {
    access_token: createMockToken({
      user_id: user.id,
      email: user.email,
      roles: user.roles,
      school_id: user.school_id,
    }),
    token_type: 'bearer',
    user_id: user.id,
    email: user.email,
    first_name: user.first_name,
    last_name: user.last_name,
    roles: user.roles,
    school_id: school.school_id,
    school_name: school.school_name,
    school_code: school.school_code,
    primary_color: school.primary_color,
    secondary_color: school.secondary_color,
    accent_color: school.accent_color,
    must_change_password: false,
    mfa_required: false,
    face_verification_required: user.roles.some(r => ['admin', 'school_it', 'campus_admin', 'student'].includes(String(r).toLowerCase())),
    face_reference_enrolled: true,
    face_verification_pending: user.roles.some(r => ['admin', 'school_it', 'campus_admin', 'student'].includes(String(r).toLowerCase())),
    is_admin: user.roles.some(r => String(r).toLowerCase() === 'admin'),
  };
}

function handleTokenRequest(req, res) {
  console.log(`[POST] ${req.path} - Body:`, JSON.stringify(req.body));
  const { username, password } = req.body || {};

  if (!username || !password) {
    console.log(`[WARN] Missing username or password`);
    return res.status(400).json({ detail: 'Missing username or password' });
  }

  const users = db.data.users || [];
  const user = users.find(u => u.email === username && u.password === password);

  if (!user) {
    console.log(`[WARN] Invalid credentials for: ${username}`);
    return res.status(401).json({ detail: 'Invalid credentials' });
  }

  const school = getSchoolById(user.school_id);
  console.log(`[INFO] Login: ${user.email} -> school: ${school?.school_name || 'unknown'}`);
  return res.status(200).json(buildTokenPayload(user));
}

function getCurrentUser(req) {
  const auth = req.headers['authorization'] || '';
  const token = auth.replace('Bearer ', '').trim();
  if (!token) return null;

  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const payloadJson = Buffer.from(parts[1], 'base64').toString();
    const payload = JSON.parse(payloadJson);
    const users = db.data.users || [];
    return users.find(u => String(u.id) === String(payload.user_id)) || null;
  } catch (e) {
    console.error(`[AUTH ERROR] Failed to parse token: ${e.message}`);
    return null;
  }
}

app.get('/users', (req, res) => res.json(db.data.users || []));
app.get('/governance/ssg/setup', (req, res) => res.json({
  unit: (db.data.governance_units || []).find(u => String(u.unit_type).toUpperCase() === 'SSG') || null,
  total_imported_students: 0
}));
app.get('/governance/access/me', (req, res) => res.json({ units: db.data.governance_units || [] }));
app.get('/governance/units', (req, res) => res.json(db.data.governance_units || []));
app.get('/attendance/summary', (req, res) => res.json({ summary: [], total: 0 }));
app.get('/governance/students/search', (req, res) => {
  const query = (req.query.q || '').toLowerCase();
  const users = db.data.users || [];
  const students = users.filter(u => 
    u.roles.includes('student') && 
    (u.email.toLowerCase().includes(query) || 
     u.first_name.toLowerCase().includes(query) || 
     u.last_name.toLowerCase().includes(query))
  ).map(u => ({
    id: u.id,
    email: u.email,
    first_name: u.first_name,
    last_name: u.last_name,
    student_id: u.student_profile?.student_id
  }));
  res.json(students);
});

app.post('/admin/import-students/preview', async (req, res) => {
  console.log(`[POST] /api/admin/import-students/preview`);
  await parseMultipartBody(req);
  res.json({
    preview_token: 'mock-preview-token-' + Date.now(),
    total_rows: 50,
    valid_rows: 48,
    error_rows: 2,
    rows: [
      { email: 'imported1@example.com', first_name: 'Imported', last_name: 'One', status: 'valid' },
      { email: 'imported2@example.com', first_name: 'Imported', last_name: 'Two', status: 'valid' }
    ]
  });
});

app.post('/admin/import-students', async (req, res) => {
  console.log(`[POST] /api/admin/import-students`);
  await parseBody(req);
  const jobId = 'job-' + Math.random().toString(36).slice(-6);
  res.json({
    job_id: jobId,
    status: 'pending',
    message: 'Import job created successfully.'
  });
});

app.get('/admin/import-students/jobs/:jobId', (req, res) => {
  const { jobId } = req.params;
  res.json({
    id: jobId,
    status: 'completed',
    progress: 100,
    total_rows: 50,
    processed_rows: 50,
    success_count: 50,
    error_count: 0
  });
});

app.post('/token', async (req, res) => {
  await parseBody(req);
  handleTokenRequest(req, res);
});

app.post('/token', async (req, res) => {
  await parseBody(req);
  handleTokenRequest(req, res);
});

app.post('/school/admin/create-school-it', async (req, res) => {
  console.log(`[POST] /api/school/admin/create-school-it`);
  await parseMultipartBody(req);
  const payload = req.body;

  const nextSchoolId = Math.max(0, ...(db.data.schools || []).map(s => Number(s.school_id) || 0)) + 1;
  const nextUserId = Math.max(0, ...(db.data.users || []).map(u => Number(u.id) || 0)) + 1;
  const now = new Date().toISOString();

  const newSchool = {
    id: String(nextSchoolId),
    school_id: nextSchoolId,
    school_name: payload.school_name,
    school_code: payload.school_code || null,
    primary_color: payload.primary_color || '#0057B8',
    secondary_color: payload.secondary_color || '#FFD400',
    accent_color: '#000000',
    logo_url: null,
    subscription_status: 'trial',
    active_status: true,
    created_at: now,
    updated_at: now
  };

  const newUser = {
    id: String(nextUserId),
    email: payload.school_it_email,
    password: payload.school_it_password || 'password123',
    first_name: payload.school_it_first_name,
    last_name: payload.school_it_last_name,
    middle_name: payload.school_it_middle_name || null,
    roles: ['school_IT'],
    is_active: true,
    school_id: nextSchoolId,
    created_at: now
  };

  db.data.schools = [...(db.data.schools || []), newSchool];
  db.data.users = [...(db.data.users || []), newUser];
  await db.write();

  console.log(`[INFO] Created school: ${newSchool.school_name} (ID: ${nextSchoolId})`);
  console.log(`[INFO] Created admin: ${newUser.email}`);

  res.status(201).json({
    school: newSchool,
    school_it_user_id: nextUserId,
    school_it_email: newUser.email,
    generated_temporary_password: newUser.password
  });
});

app.get('/school/admin/list', (req, res) => {
  console.log(`[GET] /school/admin/list`);
  res.json(db.data.schools || []);
});

app.get('/school/admin/school-it-accounts', (req, res) => {
  console.log(`[GET] /school/admin/school-it-accounts`);
  const users = db.data.users || [];
  const schoolItAccounts = users.filter(u => u.roles.some(r => String(r).toLowerCase() === 'school_it'));
  res.json(schoolItAccounts);
});

app.get('/governance/settings/me', (req, res) => {
  console.log(`[GET] /governance/settings/me`);
  res.json({
    school_id: 1,
    attendance_retention_days: 365,
    audit_log_retention_days: 365,
    import_file_retention_days: 30,
    auto_delete_enabled: false,
    updated_at: new Date().toISOString()
  });
});

app.put('/governance/settings/me', async (req, res) => {
  console.log(`[PUT] /governance/settings/me`);
  await parseBody(req);
  res.status(200).json({
    ...req.body,
    updated_at: new Date().toISOString()
  });
});

app.get('/users/me', (req, res) => {
  console.log(`[GET] /users/me`);
  const user = getCurrentUser(req) || db.data.users?.[0]; // Fallback to first user only if no token
  if (user) {
    res.json({
      ...user,
      password: undefined,
      school_name: getSchoolById(user.school_id)?.school_name || 'System Admin',
    });
  } else {
    res.status(404).json({ error: 'No mock user' });
  }
});

app.get('/users/:id', (req, res, next) => {
  const { id } = req.params;
  const users = db.data.users || [];
  const user = users.find(u => String(u.id) === String(id));
  if (user) {
    res.json({ ...user, password: undefined });
  } else {
    next();
  }
});

app.get('/school/me', (req, res) => {
  console.log(`[GET] /school/me`);
  const user = getCurrentUser(req);
  if (!user?.school_id) return res.json({ school_name: 'System Admin', school_id: null });
  const school = getSchoolById(user.school_id) || db.data.schools?.[0] || {};
  res.json(school);
});

app.get('/school-settings/me', (req, res) => {
  console.log(`[GET] /school-settings/me`);
  const user = getCurrentUser(req);
  if (!user?.school_id) return res.json({ primary_color: '#000000', school_name: 'Super Admin' });
  const school = getSchoolById(user.school_id) || db.data.schools?.[0] || {};
  res.json(school);
});

app.put('/school/update', async (req, res) => {
  const user = getCurrentUser(req);
  if (!user) return res.status(401).json({ detail: 'Unauthorized' });

  const contentType = req.headers['content-type'] || '';
  if (contentType.includes('multipart/form-data')) {
    await parseMultipartBody(req);
  } else {
    await parseBody(req);
  }

  const payload = req.body;
  const school = (db.data.schools || []).find(s => String(s.school_id) === String(user.school_id));

  if (!school) return res.status(404).json({ detail: 'School not found (Searching school_id: ' + user.school_id + ')' });

  if (payload.school_name !== undefined) school.school_name = payload.school_name;
  if (payload.primary_color !== undefined) school.primary_color = payload.primary_color;
  if (payload.secondary_color !== undefined) school.secondary_color = payload.secondary_color;
  if (payload.school_code !== undefined) school.school_code = payload.school_code;

  school.updated_at = new Date().toISOString();
  await db.write();

  res.json(school);
});

app.get('/attendance/me/records', (req, res) => {
  console.log(`[GET] /attendance/me/records`);
  res.json(db.data.attendance || []);
});

app.get('/attendance/students/me', (req, res) => {
  console.log(`[GET] /attendance/students/me`);
  res.json(db.data.attendance || []);
});

app.get('/auth/security/face-status', (req, res) => {
  console.log(`[GET] /auth/security/face-status`);
  const user = getCurrentUser(req);
  const requiresFace = user ? user.roles.some(r => ['admin', 'school_it', 'campus_admin', 'student'].includes(String(r).toLowerCase())) : false;
  res.json({
    face_verification_required: requiresFace,
    face_reference_enrolled: true,
    provider: 'face_recognition',
    liveness_enabled: true,
    anti_spoof_ready: true,
  });
});

app.post('/auth/security/face-verify', async (req, res) => {
  console.log(`[POST] /auth/security/face-verify`);
  await parseBody(req);
  const user = getCurrentUser(req);
  if (!user) return res.status(401).json({ detail: 'Unauthorized' });

  setTimeout(() => {
    res.json({
      matched: true,
      confidence: 0.98,
      access_token: createMockToken({
        user_id: user.id,
        email: user.email,
        roles: user.roles,
        school_id: user.school_id,
      }),
      token_type: 'bearer',
      face_verification_pending: false
    });
  }, 600);
});

app.post('/auth/security/face-setup', async (req, res) => {
  console.log(`[POST] /auth/security/face-setup`);
  setTimeout(() => res.json({ success: true }), 800);
});

app.get('/auth/security/face-reference', (req, res) => {
  console.log(`[GET] /auth/security/face-reference`);
  res.json({
    face_reference_enrolled: false,
    provider: 'face_recognition',
    updated_at: new Date().toISOString(),
  });
});

app.get('/departments/', (req, res, next) => {
  const queryString = req.url.split('?')[1] ?? '';
  const params = new URLSearchParams(queryString);
  const schoolId = params.get('school_id');
  let departments = db.data.departments || [];
  if (schoolId) {
    departments = departments.filter(d => String(d.school_id) === String(schoolId));
  }
  res.json(departments);
  next?.();
});

app.get('/programs/', (req, res, next) => {
  const queryString = req.url.split('?')[1] ?? '';
  const params = new URLSearchParams(queryString);
  const schoolId = params.get('school_id');
  let programs = db.data.programs || [];
  if (schoolId) {
    programs = programs.filter(p => String(p.school_id) === String(schoolId));
  }
  res.json(programs);
  next?.();
});

app.get('/events/', (req, res, next) => {
  const queryString = req.url.split('?')[1] ?? '';
  const params = new URLSearchParams(queryString);
  const schoolId = params.get('school_id');
  let events = db.data.events || [];
  if (schoolId) {
    events = events.filter(e => String(e.school_id) === String(schoolId));
  }
  res.json(events);
  next?.();
});

app.post('/public-attendance/events/nearby', async (req, res) => {
  console.log(`[POST] /public-attendance/events/nearby`);
  await parseBody(req);
  const events = (db.data.events || []).map(e => ({
    ...e,
    school_name: getSchoolById(e.school_id)?.school_name || 'Campus',
    distance_m: Math.random() * 50,
    effective_distance_m: Math.random() * 50,
    accuracy_m: req.body?.accuracy_m || 5,
    attendance_phase: 'sign_in',
    phase_message: `${e.name} is ready for Sign In.`,
    scope_label: 'Campus-wide',
    departments: [],
    programs: []
  }));

  res.json({
    events,
    scan_cooldown_seconds: 8
  });
});

app.post('/public-attendance/events/:eventId/multi-face-scan', async (req, res) => {
  const { eventId } = req.params;
  console.log(`[POST] /public-attendance/events/${eventId}/multi-face-scan`);
  await parseBody(req);

  const event = (db.data.events || []).find(e => String(e.id) === String(eventId));
  if (!event) return res.status(404).json({ detail: 'Event not found' });

  // Mock matching a student (student@example.com is ID 3)
  const student = (db.data.users || []).find(u => u.roles.includes('student'));
  const outcomes = [];

  if (student) {
    outcomes.push({
      action: 'time_in',
      reason_code: 'success',
      message: `Welcome, ${student.first_name}! Your attendance for ${event.name} has been recorded.`,
      student_id: student.student_profile?.student_id || 'STU-001',
      student_name: `${student.first_name} ${student.last_name}`,
      attendance_id: Math.floor(Math.random() * 1000),
      distance: 2.5,
      confidence: 0.95 + Math.random() * 0.04,
      threshold: 0.85,
      liveness: { label: 'live', score: 0.99 },
      time_in: new Date().toISOString()
    });
  } else {
    outcomes.push({
      action: 'no_match',
      message: 'No matching student found in the frame.',
      confidence: 0.45
    });
  }

  res.json({
    event_id: Number(eventId),
    event_phase: 'sign_in',
    message: outcomes[0].message,
    scan_cooldown_seconds: 8,
    geo: {
      latitude: req.body?.latitude,
      longitude: req.body?.longitude,
      accuracy_m: req.body?.accuracy_m
    },
    outcomes
  });
});

app.post('/notifications/dispatch/:kind', async (req, res) => {
  const { kind } = req.params;
  console.log(`[POST] /notifications/dispatch/${kind}`);
  await parseBody(req);
  res.status(202).json({
    summary: `${kind.replace('-', ' ')} notifications dispatched successfully.`,
    total_sent: kind === 'low-attendance' ? 12 : 5,
    timestamp: new Date().toISOString()
  });
});

app.post('/governance/run-retention', async (req, res) => {
  console.log(`[POST] /governance/run-retention`);
  await parseBody(req);
  res.status(200).json({
    summary: 'Data retention cleanup completed.',
    records_deleted: 154,
    timestamp: new Date().toISOString()
  });
});

app.patch('/school/admin/:id/status', async (req, res) => {
  const { id } = req.params;
  console.log(`[PATCH] /school/admin/${id}/status`);
  await parseBody(req);
  const school = db.data.schools.find(s => String(s.school_id) === String(id));
  if (school) {
    Object.assign(school, req.body);
    await db.write();
    res.json(school);
  } else {
    res.status(404).json({ error: 'School not found' });
  }
});

app.patch('/school/admin/school-it-accounts/:id/status', async (req, res) => {
  const { id } = req.params;
  console.log(`[PATCH] /school/admin/school-it-accounts/${id}/status`);
  await parseBody(req);
  const user = db.data.users.find(u => String(u.id) === String(id));
  if (user) {
    user.is_active = Boolean(req.body.is_active);
    await db.write();
    res.json(user);
  } else {
    res.status(404).json({ error: 'User not found' });
  }
});

app.post('/school/admin/school-it-accounts/:id/reset-password', async (req, res) => {
  const { id } = req.params;
  console.log(`[POST] /school/admin/school-it-accounts/${id}/reset-password`);
  const user = db.data.users.find(u => String(u.id) === String(id));
  if (user) {
    const tempPassword = `RESET-${Math.random().toString(36).slice(-8).toUpperCase()}`;
    res.json({
      user_id: user.id,
      email: user.email,
      temporary_password: tempPassword,
      must_change_password: true,
      expires_at: new Date(Date.now() + 86400000).toISOString()
    });
  } else {
    res.status(404).json({ error: 'User not found' });
  }
});

app.post('/users/:id/reset-password', async (req, res) => {
  const { id } = req.params;
  console.log(`[POST] /users/${id}/reset-password`);
  const user = db.data.users.find(u => String(u.id) === String(id));
  if (user) {
    const tempPassword = `STU-RESET-${Math.random().toString(36).slice(-8).toUpperCase()}`;
    res.json({
      user_id: user.id,
      email: user.email,
      temporary_password: tempPassword,
      must_change_password: true,
      expires_at: new Date(Date.now() + 86400000).toISOString()
    });
  } else {
    res.status(404).json({ error: 'User not found' });
  }
});

app.post('/school/admin', async (req, res) => {
  console.log(`[POST] /school/admin`);
  await parseBody(req);
  const { school_name, school_code, primary_color, secondary_color, school_it_email, school_it_first_name, school_it_last_name, school_it_password } = req.body;
  
  const newSchoolId = db.data.schools.length + 1;
  const newSchool = {
    id: String(newSchoolId),
    school_id: newSchoolId,
    school_name: school_name || 'New Campus',
    school_code: school_code || 'NEW',
    primary_color: primary_color || '#0057B8',
    secondary_color: secondary_color || '#FFFFFF',
    accent_color: '#000000',
    subscription_status: 'trial',
    active_status: true,
    created_at: new Date().toISOString()
  };
  
  const newUserId = db.data.users.length + 1;
  const newUser = {
    id: String(newUserId),
    email: school_it_email || `admin${newSchoolId}@example.com`,
    password: school_it_password || 'password123',
    first_name: school_it_first_name || 'Campus',
    last_name: school_it_last_name || 'Admin',
    roles: ['school_IT'],
    is_active: true,
    school_id: newSchoolId,
    created_at: new Date().toISOString()
  };
  
  db.data.schools.push(newSchool);
  db.data.users.push(newUser);
  await db.write();
  
  res.status(201).json({
    school: newSchool,
    user: newUser,
    generated_temporary_password: school_it_password ? undefined : 'password123'
  });
});

app.patch('/governance/requests/:id', async (req, res) => {
  const { id } = req.params;
  console.log(`[PATCH] /governance/requests/${id}`);
  await parseBody(req);
  const request = db.data.governance_requests.find(r => String(r.id) === String(id));
  if (request) {
    Object.assign(request, req.body);
    request.resolved_at = new Date().toISOString();
    await db.write();
    res.json(request);
  } else {
    res.status(404).json({ error: 'Request not found' });
  }
});

app.get('/governance/requests', (req, res, next) => {
  req.url = req.url.replace('/governance/requests', '/governance_requests');
  next();
});

app.get('/:name', async (req, res, next) => {
  const { name = '' } = req.params;
  console.log(`[GET] /${name}`);
  const queryString = req.url.split('?')[1] ?? '';
  const params = new URLSearchParams(queryString);
  const where = {};
  for (const [key, value] of params.entries()) {
    if (!['_sort', '_page', '_per_page', '_embed', '_where'].includes(key)) {
      where[key] = value;
    }
  }
  res.locals['data'] = await service.find(name, { where });
  next?.();
});

app.get('/:name/:id', async (req, res, next) => {
  const { name = '', id = '' } = req.params;
  console.log(`[GET] /${name}/${id}`);
  res.locals['data'] = await service.findById(name, id, req.query);
  next?.();
});

async function parseJsonBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        req.body = JSON.parse(body || '{}');
      } catch {
        req.body = {};
      }
      resolve();
    });
  });
}

const withBody = (action) => {
  return async (req, res, next) => {
    await parseJsonBody(req);
    const { name = '' } = req.params;
    if (!req.body || typeof req.body !== 'object' || Array.isArray(req.body)) {
      res.status(400).json({ error: 'Body must be a JSON object' });
      return;
    }
    res.locals['data'] = await action(name, req.body);
    next?.();
  };
};

const withIdAndBody = (action) => {
  return async (req, res, next) => {
    await parseJsonBody(req);
    const { name = '', id = '' } = req.params;
    if (!req.body || typeof req.body !== 'object' || Array.isArray(req.body)) {
      res.status(400).json({ error: 'Body must be a JSON object' });
      return;
    }
    res.locals['data'] = await action(name, id, req.body);
    next?.();
  };
};

app.post('/:name', async (req, res, next) => {
  console.log(`[POST] /${req.params.name}`);
  await parseJsonBody(req);
  const { name = '' } = req.params;
  if (!req.body || typeof req.body !== 'object' || Array.isArray(req.body)) {
    res.status(400).json({ error: 'Body must be a JSON object' });
    return;
  }
  res.locals['data'] = await service.create(name, req.body);
  next?.();
});

app.post('/:name/', async (req, res, next) => {
  console.log(`[POST] /${req.params.name}/`);
  await parseJsonBody(req);
  const { name = '' } = req.params;
  if (!req.body || typeof req.body !== 'object' || Array.isArray(req.body)) {
    res.status(400).json({ error: 'Body must be a JSON object' });
    return;
  }
  res.locals['data'] = await service.create(name, req.body);
  next?.();
});

app.put('/:name', withBody(service.update.bind(service)));
app.put('/:name/', withBody(service.update.bind(service)));
app.put('/:name/:id', withIdAndBody(service.updateById.bind(service)));
app.patch('/:name', withBody(service.patch.bind(service)));
app.patch('/:name/', withBody(service.patch.bind(service)));
app.patch('/:name/:id', withIdAndBody(service.patchById.bind(service)));
app.delete('/:name/:id', async (req, res, next) => {
  console.log(`[DELETE] /${req.params.name}/${req.params.id}`);
  const { name = '', id = '' } = req.params;
  res.locals['data'] = await service.destroyById(name, id, req.query['_dependent']);
  next?.();
});

app.use('/:name', (req, res) => {
  console.log(`[USE] /${req.params.name} - method: ${req.method}`);
  const { data } = res.locals;
  console.log(`  data: ${JSON.stringify(data)?.slice(0, 100)}`);
  if (data === undefined) {
    res.status(404).json({ error: 'Not Found' });
  } else {
    if (req.method === 'POST') res.status(201);
    res.json(data);
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`\x1b[32m✔ Mock API Server running on http://localhost:${PORT}\x1b[0m`);
  console.log(`\x1b[36mMulti-campus support enabled\x1b[0m`);
  console.log(`\x1b[33mTest credentials:\x1b[0m`);
  console.log(`  Campus 1 (Mock University):`);
  console.log(`    Admin: admin@example.com / password123`);
  console.log(`    School IT: it@example.com / password123`);
  console.log(`    Student: student@example.com / password123`);
  console.log(`  Campus 2 (North Campus College):`);
  console.log(`    School IT: it-north@example.com / password123`);
  console.log(`    Student: student-north@example.com / password123`);
  console.log(`  Campus 3 (South Institute):`);
  console.log(`    School IT: it-south@example.com / password123`);
  console.log('');
  console.log('Available resources:');
  if (db.data) {
    const resources = ['users', 'schools', 'departments', 'programs', 'events', 'attendance', 'governance_units', 'audit_logs', 'notification_logs', 'governance_requests'];
    resources.forEach(key => {
      if (db.data[key]) {
        console.log(`  http://localhost:${PORT}/${key}`);
      }
    });
  }
});
