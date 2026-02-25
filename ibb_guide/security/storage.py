"""
Secure File Storage Backends
Provides:
- Private storage for sensitive documents
- Safe filename generation
- Path traversal prevention
"""
import os
import uuid
import re
from datetime import datetime
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.text import slugify


class PrivateFileStorage(FileSystemStorage):
    """
    Storage backend for private/sensitive files.
    Files stored here are NOT directly accessible via web server.
    Must be served through protected views.
    """
    
    def __init__(self, *args, **kwargs):
        # Use PRIVATE_MEDIA_ROOT from settings
        location = getattr(settings, 'PRIVATE_MEDIA_ROOT', None)
        if not location:
            location = os.path.join(settings.BASE_DIR, 'private_media')
        
        kwargs['location'] = location
        kwargs['base_url'] = None  # No public URL
        super().__init__(*args, **kwargs)
    
    def url(self, name):
        """Private files have no public URL."""
        raise ValueError(
            "Private files cannot be accessed via URL. "
            "Use ServePrivateDocumentView instead."
        )


# Singleton instance
private_storage = PrivateFileStorage()


def safe_filename(filename: str, max_length: int = 100) -> str:
    """
    Generate a safe filename from user input.
    
    - Removes path components
    - Sanitizes special characters
    - Limits length
    - Preserves extension
    """
    if not filename:
        return f"file_{uuid.uuid4().hex[:8]}"
    
    # Remove path components (prevent traversal)
    filename = os.path.basename(filename)
    
    # Split name and extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        ext = ext.lower()[:10]  # Limit extension length
    else:
        name = filename
        ext = ''
    
    # Sanitize name
    name = slugify(name, allow_unicode=True)
    if not name:
        name = uuid.uuid4().hex[:8]
    
    # Limit length
    if len(name) > max_length - len(ext) - 1:
        name = name[:max_length - len(ext) - 1]
    
    return f"{name}.{ext}" if ext else name


def generate_unique_filename(original_filename: str, prefix: str = '') -> str:
    """
    Generate a unique filename with UUID to prevent collisions.
    
    Format: prefix_uuid_sanitized.ext
    """
    safe_name = safe_filename(original_filename)
    unique_id = uuid.uuid4().hex[:12]
    
    if '.' in safe_name:
        name, ext = safe_name.rsplit('.', 1)
        if prefix:
            return f"{prefix}_{unique_id}_{name[:30]}.{ext}"
        return f"{unique_id}_{name[:30]}.{ext}"
    else:
        if prefix:
            return f"{prefix}_{unique_id}_{safe_name[:30]}"
        return f"{unique_id}_{safe_name[:30]}"


def private_upload_path(instance, filename: str) -> str:
    """
    Generate upload path for private documents.
    
    Format: {model_name}/{year}/{month}/{uuid}.ext
    
    Usage in model:
        document = models.FileField(upload_to=private_upload_path, storage=private_storage)
    """
    # Get model name
    model_name = instance.__class__.__name__.lower()
    
    # Get date components
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    
    # Generate safe unique filename
    safe_name = generate_unique_filename(filename)
    
    return f"{model_name}/{year}/{month}/{safe_name}"


def public_upload_path(instance, filename: str) -> str:
    """
    Generate upload path for public media.
    
    Format: {model_name}/{year}/{uuid}.ext
    """
    model_name = instance.__class__.__name__.lower()
    now = datetime.now()
    year = now.strftime('%Y')
    safe_name = generate_unique_filename(filename)
    
    return f"{model_name}/{year}/{safe_name}"


def is_path_safe(path: str) -> bool:
    """
    Check if a file path is safe (no traversal attempts).
    """
    # Normalize path
    normalized = os.path.normpath(path)
    
    # Check for traversal patterns
    dangerous_patterns = [
        '..',
        '//',
        '\\\\',
        '\x00',  # Null byte
    ]
    
    for pattern in dangerous_patterns:
        if pattern in path:
            return False
    
    # Check if path tries to escape
    if normalized.startswith('/') or normalized.startswith('\\'):
        return False
    
    if ':' in normalized:  # Windows drive letters
        return False
    
    return True


def validate_path(path: str) -> str:
    """
    Validate and sanitize a file path.
    Raises ValueError if path is unsafe.
    """
    if not is_path_safe(path):
        raise ValueError("Invalid file path detected")
    
    return os.path.normpath(path)
