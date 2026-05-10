import sys
import os
from pathlib import Path

# Add backend to sys.path
backend_path = Path("backend").resolve()
sys.path.insert(0, str(backend_path))

try:
    from app.services.school_feature_flags import privileged_face_verification_enabled_for_school
    print("Import school_feature_flags: SUCCESS")
    from app.services.auth_session import issue_login_token_response
    print("Import auth_session: SUCCESS")
except Exception as e:
    print(f"Import FAILED: {e}")
    import traceback
    traceback.print_exc()
