import pytest
from app.core.database import SessionLocal
import tempfile
import csv

@pytest.fixture
def mock_csv_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "first_name", "last_name", "email", "department_name", "program_name", "year_level"])
        # Valid row
        writer.writerow(["1001", "John", "Doe", "john@test.com", "Test Department", "Test Program", "1"])
        # Duplicate email
        writer.writerow(["1002", "Jane", "Doe", "john@test.com", "Test Department", "Test Program", "2"])
        # Invalid department
        writer.writerow(["1003", "Bob", "Smith", "bob@test.com", "Fake Dept", "Test Program", "3"])
    yield f.name

def test_bulk_import_validation(client, campus_admin_headers, mock_csv_file):
    with open(mock_csv_file, 'rb') as f:
        files = {"file": ("students.csv", f, "text/csv")}
        r = client.post("/api/v1/admin/import/students", headers=campus_admin_headers, files=files)
        
    assert r.status_code in [200, 400], "Should either return partial success or 400 failure on invalid data"
    if r.status_code == 200:
        data = r.json()
        assert "failed_rows" in data, "Must return failure report for bad rows"
        assert len(data["failed_rows"]) >= 2, "Duplicate email and invalid department should fail"
