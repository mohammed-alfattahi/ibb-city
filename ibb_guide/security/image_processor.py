"""
Image Processing for Secure Uploads
Provides:
- Image re-encoding to strip malicious content
- EXIF metadata removal
- Format standardization
"""
import io
import logging
from typing import Optional, Tuple
from PIL import Image, ExifTags
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Secure image processor that re-encodes images to strip metadata
    and potential malicious content.
    
    Usage:
        processor = ImageProcessor()
        safe_file = processor.process(uploaded_file)
    """
    
    # Output format mapping
    FORMAT_MAP = {
        'image/jpeg': ('JPEG', 'jpg', 'image/jpeg'),
        'image/png': ('PNG', 'png', 'image/png'),
        'image/webp': ('WEBP', 'webp', 'image/webp'),
        'image/gif': ('GIF', 'gif', 'image/gif'),
    }
    
    DEFAULT_QUALITY = 85
    MAX_DIMENSION = 4096  # Max width/height
    
    def __init__(self, quality: int = None, max_dimension: int = None):
        self.quality = quality or self.DEFAULT_QUALITY
        self.max_dimension = max_dimension or self.MAX_DIMENSION
    
    def process(self, file: UploadedFile) -> InMemoryUploadedFile:
        """
        Process and re-encode an image file.
        
        - Strips all EXIF metadata
        - Re-encodes to remove potential malicious content
        - Resizes if exceeds max dimensions
        
        Returns a new safe file object.
        """
        try:
            # Open image
            file.seek(0)
            image = Image.open(file)
            
            # Determine output format
            original_format = image.format or 'JPEG'
            mime_type = f"image/{original_format.lower()}"
            pil_format, extension, content_type = self.FORMAT_MAP.get(
                mime_type, ('JPEG', 'jpg', 'image/jpeg')
            )
            
            # Convert RGBA to RGB for JPEG
            if pil_format == 'JPEG' and image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Strip EXIF data
            image = self._strip_exif(image)
            
            # Resize if too large
            image = self._resize_if_needed(image)
            
            # Re-encode to buffer
            buffer = io.BytesIO()
            save_kwargs = {'format': pil_format}
            
            if pil_format in ('JPEG', 'WEBP'):
                save_kwargs['quality'] = self.quality
            if pil_format == 'PNG':
                save_kwargs['optimize'] = True
            
            image.save(buffer, **save_kwargs)
            buffer.seek(0)
            
            # Create new filename
            original_name = getattr(file, 'name', 'image')
            base_name = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
            new_name = f"{base_name}.{extension}"
            
            # Create new uploaded file
            processed_file = InMemoryUploadedFile(
                file=buffer,
                field_name=None,
                name=new_name,
                content_type=content_type,
                size=buffer.getbuffer().nbytes,
                charset=None
            )
            
            logger.info(f"Image processed: {file.name} -> {new_name}, size: {processed_file.size}")
            return processed_file
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise ValueError(f"Failed to process image: {str(e)}")
    
    def _strip_exif(self, image: Image.Image) -> Image.Image:
        """
        Remove all EXIF metadata from image.
        Creates a new image without metadata.
        """
        # Get orientation before stripping (to fix rotated photos)
        orientation = None
        try:
            exif = image._getexif()
            if exif:
                for tag, value in exif.items():
                    if ExifTags.TAGS.get(tag) == 'Orientation':
                        orientation = value
                        break
        except (AttributeError, KeyError, IndexError):
            pass
        
        # Create new image without EXIF
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        
        # Fix orientation if needed
        if orientation:
            image_without_exif = self._fix_orientation(image_without_exif, orientation)
        
        return image_without_exif
    
    def _fix_orientation(self, image: Image.Image, orientation: int) -> Image.Image:
        """Apply correct rotation based on EXIF orientation tag."""
        if orientation == 2:
            return image.transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            return image.rotate(180)
        elif orientation == 4:
            return image.transpose(Image.FLIP_TOP_BOTTOM)
        elif orientation == 5:
            return image.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 6:
            return image.rotate(-90, expand=True)
        elif orientation == 7:
            return image.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 8:
            return image.rotate(90, expand=True)
        return image
    
    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """Resize image if it exceeds maximum dimensions."""
        width, height = image.size
        
        if width <= self.max_dimension and height <= self.max_dimension:
            return image
        
        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = self.max_dimension
            new_height = int(height * (self.max_dimension / width))
        else:
            new_height = self.max_dimension
            new_width = int(width * (self.max_dimension / height))
        
        logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.LANCZOS)


def process_uploaded_image(file: UploadedFile) -> InMemoryUploadedFile:
    """Convenience function to process an uploaded image."""
    return ImageProcessor().process(file)


def has_exif_data(file: UploadedFile) -> bool:
    """Check if an image file contains EXIF data."""
    try:
        file.seek(0)
        image = Image.open(file)
        exif = image._getexif()
        file.seek(0)
        return exif is not None and len(exif) > 0
    except Exception:
        return False
