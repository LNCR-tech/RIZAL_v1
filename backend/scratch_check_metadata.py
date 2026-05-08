import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models.core.base import AppBase
from app.models import platform_features, user, school, event  # Import models to register them

print("Tables in metadata:")
for table_name in AppBase.metadata.tables.keys():
    print(f" - {table_name}")

if 'privacy_consent_types' in AppBase.metadata.tables:
    print("\nSUCCESS: privacy_consent_types is in metadata.")
else:
    print("\nFAILURE: privacy_consent_types is NOT in metadata.")
