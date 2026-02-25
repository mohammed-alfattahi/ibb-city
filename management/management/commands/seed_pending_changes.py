from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User, PartnerProfile
from places.models import Establishment
from management.models.pending_changes import PendingChange
import random

class Command(BaseCommand):
    help = 'Seeds trial data for Admin UI testing including Pending Changes and Partnerships'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Admin Trial Data...')
        
        # Select base users
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found. Please create a staff user first.'))
            return

        # 1. Clear Existing Trial Data (Optional, but helps keep it clean)
        # PendingChange.objects.all().delete()
        
        establishments = list(Establishment.objects.all()[:5])
        if not establishments:
            self.stdout.write(self.style.ERROR('No establishments found. Please seed establishments first.'))
            return

        # --- SEED PENDING CHANGES ---
        pending_data = [
            ('name', 'مطعم حضرموت القديم', 'مطعم حضرموت الملكي الجديد'),
            ('description', 'مطعم يقدم المأكولات الشعبية', 'مطعم سياحي فاخر يقدم أرقى المأكولات الشعبية اليمنية بتنسيق عصري.'),
            ('name', 'فندق إب جراند', 'إب جراند أوتيل & سبا'),
        ]
        
        for i, (field, old, new) in enumerate(pending_data):
            est = establishments[i % len(establishments)]
            PendingChange.objects.get_or_create(
                establishment=est,
                field_name=field,
                old_value=old,
                new_value=new,
                requested_by=admin_user,
                status='pending'
            )
            self.stdout.write(self.style.SUCCESS(f'Checked/Created pending change: {est.name}'))

        # Seed Recent Activity for Timeline
        for i in range(5):
            est = establishments[random.randint(0, len(establishments)-1)]
            status = 'approved' if i % 2 == 0 else 'rejected'
            PendingChange.objects.create(
                establishment=est,
                field_name=random.choice(['name', 'description']),
                old_value='Old Value',
                new_value='New Value Approved' if status == 'approved' else 'New Value Rejected',
                requested_by=admin_user,
                status=status,
                reviewed_by=admin_user,
                reviewed_at=timezone.now() - timezone.timedelta(hours=random.randint(1, 100)),
                review_note='Test Review Note' if status == 'rejected' else ''
            )

        # --- SEED PARTNERSHIP REQUESTS ---
        # Create some dummy users for partners
        for i in range(1, 6):
            username = f'trial_partner_{i}'
            user, created = User.objects.get_or_create(
                username=username,
                email=f'{username}@example.com'
            )
            if created:
                user.set_password('password123')
                user.save()
            
            # Create Partner Profile
            profile, _ = PartnerProfile.objects.get_or_create(user=user)
            
            # Rotate statuses
            if i <= 2:
                profile.status = 'pending'
                profile.organization_name = f'نشاط تجاري معلق {i}'
                profile.submitted_at = timezone.now() - timezone.timedelta(days=i)
                self.stdout.write(self.style.SUCCESS(f'Created Pending Partner: {username}'))
            elif i == 3:
                profile.status = 'approved'
                profile.is_approved = True
                profile.organization_name = f'شريك معتمد سابقا'
                profile.reviewed_at = timezone.now() - timezone.timedelta(days=10)
                profile.reviewed_by = admin_user
            else:
                profile.status = 'rejected'
                profile.organization_name = f'طلب مرفوض للتجربة'
                profile.rejection_reason = 'المستندات غير مكتملة'
                profile.reviewed_at = timezone.now() - timezone.timedelta(days=5)
                profile.reviewed_by = admin_user
            
            profile.save()

        self.stdout.write(self.style.SUCCESS('Successfully seeded all admin trial data.'))
