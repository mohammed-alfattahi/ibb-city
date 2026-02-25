"""
File Validators for Secure Upload Handling
Provides strict validation for file uploads including:
- MIME type validation (not just extension)
- File size limits
- Extension allowlists
- MIME/extension mismatch detection
"""
import magic
import logging
from typing import List, Optional, Tuple
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class FileValidationError(ValidationError):
    """Custom exception for file validation failures."""
    pass


class FileValidator:
    """
    Base file validator with MIME type and extension checks.
    
    Usage:
        validator = FileValidator(
            allowed_extensions=['pdf', 'jpg'],
            allowed_mimes=['application/pdf', 'image/jpeg'],
            max_size_mb=10
        )
        validator.validate(uploaded_file)
    """
    
    def __init__(
        self,
        allowed_extensions: List[str],
        allowed_mimes: List[str],
        max_size_mb: float = 10,
        blocked_mimes: Optional[List[str]] = None
    ):
        self.allowed_extensions = [ext.lower().lstrip('.') for ext in allowed_extensions]
        self.allowed_mimes = [mime.lower() for mime in allowed_mimes]
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.blocked_mimes = [m.lower() for m in (blocked_mimes or [])]
    
    def validate(self, file: UploadedFile) -> None:
        """
        Validate uploaded file. Raises FileValidationError on failure.
        """
        self._validate_size(file)
        self._validate_extension(file)
        self._validate_mime_type(file)
        self._validate_mime_extension_match(file)
    
    def _validate_size(self, file: UploadedFile) -> None:
        """Check file size against limit."""
        if file.size > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            raise FileValidationError(
                _("File size exceeds maximum allowed (%(max)s MB)") % {'max': max_mb}
            )
    
    def _validate_extension(self, file: UploadedFile) -> None:
        """Check file extension against allowlist."""
        ext = self._get_extension(file.name)
        if ext not in self.allowed_extensions:
            raise FileValidationError(
                _("File extension '%(ext)s' is not allowed. Allowed: %(allowed)s") % {
                    'ext': ext,
                    'allowed': ', '.join(self.allowed_extensions)
                }
            )
    
    def _validate_mime_type(self, file: UploadedFile) -> None:
        """Check actual MIME type using python-magic."""
        mime_type = self._detect_mime_type(file)
        
        # Check blocked mimes first
        if mime_type in self.blocked_mimes:
            raise FileValidationError(
                _("File type '%(mime)s' is not allowed for security reasons.") % {'mime': mime_type}
            )
        
        # Check allowed mimes
        if mime_type not in self.allowed_mimes:
            raise FileValidationError(
                _("File content type '%(mime)s' is not allowed.") % {'mime': mime_type}
            )
    
    def _validate_mime_extension_match(self, file: UploadedFile) -> None:
        """Detect and reject MIME/extension mismatches (potential attacks)."""
        ext = self._get_extension(file.name)
        mime_type = self._detect_mime_type(file)
        
        # Map of extensions to expected MIME types
        ext_mime_map = {
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'png': ['image/png'],
            'gif': ['image/gif'],
            'webp': ['image/webp'],
            'pdf': ['application/pdf'],
            'doc': ['application/msword'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        }
        
        expected_mimes = ext_mime_map.get(ext, [])
        if expected_mimes and mime_type not in expected_mimes:
            logger.warning(
                f"MIME/extension mismatch detected: ext={ext}, mime={mime_type}, file={file.name}"
            )
            raise FileValidationError(
                _("File content does not match its extension. Possible security issue detected.")
            )
    
    def _get_extension(self, filename: str) -> str:
        """Extract and normalize file extension."""
        if '.' not in filename:
            return ''
        return filename.rsplit('.', 1)[-1].lower()
    
    def _detect_mime_type(self, file: UploadedFile) -> str:
        """Detect actual MIME type from file content."""
        file.seek(0)
        header = file.read(2048)
        file.seek(0)
        
        try:
            mime_type = magic.from_buffer(header, mime=True)
            return mime_type.lower()
        except Exception as e:
            logger.error(f"MIME detection failed: {e}")
            raise FileValidationError(_("Could not determine file type."))


class ImageValidator(FileValidator):
    """
    Specialized validator for image uploads.
    Blocks SVG and other potentially dangerous image formats.
    """
    
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']
    ALLOWED_MIMES = [
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/gif',
    ]
    BLOCKED_MIMES = [
        'image/svg+xml',  # Can contain scripts
        'image/x-icon',   # Can be used for attacks
    ]
    MAX_SIZE_MB = 5
    
    def __init__(self, max_size_mb: float = None):
        super().__init__(
            allowed_extensions=self.ALLOWED_EXTENSIONS,
            allowed_mimes=self.ALLOWED_MIMES,
            max_size_mb=max_size_mb or self.MAX_SIZE_MB,
            blocked_mimes=self.BLOCKED_MIMES
        )


class DocumentValidator(FileValidator):
    """
    Validator for document uploads (PDFs, images of documents).
    Used for National ID, licenses, commercial registry.
    """
    
    ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']
    ALLOWED_MIMES = [
        'application/pdf',
        'image/jpeg',
        'image/png',
    ]
    MAX_SIZE_MB = 10
    
    def __init__(self, max_size_mb: float = None):
        super().__init__(
            allowed_extensions=self.ALLOWED_EXTENSIONS,
            allowed_mimes=self.ALLOWED_MIMES,
            max_size_mb=max_size_mb or self.MAX_SIZE_MB
        )


class CoverImageValidator(ImageValidator):
    """Validator for establishment cover images (larger size allowed)."""
    MAX_SIZE_MB = 10


class ProfileImageValidator(ImageValidator):
    """Validator for user profile images (smaller size)."""
    MAX_SIZE_MB = 2


# Convenience validation functions
def validate_image(file: UploadedFile) -> None:
    """Validate an image upload."""
    ImageValidator().validate(file)


def validate_document(file: UploadedFile) -> None:
    """Validate a document upload."""
    DocumentValidator().validate(file)


def validate_cover_image(file: UploadedFile) -> None:
    """Validate a cover image upload."""
    CoverImageValidator().validate(file)
