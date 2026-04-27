import io
import openpyxl


def _make_xlsx(rows: list[dict]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = ["Student_ID", "Email", "Last Name", "First Name", "Middle Name", "Department", "Course"]
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_preview_import_valid(client, campus_admin_headers):
    xlsx = _make_xlsx([{
        "Student_ID": "2024-0001",
        "Email": "import_test@test.local",
        "Last Name": "Doe",
        "First Name": "John",
        "Middle Name": "",
        "Department": "Test Department",
        "Course": "Test Program",
    }])
    r = client.post(
        "/api/admin/import-students/preview",
        headers=campus_admin_headers,
        files={"file": ("students.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 200


def test_preview_import_invalid_file(client, campus_admin_headers):
    r = client.post(
        "/api/admin/import-students/preview",
        headers=campus_admin_headers,
        files={"file": ("bad.txt", b"not an excel file", "text/plain")},
    )
    assert r.status_code in (400, 422)


def test_import_requires_auth(client):
    r = client.post("/api/admin/import-students/preview", files={"file": ("f.xlsx", b"", "application/octet-stream")})
    assert r.status_code == 401


def test_student_cannot_import(client, student_headers):
    xlsx = _make_xlsx([])
    r = client.post(
        "/api/admin/import-students/preview",
        headers=student_headers,
        files={"file": ("students.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 403
