
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibb_guide.settings.dev")
django.setup()

from management.models import PublicEmergencyContact, SafetyGuideline
from places.models import Category, Place

def populate_data():
    print("--- Populating Functional Data ---")

    # 1. Emergency Contacts
    print("Populating Emergency Contacts...")
    contacts = [
        {'title': 'شرطة إب', 'number': '199', 'icon': 'fas fa-taxi', 'color': 'primary', 'desc': 'للبلاغات الأمنية', 'is_primary': True},
        {'title': 'الإسعاف', 'number': '191', 'icon': 'fas fa-ambulance', 'color': 'danger', 'desc': 'للحالات الطبية الطارئة', 'is_primary': True},
        {'title': 'الدفاع المدني', 'number': '191', 'icon': 'fas fa-fire-extinguisher', 'color': 'warning', 'desc': 'للحرائق والكوارث', 'is_primary': True},
        {'title': 'مستشفى الثورة', 'number': '04-401000', 'icon': 'fas fa-hospital', 'color': 'success', 'desc': 'مستشفى حكومي', 'is_hospital': True},
        {'title': 'مستشفى جبلة', 'number': '04-412222', 'icon': 'fas fa-hospital', 'color': 'info', 'desc': 'مستشفى عام', 'is_hospital': True},
    ]

    for c in contacts:
        PublicEmergencyContact.objects.get_or_create(
            title=c['title'],
            defaults={
                'number': c['number'],
                'icon': c['icon'],
                'color': c['color'],
                'description': c['desc'],
                'is_primary_card': c.get('is_primary', False),
                'is_hospital': c.get('is_hospital', False),
                'is_active': True
            }
        )

    # 2. Safety Guidelines
    print("Populating Safety Guidelines...")
    guidelines = [
        {'title': 'القيادة في الجبال', 'desc': 'تجنب السرعة في المنعطفات الجبلية واستخدم الغيارات الثقيلة عند النزول.', 'icon': 'fas fa-car', 'color': 'warning'},
        {'title': 'أوقات الأمطار', 'desc': 'تجنب مجاري السيول والوديان أثناء مواسم الأمطار الغزيرة.', 'icon': 'fas fa-cloud-showers-heavy', 'color': 'info'},
        {'title': 'احترام العادات', 'desc': 'يرجى الالتزام بالملابس المحتشمة واحترام خصوصية السكان المحليين.', 'icon': 'fas fa-users', 'color': 'success'},
    ]
    for g in guidelines:
        SafetyGuideline.objects.get_or_create(
            title=g['title'],
            defaults={
                'description': g['desc'],
                'icon': g['icon'],
                'color': g['color'],
                'is_active': True
            }
        )

    # 3. Parks Category & Places
    print("Checking Parks Category...")
    # Model only has 'name' field
    park_cat, created = Category.objects.get_or_create(name='Park')
    if created:
        print(" - Created 'Park' category")
    
    # Assign some places to Park if none exist
    # Find places that look like parks
    parks_count = Place.objects.filter(category__name__in=['Park', 'Garden', 'منتزه', 'حديقة']).count()
    if parks_count == 0:
        print("No parks found. Assigning 'Park' category to suitable places...")
        potential_parks = Place.objects.filter(name__icontains='حديقة') | Place.objects.filter(name__icontains='منتزه') | Place.objects.filter(name__icontains='مشلال')
        for p in potential_parks:
            p.category = park_cat
            p.save()
            print(f" - Assigned {p.name} to Park category")
            
    print("--- Population Complete ---")

if __name__ == "__main__":
    populate_data()
