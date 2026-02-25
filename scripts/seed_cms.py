import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.dev')
django.setup()

from cms.models import UIZone, UIComponent, ZoneComponent

def seed_cms():
    # 1. Create Zone
    zone, _ = UIZone.objects.get_or_create(
        slug='sidebar_right',
        defaults={'name': 'الشريط الجانبي الأيمن'}
    )
    
    # 2. Create Components
    comp_weather, _ = UIComponent.objects.get_or_create(
        slug='weather_widget',
        defaults={
            'name': 'ودجة الطقس',
            'template_path': 'components/molecules/weather_widget.html'
        }
    )
    
    comp_partners, _ = UIComponent.objects.get_or_create(
        slug='partners_widget',
        defaults={
            'name': 'ودجة الشركاء',
            'template_path': 'components/molecules/partners_widget.html'
        }
    )
    
    comp_footer, _ = UIComponent.objects.get_or_create(
        slug='mini_footer',
        defaults={
            'name': 'تذييل صغير',
            'template_path': 'components/molecules/mini_footer.html'
        }
    )
    
    # 3. Link them (if not exists)
    if not ZoneComponent.objects.filter(zone=zone).exists():
        ZoneComponent.objects.create(zone=zone, component=comp_weather, order=1)
        ZoneComponent.objects.create(zone=zone, component=comp_partners, order=2)
        ZoneComponent.objects.create(zone=zone, component=comp_footer, order=3)
        print("CMS Seeded: Sidebar Right with 3 components.")
    else:
        print("CMS Sidebar already has components.")

if __name__ == '__main__':
    seed_cms()
