"""
Protected Views for Serving Private Documents
Ensures only authorized users can access sensitive files.
"""
import os
import mimetypes
import logging
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

from .models import FileAuditLog
from .storage import validate_path

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class ServePrivateDocumentView(LoginRequiredMixin, View):
    """
    Serve private documents with permission checks.
    
    Access control:
    - Staff/Admin: Full access to all private documents
    - Document owner: Access to their own documents
    - Others: Access denied
    
    URL pattern: /private/<path:document_path>
    """
    
    def get(self, request, document_path):
        ip = get_client_ip(request)
        
        try:
            # Validate path (prevent traversal)
            safe_path = validate_path(document_path)
        except ValueError:
            logger.warning(f"Path traversal attempt: {document_path} by {request.user}")
            FileAuditLog.log_access_denied(
                user=request.user,
                file_path=document_path,
                ip=ip,
                notes="Path traversal attempt"
            )
            raise Http404("Document not found")
        
        # Build full path
        private_root = getattr(settings, 'PRIVATE_MEDIA_ROOT', 
                               os.path.join(settings.BASE_DIR, 'private_media'))
        full_path = os.path.join(private_root, safe_path)
        
        # Normalize and verify path is within private root
        full_path = os.path.normpath(full_path)
        if not full_path.startswith(os.path.normpath(private_root)):
            logger.warning(f"Path escape attempt: {document_path} by {request.user}")
            FileAuditLog.log_access_denied(
                user=request.user,
                file_path=document_path,
                ip=ip,
                notes="Path escape attempt"
            )
            raise Http404("Document not found")
        
        # Check file exists
        if not os.path.isfile(full_path):
            raise Http404("Document not found")
        
        # Permission check
        if not self._check_permission(request, safe_path):
            FileAuditLog.log_access_denied(
                user=request.user,
                file_path=document_path,
                ip=ip,
                notes="Permission denied"
            )
            return HttpResponseForbidden("You do not have permission to access this document.")
        
        # Log access
        FileAuditLog.log_download(
            user=request.user,
            file_path=document_path,
            ip=ip
        )
        
        # Serve file
        content_type, _ = mimetypes.guess_type(full_path)
        response = FileResponse(
            open(full_path, 'rb'),
            content_type=content_type or 'application/octet-stream'
        )
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(safe_path)}"'
        
        return response
    
    def _check_permission(self, request, document_path: str) -> bool:
        """
        Check if user has permission to access document.
        
        Rules:
        - Staff/Admin: Always allowed
        - Owner: Can access their own documents
        """
        user = request.user
        
        # Staff/Admin access
        if user.is_staff or user.is_superuser:
            return True
        
        # Check ownership based on path pattern
        # Pattern: partnerprofile/{year}/{month}/{filename}
        # We need to check if this path belongs to the user's profile
        path_parts = document_path.split('/')
        
        if len(path_parts) >= 1:
            model_name = path_parts[0].lower()
            
            # Partner profile documents
            if model_name == 'partnerprofile':
                from users.models import PartnerProfile
                try:
                    profile = PartnerProfile.objects.get(user=user)
                    # Check if any of the profile's documents match this path
                    for field in ['national_id_image', 'commercial_registry', 'license_image']:
                        field_value = getattr(profile, field, None)
                        if field_value and document_path in str(field_value):
                            return True
                except PartnerProfile.DoesNotExist:
                    pass
        
        return False


class ServePartnerDocumentView(LoginRequiredMixin, View):
    """
    Specialized view for serving partner documents.
    Partners can view their own documents.
    Staff can view any partner's documents.
    """
    
    def get(self, request, profile_id, document_type):
        from users.models import PartnerProfile
        
        ip = get_client_ip(request)
        
        # Get profile
        try:
            profile = PartnerProfile.objects.get(pk=profile_id)
        except PartnerProfile.DoesNotExist:
            raise Http404("Profile not found")
        
        # Permission check
        is_owner = profile.user == request.user
        is_staff = request.user.is_staff or request.user.is_superuser
        
        if not (is_owner or is_staff):
            FileAuditLog.log_access_denied(
                user=request.user,
                file_path=f"partner/{profile_id}/{document_type}",
                ip=ip,
                notes="Permission denied"
            )
            return HttpResponseForbidden("Access denied")
        
        # Get document field
        document_fields = {
            'national_id': 'national_id_image',
            'commercial_registry': 'commercial_registry',
            'license': 'license_image',
        }
        
        field_name = document_fields.get(document_type)
        if not field_name:
            raise Http404("Invalid document type")
        
        document = getattr(profile, field_name, None)
        if not document:
            raise Http404("Document not found")
        
        # Log and serve
        FileAuditLog.log_download(
            user=request.user,
            file_path=document.name,
            ip=ip,
            entity_type='PartnerProfile',
            entity_id=str(profile_id)
        )
        
        return FileResponse(
            document.open('rb'),
            content_type=mimetypes.guess_type(document.name)[0] or 'application/octet-stream'
        )
