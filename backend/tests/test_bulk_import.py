import pytest
from app.core.database import SessionLocal
import tempfile
import csv

@pytest.fixture
def mock_csv_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(["Student_ID", "Email", "Last_Name", "First_Name", "Middle_Initial", "Department", "Course"])
        # Valid row
        writer.writerow(["1001", "john@test.com", "Doe", "John", "A", "Test Department", "Test Program"])
        # Duplicate email
        writer.writerow(["1002", "john@test.com", "Doe", "Jane", "B", "Test Department", "Test Program"])
        # Invalid department
        writer.writerow(["1003", "bob@test.com", "Smith", "Bob", "C", "Fake Dept", "Test Program"])
    yield f.name

def test_bulk_import_validation(client, campus_admin_headers, mock_csv_file):
    with open(mock_csv_file, 'rb') as f:
        files = {"file": ("students.csv", f, "text/csv")}
        r = client.post("/api/v1/admin/import-students/preview", headers=campus_admin_headers, files=files)
        
    assert r.status_code in [200, 400], "Should either return partial success or 400 failure on invalid data"
    if r.status_code == 200:
        data = r.json()
        assert "invalid_rows" in data, "Must return failure report for bad rows"
        assert data["invalid_rows"] >= 2, "Duplicate email and invalid department should fail"
