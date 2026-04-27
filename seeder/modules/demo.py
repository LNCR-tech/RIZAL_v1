import csv
import logging
import random
import string
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from modules.data import (
    FIRST_NAMES, LAST_NAMES, MIDDLE_NAMES, SUFFIXES,
    SCHOOL_NAMES, COLLEGES_DATASET, EVENT_THEMES, EVENT_LOCATIONS,
    ANNOUNCEMENT_DATA, MOCK_NOTE_TAGS, MOCK_NOTES_POOL, COMPLIANCE_NOTES,
    EVENT_TYPES
)
from app.models.event import EventStatus as DBEventStatus
from modules.helpers import (
    get_random_date_in_range, chunked, hash_passwords_parallel, 
    pick_colleges, is_absent, apply_suffix
)
from modules.core import (
    get_or_create_school, get_or_create_department, get_or_create_program,
    link_program_to_department, create_user, assign_role, 
    create_student_profile, create_governance_unit, assign_unit_permissions,
    create_governance_member, set_member_permissions, create_event,
    create_sanction_config, create_sanction_delegation, SanctionDelegationScopeType,
    create_announcement, create_student_note, create_compliance_history
)

from app.models.user import User, StudentProfile
from app.models.attendance import Attendance, AttendanceStatus
from app.models.sanctions import SanctionRecord, SanctionItem, SanctionComplianceStatus, SanctionItemStatus
from app.models.governance_hierarchy import GovernanceUnitType, PermissionCode

logger = logging.getLogger(__name__)

# Permission sets
SSG_PERMISSIONS = [p for p in PermissionCode]
SG_PERMISSIONS = [
    PermissionCode.CREATE_ORG, PermissionCode.MANAGE_STUDENTS, PermissionCode.VIEW_STUDENTS,
    PermissionCode.MANAGE_EVENTS, PermissionCode.MANAGE_ATTENDANCE, PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST,
    PermissionCode.APPROVE_SANCTION_COMPLIANCE, PermissionCode.VIEW_SANCTIONS_DASHBOARD
]
ORG_PERMISSIONS = [
    PermissionCode.VIEW_STUDENTS, PermissionCode.MANAGE_EVENTS, PermissionCode.MANAGE_ATTENDANCE
]

def run_demo(
    db: Session,
    *,
    rng: random.Random,
    n_schools: int,
    min_students: int,
    max_students: int,
    min_events: int,
    max_events: int,
    min_colleges: int,
    max_colleges: int,
    min_programs: int,
    start_date: tuple[int, int, int],
    end_date: tuple[int, int, int],
    suffix_probability: float,
    unique_passwords: bool,
    credentials_format: str = "csv",
    seed_admin_email: str = None,
    seed_admin_password: str = None
) -> None:
    now = datetime.now(timezone.utc)
    
    # Use centralized event types from config.py
    type_pool = EVENT_TYPES

    # Roll for this universe's "Chaos Climatology" 
    # (Probability of things going wrong in this specific seeder run)
    cancellation_prob_base = rng.uniform(0.02, 0.07) 
    emergency_cutoff_prob = rng.uniform(0.1, 0.25)
    
    logger.info(f"Stochastic Chaos Config: Cancellation Base={cancellation_prob_base:.2%}, Emergency Cutoff={emergency_cutoff_prob:.2%}")
    # Determine format settings
    fmt_map = {
        "csv": (",", ".csv"),
        "tsv": ("\t", ".tsv"),
        "psv": ("|", ".psv")
    }
    delim, ext = fmt_map.get(credentials_format.lower(), (",", ".csv"))
    
    storage_dir = Path("storage/seeder_outputs")
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    admins_file = storage_dir / f"campus_admin_credentials{ext}"
    gov_file = storage_dir / f"student_governance_credentials{ext}"
    student_file = storage_dir / f"student_credentials{ext}"
    
    # Initialize files and write headers
    header = ["School", "Role", "Email", "Password", "First Name", "Last Name"]
    for fpath in [admins_file, gov_file, student_file]:
        with open(fpath, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delim)
            writer.writerow(header)

    # Sample unique school names to prevent collisions within the loop
    selected_school_names = rng.sample(SCHOOL_NAMES, k=min(n_schools, len(SCHOOL_NAMES)))
    
    for i, school_name in enumerate(selected_school_names):
        logger.info(f"Generating School {i+1}/{len(selected_school_names)}: {school_name}")
        
        school_domain = "".join(c for c in school_name if c.isalpha()).lower() + ".edu.ph"
        
        school = get_or_create_school(
            db, 
            name=school_name, 
            school_name=school_name, 
            school_code=school_name[:3].upper() + "U"
        )
        
        # 1. Colleges & Programs
        n_colleges = rng.randint(min_colleges, max_colleges)
        chosen_acad = pick_colleges(rng, COLLEGES_DATASET, n_colleges, min_programs=min_programs)
        program_pool = []
        for dept_name, prog_names in chosen_acad.items():
            dept = get_or_create_department(db, school_id=school.id, name=dept_name)
            for pname in prog_names:
                prog = get_or_create_program(db, school_id=school.id, name=pname)
                link_program_to_department(db, prog, dept)
                program_pool.append(prog)
                
        # 2. Campus Admin
        admin_email = f"admin@{school_domain}"
        admin_pw = "CampusAdmin123!"
        admin_hash = hash_passwords_parallel([admin_pw], rounds=6, workers=1)[0]
        
        campus_admin = db.query(User).filter_by(email=admin_email).first()
        if not campus_admin:
            campus_admin = create_user(
                db, email=admin_email, school_id=school.id, password_hash=admin_hash, 
                first_name="Admin", last_name="Campus"
            )
            assign_role(db, campus_admin, "campus_admin")
        
        with open(admins_file, 'a', newline='') as f:
            csv.writer(f, delimiter=delim).writerow([school.name, "Campus Admin", admin_email, admin_pw, "Admin", "Campus"])
            
        # 3. Governance Units
        ssg_unit = create_governance_unit(
            db, school_id=school.id, unit_code=f"SSG-{school.id}", unit_name="Supreme Student Government",
            unit_type=GovernanceUnitType.SSG, parent_id=None
        )
        assign_unit_permissions(db, ssg_unit.id, SSG_PERMISSIONS)
        
        # [PROD-SEED] SSG Announcements
        num_ann = rng.randint(2, 4)
        for ann_item in rng.sample(ANNOUNCEMENT_DATA, num_ann):
            create_announcement(
                db, unit_id=ssg_unit.id, school_id=school.id,
                title=ann_item["title"], body=ann_item["body"],
                created_by=campus_admin.id
            )
        
        from app.models.department import Department
        
        sg_units = []
        org_units = []
        # Manually query departments since the relationship is missing in the School model
        school_depts = db.query(Department).filter_by(school_id=school.id).all()
        
        for dept in school_depts:
            # Calculate a temporary code for display logic since the DB model lacks the 'code' field
            dept_code = dept.name[:10].upper()
            
            sg = create_governance_unit(
                db, school_id=school.id, unit_code=f"SG-{dept.id}", unit_name=f"{dept.name} Student Gov",
                unit_type=GovernanceUnitType.SG, parent_id=ssg_unit.id, department_id=dept.id
            )
            assign_unit_permissions(db, sg.id, SG_PERMISSIONS)
            
            # [PROD-SEED] SG Announcements
            if rng.random() > 0.3:
                ann_item = rng.choice(ANNOUNCEMENT_DATA)
                create_announcement(
                    db, unit_id=sg.id, school_id=school.id,
                    title=f"[{dept_code}] {ann_item['title']}", body=ann_item["body"],
                    created_by=campus_admin.id
                )
            
            sg_units.append(sg)
            
            num_orgs = rng.randint(0, 2)
            for j in range(num_orgs):
                org = create_governance_unit(
                    db, school_id=school.id, unit_code=f"ORG-{sg.id}-{j}", unit_name=f"{dept_code} Sub-Org {j+1}",
                    unit_type=GovernanceUnitType.ORG, parent_id=sg.id, department_id=dept.id
                )
                assign_unit_permissions(db, org.id, ORG_PERMISSIONS)
                org_units.append(org)

        # 4. Students
        n_students = rng.randint(min_students, max_students)
        logger.info(f"Generating {n_students} students for {school_name}...")
        
        prog_weights = [rng.randint(10, 100) for _ in program_pool]
        assigned_progs = rng.choices(program_pool, weights=prog_weights, k=n_students)
        
        student_users = []
        student_profiles = []
        passwords = []
        used_student_ids = set()
        used_emails = set()
        
        for p in range(n_students):
            if unique_passwords:
                pw = "".join(rng.choices(string.ascii_letters + string.digits, k=10)) + "1!"
            else:
                pw = "Student123!"
            passwords.append(pw)
            
        hashes = hash_passwords_parallel(passwords, rounds=6)
        
        # Store email -> password for later logging of officers
        pwd_lookup = {}
        
        for k in range(n_students):
            fname = rng.choice(FIRST_NAMES)
            lname = rng.choice(LAST_NAMES)
            mname = rng.choice(MIDDLE_NAMES)
            name_suffix = apply_suffix(rng, "", SUFFIXES, suffix_probability).strip() or None
            
            base_email = f"{fname.split()[0].lower()}.{lname.split()[-1].lower()}"
            n = rng.randint(1, 99)
            email = f"{base_email}{n}@{school_domain}"
            while email in used_emails:
                n = rng.randint(1, 9999)
                email = f"{base_email}{n}@{school_domain}"
            used_emails.add(email)
            
            u = create_user(
                db, email=email, school_id=school.id, password_hash=hashes[k],
                first_name=fname, middle_name=mname, last_name=lname,
                suffix=name_suffix
            )
            assign_role(db, u, "student")
            prog = assigned_progs[k]
            
            # Ensure unique student_id for this school
            while True:
                sid = f"{start_date[2]}-{rng.randint(10000, 99999)}"
                if sid not in used_student_ids:
                    used_student_ids.add(sid)
                    break
            
            prof = create_student_profile(
                db, user_id=u.id, school_id=school.id, student_id=sid,
                department_id=prog.departments[0].id if prog.departments else None,
                program_id=prog.id, year_level=rng.randint(1, 4)
            )
            student_users.append(u)
            student_profiles.append(prof)
            pwd_lookup[u.email] = passwords[k]
            
            with open(student_file, 'a', newline='') as f:
                csv.writer(f, delimiter=delim).writerow([school.name, "Student", email, passwords[k], fname, lname])
                    
        # 4b. Assign random students to Governance Units as Officers (Allowing Overlaps)
        logger.info(f"Assigning student officers to governance units with potential hybrid overlays...")
        
        # Isolate the top ~15% of students as the active "leader pool"
        num_leaders = max(5, int(n_students * 0.15))
        leaders = rng.sample(student_users, min(num_leaders, len(student_users)))
        
        # Assign 3-5 SSG Officers from leaders
        num_ssg_officers = min(len(leaders), rng.randint(3, 5))
        ssg_officers = rng.sample(leaders, num_ssg_officers)
        for u in ssg_officers:
            mem = create_governance_member(db, unit_id=ssg_unit.id, user_id=u.id, position_title="SSG Officer")
            k_perms = rng.randint(1, len(SSG_PERMISSIONS))
            set_member_permissions(db, mem.id, rng.sample(SSG_PERMISSIONS, k_perms))
            
            # Log officer
            with open(gov_file, 'a', newline='') as f:
                csv.writer(f, delimiter=delim).writerow([school.name, "SSG Officer", u.email, pwd_lookup.get(u.email, "???"), u.first_name, u.last_name])
            
        # Assign 1-3 SG Officers per SG Unit from leaders
        for sg in sg_units:
            num_sg_officers = min(len(leaders), rng.randint(1, 3))
            sg_officers = rng.sample(leaders, num_sg_officers)
            for u in sg_officers:
                mem = create_governance_member(db, unit_id=sg.id, user_id=u.id, position_title="SG Officer")
                k_perms = rng.randint(1, len(SG_PERMISSIONS))
                set_member_permissions(db, mem.id, rng.sample(SG_PERMISSIONS, k_perms))
                
                # Log officer
                with open(gov_file, 'a', newline='') as f:
                    csv.writer(f, delimiter=delim).writerow([school.name, f"SG Officer ({sg.unit_name})", u.email, pwd_lookup.get(u.email, "???"), u.first_name, u.last_name])
                
        # Assign 1-2 ORG Officers per ORG Unit from leaders
        for org in org_units:
            num_org_officers = min(len(leaders), rng.randint(1, 2))
            org_officers = rng.sample(leaders, num_org_officers)
            for u in org_officers:
                mem = create_governance_member(db, unit_id=org.id, user_id=u.id, position_title="ORG Officer")
                k_perms = rng.randint(1, len(ORG_PERMISSIONS))
                set_member_permissions(db, mem.id, rng.sample(ORG_PERMISSIONS, k_perms))
                
                # Log officer
                with open(gov_file, 'a', newline='') as f:
                    csv.writer(f, delimiter=delim).writerow([school.name, f"ORG Officer ({org.unit_name})", u.email, pwd_lookup.get(u.email, "???"), u.first_name, u.last_name])
                    
        # [PROD-SEED] Internal Student Notes (~10% coverage)
        num_notes = max(1, int(n_students * 0.1))
        noted_students = rng.sample(student_profiles, num_notes)
        for prof in noted_students:
            creator = rng.choice(leaders)
            unit_id = ssg_unit.id if rng.random() > 0.5 else rng.choice(sg_units).id
            create_student_note(
                db, unit_id=unit_id, student_id=prof.id, school_id=school.id,
                tags=rng.sample(MOCK_NOTE_TAGS, rng.randint(1, 2)),
                notes=rng.choice(MOCK_NOTES_POOL),
                created_by=creator.id
            )
                    
        # 5. Events
        n_events = rng.randint(min_events, max_events)
        logger.info(f"Generating {n_events} events for {school_name}...")
        
        SCOPE_WEIGHTS = {"school": 15, "department": 25, "program": 60}
        events = []
        
        for e in range(n_events):
            start = get_random_date_in_range(
                rng, start_year=start_date[2], end_year=end_date[2],
                start_month_day=(start_date[0], start_date[1]),
                end_month_day=(end_date[0], end_date[1])
            )
            # Ensure timezone awareness
            start = start.replace(tzinfo=timezone.utc)
            duration_hours = rng.randint(1, 4)
            end = start + timedelta(hours=duration_hours)
            
            # 1. Determine Stochastic Status
            status = DBEventStatus.UPCOMING
            is_emergency_cancelled = False
            
            if end < now:
                # Past event: Mostly completed, some cancelled
                if rng.random() < cancellation_prob_base:
                    status = DBEventStatus.CANCELLED
                    # Was it cancelled midway (emergency)?
                    if rng.random() < emergency_cutoff_prob:
                        is_emergency_cancelled = True
                else:
                    status = DBEventStatus.COMPLETED
            elif start < now < end:
                # Active event: 98% Ongoing, 2% Cancelled midway
                if rng.random() < 0.02:
                    status = DBEventStatus.CANCELLED
                    is_emergency_cancelled = True
                else:
                    status = DBEventStatus.ONGOING
            else:
                # Future event: 97% Upcoming, 3% Pre-emptively Cancelled
                if rng.random() < 0.03:
                    status = DBEventStatus.CANCELLED
                else:
                    status = DBEventStatus.UPCOMING

            ev = create_event(
                db, 
                school_id=school.id, 
                name=rng.choice(EVENT_THEMES), 
                location=rng.choice(EVENT_LOCATIONS), 
                start_dt=start, 
                end_dt=end,
                status=status,
                event_type=rng.choice(type_pool)
            )
            
            # Stochastic Grace Periods (diversifies the analytics data)
            ev.early_check_in_minutes = rng.randint(15, 45)
            ev.late_threshold_minutes = rng.randint(5, 20)
            
            # Track if this event should have attendance records
            # We'll attach this to the object temporary for the next loop
            ev._seeder_chaos_is_emergency = is_emergency_cancelled 
            
            # Funnel scope logic
            scope = rng.choices(list(SCOPE_WEIGHTS.keys()), weights=list(SCOPE_WEIGHTS.values()), k=1)[0]
            if scope == "program":
                ev.programs.append(rng.choice(program_pool))
            elif scope == "department" and school_depts:
                ev.departments.append(rng.choice(school_depts))
            
            events.append(ev)
            
            # Event Sanction Config
            conf = create_sanction_config(
                db, school_id=school.id, event_id=ev.id, 
                items_def=[
                    {"item_code": "LETTER", "item_name": "Apology Letter", "description": "Handwritten apology letter"},
                    {"item_code": "FINE", "item_name": "Community Fine", "description": "50 PHP community tax"}
                ]
            )
            ev._seeder_sanction_config_id = conf.id
            
            if sg_units and rng.random() > 0.5:
                # delegate this event to a random SG unit
                create_sanction_delegation(
                    db, school_id=school.id, event_id=ev.id, config_id=conf.id, 
                    unit_id=rng.choice(sg_units).id, scope_type=SanctionDelegationScopeType.UNIT
                )
        
        # 6. Attendances and Sanctions
        logger.info("Generating attendances and sanctions...")
        
        # Core rows computation
        attendance_batch = []
        sanction_record_batch = []
        sanction_item_batch = []
        
        for e_idx, ev in enumerate(events):
            # Retrieve the sanction config ID that was created for this event
            conf = ev._seeder_sanction_config_id if hasattr(ev, '_seeder_sanction_config_id') else None
            
            # CHAOS ENGINE: Determine if we should generate attendance for this event
            # Logic:
            # - COMPLETED: 100% of attendance roles (Full data)
            # - ONGOING: 20-70% of roles (Live simulation)
            # - CANCELLED (Emergency): 1-15% of roles (Panic snapshot)
            # - CANCELLED (Pre-emptive): 0%
            # - UPCOMING: 0% (Hallucination Protection)
            
            attendance_gate_prob = 0.0
            if ev.status == DBEventStatus.COMPLETED:
                attendance_gate_prob = 1.0
            elif ev.status == DBEventStatus.ONGOING:
                attendance_gate_prob = rng.uniform(0.2, 0.7)
            elif ev.status == DBEventStatus.CANCELLED and getattr(ev, '_seeder_chaos_is_emergency', False):
                attendance_gate_prob = rng.uniform(0.01, 0.15)
            
            if attendance_gate_prob <= 0:
                continue # Skip this event (Upcoming or Pre-emptively Cancelled)

            for s_idx, prof in enumerate(student_profiles):
                # Only a subset of students "managed to record" for ongoing/emergency events
                if rng.random() > attendance_gate_prob:
                    continue

                # Deterministic absence logic per student/event
                absent = is_absent(rng, base_prob=0.25)
                # Use .value because the Backend model uses raw strings in PG_ENUM
                status = AttendanceStatus.ABSENT.value if absent else rng.choices([AttendanceStatus.PRESENT.value, AttendanceStatus.LATE.value], weights=[80, 20], k=1)[0]
                
                att = Attendance(
                    student_profile_id=prof.id,
                    event_id=ev.id,
                    time_in=ev.start_at,
                    method_code="manual",
                    status_code=status
                )
                attendance_batch.append((att, absent, conf))

        # We need to add the attendances so they get IDs (if we batch insert, they won't automatically get populated)
        # Instead, we do db.add_all, flush
        for chunk in chunked(attendance_batch, 2000):
            atts = [x[0] for x in chunk]
            db.add_all(atts)
            db.flush()
            
            for att, absent, conf_id in chunk:
                if absent and conf_id: # create sanction records
                    # [PROD-SEED] Compliance Simulation (~30% resolved)
                    is_resolved = rng.random() < 0.3
                    res_status = SanctionComplianceStatus.COMPLIED if is_resolved else SanctionComplianceStatus.PENDING
                    item_status = SanctionItemStatus.COMPLIED if is_resolved else SanctionItemStatus.PENDING
                    
                    srec = SanctionRecord(
                        school_id=school.id,
                        event_id=att.event_id,
                        sanction_config_id=conf_id,
                        student_profile_id=att.student_id,
                        attendance_id=att.id,
                        status=res_status,
                        complied_at=now if is_resolved else None,
                        notes="Auto-resolved by stochastic seeder" if is_resolved else None
                    )
                    db.add(srec)
                    db.flush()
                    
                    items = [
                        SanctionItem(
                            sanction_record_id=srec.id,
                            item_code="LETTER",
                            item_name="Apology Letter",
                            status=item_status,
                            complied_at=now if is_resolved else None
                        ),
                        SanctionItem(
                            sanction_record_id=srec.id,
                            item_code="FINE",
                            item_name="Community Fine",
                            status=item_status,
                            complied_at=now if is_resolved else None
                        )
                    ]
                    db.add_all(items)
                    db.flush()
                    
                    if is_resolved:
                        for itm in items:
                            create_compliance_history(
                                db, school_id=school.id, event_id=att.event_id,
                                record_id=srec.id, item_id=itm.id, student_id=att.student_id,
                                complied_by=rng.choice(leaders).id,
                                notes=rng.choice(COMPLIANCE_NOTES)
                            )
            db.commit()
                
    logger.info(f"Demo seeding complete. Credentials saved to {storage_dir} in {credentials_format.upper()} format.")
