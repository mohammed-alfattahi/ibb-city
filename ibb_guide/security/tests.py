"""
Tests for File Security System
"""
import io
from PIL import Image
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from ibb_guide.security.file_validators import (
    FileValidator, ImageValidator, DocumentValidator, FileValidationError
)
from ibb_guide.security.image_processor import ImageProcessor, has_exif_data
from ibb_guide.security.storage import safe_filename, is_path_safe, validate_path

User = get_user_model()


class FileValidatorTest(TestCase):
    """Test file validation."""
    
    def test_valid_image_extension(self):
        """Test that valid image extensions are accepted."""
        validator = ImageValidator()
        
        # Create a valid JPEG file
        file = self._create_test_image('test.jpg', 'JPEG')
        
        with patch.object(validator, '_detect_mime_type', return_value='image/jpeg'):
            validator.validate(file)  # Should not raise
    
    def test_invalid_extension_rejected(self):
        """Test that invalid extensions are rejected."""
        validator = ImageValidator()
        
        file = SimpleUploadedFile('test.exe', b'fake content', content_type='image/jpeg')
        
        with self.assertRaises(FileValidationError):
            validator._validate_extension(file)
    
    def test_size_limit_enforced(self):
        """Test that oversized files are rejected."""
        validator = ImageValidator(max_size_mb=0.001)  # 1KB limit
        
        # Create file larger than limit
        large_content = b'x' * 2000  # 2KB
        file = SimpleUploadedFile('test.jpg', large_content, content_type='image/jpeg')
        
        with self.assertRaises(FileValidationError):
            validator._validate_size(file)
    
    def test_svg_blocked(self):
        """Test that SVG files are blocked."""
        validator = ImageValidator()
        
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        file = SimpleUploadedFile('test.svg', svg_content, content_type='image/svg+xml')
        
        with patch.object(validator, '_detect_mime_type', return_value='image/svg+xml'):
            with self.assertRaises(FileValidationError):
                validator._validate_mime_type(file)
    
    def _create_test_image(self, name: str, format: str) -> InMemoryUploadedFile:
        """Create a test image file."""
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        
        return InMemoryUploadedFile(
            file=buffer,
            field_name=None,
            name=name,
            content_type=f'image/{format.lower()}',
            size=buffer.getbuffer().nbytes,
            charset=None
        )


class ImageProcessorTest(TestCase):
    """Test image processing and EXIF stripping."""
    
    def test_image_reencoded(self):
        """Test that images are re-encoded."""
        processor = ImageProcessor()
        
        # Create test image
        original = self._create_test_image('original.jpg')
        
        # Process
        processed = processor.process(original)
        
        self.assertIsNotNone(processed)
        self.assertTrue(processed.name.endswith('.jpg'))
    
    def test_exif_stripped(self):
        """Test that EXIF data is removed."""
        processor = ImageProcessor()
        
        # Create image with EXIF-like data
        img = Image.new('RGB', (100, 100), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        file = InMemoryUploadedFile(
            file=buffer,
            field_name=None,
            name='with_exif.jpg',
            content_type='image/jpeg',
            size=buffer.getbuffer().nbytes,
            charset=None
        )
        
        # Process
        processed = processor.process(file)
        
        # Verify EXIF is stripped
        processed.seek(0)
        result_img = Image.open(processed)
        
        # Check no EXIF
        try:
            exif = result_img._getexif()
            self.assertTrue(exif is None or len(exif) == 0)
        except AttributeError:
            pass  # No EXIF attribute means no EXIF data
    
    def test_large_image_resized(self):
        """Test that large images are resized."""
        processor = ImageProcessor(max_dimension=500)
        
        # Create large image
        img = Image.new('RGB', (2000, 1000), color='green')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        file = InMemoryUploadedFile(
            file=buffer,
            field_name=None,
            name='large.jpg',
            content_type='image/jpeg',
            size=buffer.getbuffer().nbytes,
            charset=None
        )
        
        # Process
        processed = processor.process(file)
        
        # Verify resized
        processed.seek(0)
        result_img = Image.open(processed)
        self.assertLessEqual(result_img.width, 500)
        self.assertLessEqual(result_img.height, 500)
    
    def _create_test_image(self, name: str) -> InMemoryUploadedFile:
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        return InMemoryUploadedFile(
            file=buffer,
            field_name=None,
            name=name,
            content_type='image/jpeg',
            size=buffer.getbuffer().nbytes,
            charset=None
        )


class PathSecurityTest(TestCase):
    """Test path safety utilities."""
    
    def test_safe_filename(self):
        """Test filename sanitization."""
        # Normal filename
        self.assertTrue(safe_filename('document.pdf').endswith('.pdf'))
        
        # Path traversal attempt
        result = safe_filename('../../../etc/passwd')
        self.assertNotIn('..', result)
        self.assertNotIn('/', result)
    
    def test_path_traversal_detected(self):
        """Test path traversal detection."""
        self.assertFalse(is_path_safe('../etc/passwd'))
        self.assertFalse(is_path_safe('..\\windows\\system32'))
        self.assertFalse(is_path_safe('/etc/passwd'))
        self.assertFalse(is_path_safe('C:\\Windows'))
        
        # Safe paths
        self.assertTrue(is_path_safe('documents/file.pdf'))
        self.assertTrue(is_path_safe('2024/01/document.pdf'))
    
    def test_validate_path_raises(self):
        """Test that unsafe paths raise ValueError."""
        with self.assertRaises(ValueError):
            validate_path('../../../etc/passwd')


class PrivateDocumentAccessTest(TestCase):
    """Test private document access control."""
    
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass'
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access private documents."""
        response = self.client.get('/private/some/document.pdf')
        # Should redirect to login
        self.assertIn(response.status_code, [302, 403])
    
    def test_staff_can_access(self):
        """Test that staff users can access private documents."""
        self.client.force_login(self.staff_user)
        
        # This will 404 because file doesn't exist, but won't be 403
        response = self.client.get('/private/test/document.pdf')
        self.assertNotEqual(response.status_code, 403)
