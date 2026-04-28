import io
import pytest


def _make_valid_xlsx():
    """Build a minimal valid import Excel file in memory."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Student_ID", "Email", "Last Name", "First Name", "Middle Name", "Department", "Course"])
    ws.append(["STU-IMPORT-001", "importtest001@test.com", "Import", "Test", "", "Test Department", "Test Program"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


@pytest.fixture(scope="module")
def preview_token(client, campus_admin_headers, db_session):
    import time
    from app.models.department import Department
    from app.models.program import Program
    from app.models.school import School
    school = db_session.query(School).filter_by(school_code="TEST-001").first()
    dept = db_session.query(Department).filter_by(school_id=school.id).first()
    prog = db_session.query(Program).filter_by(school_id=school.id).first()
    
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Student_ID", "Email", "Last Name", "First Name", "Middle Name", "Department", "Course"])
    unique = int(time.time())
    ws.append([f"STU-IMPORT-{unique}", f"importtest{unique}@test.com", "Import", "Test", "", dept.name, prog.name])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    xlsx_bytes = buf.read()
    
    r = client.post(
        "/api/admin/import-students/preview",
        headers=campus_admin_headers,
        files={"file": ("students.xlsx", xlsx_bytes,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    if not data.get("can_commit"):
        pytest.skip(f"Preview has invalid rows: {data}")
    return data.get("preview_token")


@pytest.fixture(scope="module")
def import_job_id(client, campus_admin_headers, preview_token):
    if not preview_token:
        pytest.skip("No preview token available")
    r = client.post(
        "/api/admin/import-students",
        headers=campus_admin_headers,
        data={"preview_token": preview_token},
    )
    assert r.status_code == 200, r.text
    return r.json()["job_id"]


def test_import_template_download(client, campus_admin_headers):
    r = client.get("/api/admin/import-students/template", headers=campus_admin_headers)
    assert r.status_code == 200
    assert "spreadsheet" in r.headers.get("content-type", "")


def test_import_template_requires_auth(client):
    r = client.get("/api/admin/import-students/template")
    assert r.status_code == 401


def test_import_start_returns_job_id(import_job_id):
    assert import_job_id is not None


def test_import_status(client, campus_admin_headers, import_job_id, db_session):
    r = client.get(f"/api/admin/import-status/{import_job_id}", headers=campus_admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "state" in data
    # With eager mode the job runs synchronously — it must be completed by now
    assert data["state"] == "completed", (
        f"Expected completed, got: {data['state']}. "
        f"Errors: {data.get('errors')} "
        f"Job data: {data}"
    )
    assert data.get("success_count", 0) >= 1


def test_import_creates_student(client, campus_admin_headers, import_job_id, db_session):
    """Verify the import actually inserted a student user into the database."""
    from app.models.user import User
    from app.models.import_job import BulkImportJob
    from app.core.database import SessionLocal
    with SessionLocal() as fresh_db:
        job = fresh_db.query(BulkImportJob).filter_by(id=import_job_id).first()
        job_error = job.error_summary if job else "job not found"
        student = fresh_db.query(User).filter(
            User.email.like("importtest%@test.com")
        ).first()
    assert student is not None, (
        f"Imported student user was not found in the database. "
        f"Job error: {job_error}"
    )


def test_import_status_requires_auth(client, import_job_id):
    r = client.get(f"/api/admin/import-status/{import_job_id}")
    assert r.status_code == 401


def test_import_errors_download(client, campus_admin_headers, import_job_id):
    r = client.get(f"/api/admin/import-errors/{import_job_id}/download", headers=campus_admin_headers)
    # 404 if no errors (job succeeded or no failed rows), 200 if errors exist
    assert r.status_code in (200, 404)


def test_retry_failed_no_errors(client, campus_admin_headers, import_job_id):
    r = client.post(
        f"/api/admin/import-students/retry-failed/{import_job_id}",
        headers=campus_admin_headers,
    )
    # 400 if no failed rows to retry, 200 if there are
    assert r.status_code in (200, 400)


def test_preview_error_download(client, campus_admin_headers, preview_token):
    if not preview_token:
        pytest.skip("No preview token")
    r = client.get(
        f"/api/admin/import-preview-errors/{preview_token}/download",
        headers=campus_admin_headers,
    )
    assert r.status_code in (200, 404)


def test_preview_remove_invalid(client, campus_admin_headers, preview_token):
    if not preview_token:
        pytest.skip("No preview token")
    r = client.post(
        f"/api/admin/import-preview-errors/{preview_token}/remove-invalid",
        headers=campus_admin_headers,
    )
    # 200 if valid rows exist, 400 if none
    assert r.status_code in (200, 400)


def test_import_start_without_preview_token(client, campus_admin_headers):
    r = client.post("/api/admin/import-students", headers=campus_admin_headers, data={})
    assert r.status_code == 400


def test_import_requires_auth(client):
    r = client.post("/api/admin/import-students", data={})
    assert r.status_code == 401
