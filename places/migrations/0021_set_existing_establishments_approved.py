"""
Data migration to set existing active establishments to 'approved'.

This ensures existing establishments remain visible to the public after
the approval workflow is introduced.
"""
from django.db import migrations


def set_existing_active_to_approved(apps, schema_editor):
    """Set all existing active establishments to approved status."""
    Establishment = apps.get_model('places', 'Establishment')
    
    # Set active establishments to approved
    Establishment.objects.filter(is_active=True).update(approval_status='approved')
    
    # Log the count
    count = Establishment.objects.filter(approval_status='approved').count()
    print(f"  -> Set {count} existing active establishments to 'approved' status")


def reverse_approved_to_pending(apps, schema_editor):
    """Reverse: set approved back to pending."""
    Establishment = apps.get_model('places', 'Establishment')
    Establishment.objects.filter(approval_status='approved').update(approval_status='pending')


class Migration(migrations.Migration):
    
    dependencies = [
        ('places', '0020_add_establishment_approval_fields'),
    ]
    
    operations = [
        migrations.RunPython(
            set_existing_active_to_approved,
            reverse_approved_to_pending
        ),
    ]
