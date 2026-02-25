import os
import django
from django.utils import timezone
from datetime import timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.dev')
django.setup()

from events.models import Event
from django.contrib.auth import get_user_model

def create_demo_events():
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No superuser found. Please create one.")
        return

    now = timezone.now()

    events_data = [
        {
            'title': 'مهرجان إب السياحي الخامس',
            'description': 'أكبر تجمع سياحي في المحافظة يعرض التراث الشعبي والمنتجات المحلية مع عروض فنية مميزة.',
            'event_type': 'festival',
            'start_date': now + timedelta(days=5),
            'end_date': now + timedelta(days=10),
            'location_name': 'منتزه مشورة',
        },
        {
            'title': 'موسم الحصاد الزراعي',
            'description': 'انطلاق موسم حصاد الذرة والشعيم في ريف إب، فرصة لالتقاط الصور والاستمتاع بالطبيعة الخلابة.',
            'event_type': 'season',
            'start_date': now - timedelta(days=2), # Ongoing
            'end_date': now + timedelta(days=15),
            'location_name': 'وادي عنة',
        },
        {
            'title': 'معرض الصور الفوتوغرافية - إب الخضراء',
            'description': 'معرض يضم أجمل اللقطات التي وثقت جمال المحافظة بعدسات مصورين محليين.',
            'event_type': 'exhibition',
            'start_date': now + timedelta(days=20),
            'end_date': now + timedelta(days=25),
            'location_name': 'المركز الثقافي',
        },
    ]

    for data in events_data:
        event, created = Event.objects.get_or_create(
            title=data['title'],
            defaults={
                'description': data['description'],
                'event_type': data['event_type'],
                'start_date': data['start_date'],
                'end_date': data['end_date'],
                'location_name': data['location_name'],
                'created_by': admin_user,
                'slug': None # Will auto-generate
            }
        )
        if created:
            event.save() # To generate slug
            print(f"Created Event: {event.title}")
        else:
            print(f"Event exists: {event.title}")

if __name__ == '__main__':
    create_demo_events()
