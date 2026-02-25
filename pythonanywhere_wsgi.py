# PythonAnywhere WSGI Configuration
# Copy this content to your WSGI file in PythonAnywhere Web tab

import os
import sys

# Add project path
path = '/home/osamaalii/ibb_guide_main'
if path not in sys.path:
    sys.path.insert(0, path)

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(path, '.env'))
except Exception:
    pass

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.prod')

# Get WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
