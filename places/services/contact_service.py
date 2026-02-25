"""
Contact Service
خدمة إدارة جهات الاتصال

Handles CRUD operations with audit logging and office notifications.
"""
from django.utils import timezone
from places.models import EstablishmentContact
from management.models import AuditLog


class ContactService:
    """
    Service for managing establishment contacts.
    All operations are logged and office is notified.
    """
    
    @staticmethod
    def add_contact(user, establishment, data, ip=None):
        """
        Add a new contact to establishment.
        
        Args:
            user: The user adding the contact
            establishment: The establishment
            data: Dict with contact fields
            ip: Client IP address
            
        Returns:
            (contact, success, message)
        """
        try:
            # Get next display order
            max_order = EstablishmentContact.objects.filter(
                establishment=establishment
            ).order_by('-display_order').values_list('display_order', flat=True).first()
            
            next_order = (max_order or 0) + 1
            
            contact = EstablishmentContact(
                establishment=establishment,
                type=data.get('type'),
                carrier=data.get('carrier'),
                label=data.get('label', ''),
                value=data.get('value'),
                is_primary=data.get('is_primary', False),
                is_visible=data.get('is_visible', True),
                display_order=data.get('display_order', next_order),
                created_by=user,
            )
            contact.save()
            
            # Audit log
            try:
                AuditLog.objects.create(
                    user=user,
                    action='contact_added',
                    table_name='EstablishmentContact',
                    record_id=str(contact.pk),
                    diff={
                        'establishment': establishment.name,
                        'type': contact.type,
                        'value': contact.value,
                    },
                )
            except Exception:
                pass
            
            # Notify office
            try:
                from interactions.notifications.admin import AdminNotifications
                AdminNotifications.notify_establishment_contact_updated(
                    establishment, user, 'added', contact
                )
            except Exception:
                pass
            
            return contact, True, 'تم إضافة جهة الاتصال بنجاح'
            
        except Exception as e:
            return None, False, str(e)
    
    @staticmethod
    def update_contact(user, contact, data, ip=None):
        """
        Update an existing contact.
        
        Args:
            user: The user making the update
            contact: The EstablishmentContact instance
            data: Dict with updated fields
            ip: Client IP address
            
        Returns:
            (contact, success, message)
        """
        try:
            # Store before state
            before = {
                'type': contact.type,
                'carrier': contact.carrier,
                'label': contact.label,
                'value': contact.value,
                'is_primary': contact.is_primary,
                'is_visible': contact.is_visible,
            }
            
            # Update fields
            for field in ['type', 'carrier', 'label', 'value', 'is_primary', 'is_visible']:
                if field in data:
                    setattr(contact, field, data[field])
            
            contact.save()
            
            # After state
            after = {
                'type': contact.type,
                'carrier': contact.carrier,
                'label': contact.label,
                'value': contact.value,
                'is_primary': contact.is_primary,
                'is_visible': contact.is_visible,
            }
            
            # Audit log
            try:
                AuditLog.objects.create(
                    user=user,
                    action='contact_updated',
                    table_name='EstablishmentContact',
                    record_id=str(contact.pk),
                    diff={'before': before, 'after': after},
                )
            except Exception:
                pass
            
            # Notify office
            try:
                from interactions.notifications.admin import AdminNotifications
                AdminNotifications.notify_establishment_contact_updated(
                    contact.establishment, user, 'updated', contact
                )
            except Exception:
                pass
            
            return contact, True, 'تم تحديث جهة الاتصال بنجاح'
            
        except Exception as e:
            return None, False, str(e)
    
    @staticmethod
    def delete_contact(user, contact, ip=None):
        """
        Delete a contact.
        
        Args:
            user: The user deleting
            contact: The EstablishmentContact instance
            ip: Client IP address
            
        Returns:
            (success, message)
        """
        try:
            establishment = contact.establishment
            contact_data = {
                'type': contact.type,
                'value': contact.value,
                'establishment': establishment.name,
            }
            contact_id = str(contact.pk)
            
            contact.delete()
            
            # Audit log
            try:
                AuditLog.objects.create(
                    user=user,
                    action='contact_deleted',
                    table_name='EstablishmentContact',
                    record_id=contact_id,
                    diff=contact_data,
                )
            except Exception:
                pass
            
            # Notify office
            try:
                from interactions.notifications.admin import AdminNotifications
                AdminNotifications.notify_establishment_contact_updated(
                    establishment, user, 'deleted', None
                )
            except Exception:
                pass
            
            return True, 'تم حذف جهة الاتصال بنجاح'
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def reorder_contacts(user, establishment, ordered_ids, ip=None):
        """
        Reorder contacts by updating display_order.
        
        Args:
            user: The user reordering
            establishment: The establishment
            ordered_ids: List of contact UUIDs in desired order
            ip: Client IP address
            
        Returns:
            (success, message)
        """
        try:
            for index, contact_id in enumerate(ordered_ids):
                EstablishmentContact.objects.filter(
                    pk=contact_id,
                    establishment=establishment
                ).update(display_order=index)
            
            # Audit log
            try:
                AuditLog.objects.create(
                    user=user,
                    action='contacts_reordered',
                    table_name='Establishment',
                    record_id=str(establishment.pk),
                    diff={'new_order': ordered_ids},
                )
            except Exception:
                pass
            
            return True, 'تم إعادة ترتيب جهات الاتصال'
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def toggle_visibility(user, contact, ip=None):
        """Toggle contact visibility."""
        contact.is_visible = not contact.is_visible
        contact.save(update_fields=['is_visible', 'updated_at'])
        
        # Audit log
        try:
            AuditLog.objects.create(
                user=user,
                action='contact_visibility_toggled',
                table_name='EstablishmentContact',
                record_id=str(contact.pk),
                diff={'is_visible': contact.is_visible},
            )
        except Exception:
            pass
        
        return contact.is_visible
    
    @staticmethod
    def get_visible_contacts(establishment):
        """Get visible contacts for tourist display, grouped by type."""
        contacts = EstablishmentContact.objects.filter(
            establishment=establishment,
            is_visible=True
        ).order_by('display_order')
        
        # Group by type category
        grouped = {
            'phones': [],
            'messaging': [],
            'social': [],
            'links': [],
        }
        
        for contact in contacts:
            if contact.type == 'phone':
                grouped['phones'].append(contact)
            elif contact.type in ['whatsapp', 'telegram']:
                grouped['messaging'].append(contact)
            elif contact.type in ['facebook', 'instagram', 'tiktok', 'snapchat', 'youtube']:
                grouped['social'].append(contact)
            else:
                grouped['links'].append(contact)
        
        return grouped
