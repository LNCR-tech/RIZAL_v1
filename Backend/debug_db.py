import traceback
import logging
import sys

# Redirect all output to a file
with open('/tmp/debug_output.txt', 'w') as f:
    sys.stdout = f
    sys.stderr = f
    logging.disable(logging.CRITICAL)
    
    try:
        from app.models.base import Base
        from app.database import engine
        from app.models.role import Role
        from app.models.user import User, UserRole
        print('Tables in metadata:', list(Base.metadata.tables.keys()))
        Base.metadata.create_all(bind=engine)
        print('CREATE ALL SUCCESS')
    except Exception as e:
        print(f'\n\nERROR TYPE: {type(e).__name__}')
        print(f'ERROR MESSAGE: {e}')
        traceback.print_exc()

# Read and print file contents
with open('/tmp/debug_output.txt', 'r') as f:
    print(f.read(), file=sys.__stdout__)
