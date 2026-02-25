import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Role

User = get_user_model()
username = 'partner_demo'
password = 'partner_password123'

if not User.objects.filter(username=username).exists():
    user = User.objects.create_user(username=username, email='partner@demo.com', password=password)
    partner_role, _ = Role.objects.get_or_create(name='Partner')
    user.role = partner_role
    user.save()
    
    # Create Partner Profile
    # Import locally to avoid circular import issues if unique
    from users.models import PartnerProfile
    if not hasattr(user, 'partner_profile'):
        PartnerProfile.objects.create(user=user, is_approved=True)

    print(f"Created partner user: {username} / {password}")
else:
    u = User.objects.get(username=username)
    u.set_password(password)
    u.save()
    print(f"Reset password for existing user: {username} / {password}")
