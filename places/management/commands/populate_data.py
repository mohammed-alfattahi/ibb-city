from django.core.management.base import BaseCommand
from places.models import Place, Category, Landmark, Establishment, ServicePoint, PlaceMedia
from interactions.models import Review
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with realistic default data for Ibb Tourist Guide'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Create Admin User if not exists
        admin_user, created = User.objects.get_or_create(username='admin', email='admin@ibb.com')
        if created:
            admin_user.set_password('admin123')
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()

        # Create Categories
        cats = {
            'attraction': 'معالم سياحية',
            'hotel': 'فنادق واستراحات',
            'park': 'منتزهات',
            'restaurant': 'مطاعم',
            'service': 'خدمات عامة'
        }
        
        categories = {}
        for key, name in cats.items():
            cat, _ = Category.objects.get_or_create(name=name)
            categories[key] = cat

        # 1. Landmarks
        landmarks_data = [
            {
                'name': 'شلال المشنة',
                'desc': 'من أجمل شلالات مدينة إب، يقع في منطقة المشنة ويمتاز بتدفقه الغزير طوال موسم الأمطار.',
                'addr': 'المشنة، إب',
                'rating': 4.8
            },
            {
                'name': 'جبل ربي',
                'desc': 'إطلالة بانورامية ساحرة على مدينة إب القديمة والحديثة. مكان مفضل للتنزه وقت الغروب.',
                'addr': 'جبل ربي، إب',
                'rating': 4.5
            },
            {
                'name': 'وادي عنة',
                'desc': 'وادي أخضر يكسوه الغطاء النباتي الكثيف وتجري فيه المياه، يعتبر وجهة مثالية للنزهات العائلية.',
                'addr': 'العدين، إب',
                'rating': 4.9
            },
            {
                'name': 'حصن حب',
                'desc': 'حصن تاريخي قديم يقع على قمة جبل شاهق، يروي تاريخ المنطقة العريق.',
                'addr': 'بعدان، إب',
                'rating': 4.3
            }
        ]

        for data in landmarks_data:
            l, created = Landmark.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['desc'],
                    'category': categories['attraction'],
                    'address_text': data['addr'],
                    'avg_rating': data['rating'],
                    'latitude': 13.9667 + random.uniform(-0.05, 0.05),
                    'longitude': 44.1833 + random.uniform(-0.05, 0.05)
                }
            )
            if created:
                self.stdout.write(f"Created Landmark: {l.name}")
                # Add fake review
                Review.objects.create(
                    user=admin_user,
                    place=l,
                    rating=5,
                    comment='مكان رائع جداً ويستحق الزيارة!'
                )

        # 2. Hotels (Establishments)
        hotels_data = [
            {
                'name': 'فندق تاج إب',
                'desc': 'فندق سياحي فاخر يطل على المدينة، يوفر خدمات راقية وغرف مريحة.',
                'rating': 4.2
            },
            {
                'name': 'منتجع إب جاردن',
                'desc': 'منتجع سياحي متكامل يضم شاليهات ومسابح وحدائق خضراء واسعة.',
                'rating': 4.7
            }
        ]

        for data in hotels_data:
            h, created = Establishment.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['desc'],
                    'category': categories['hotel'],
                    'owner': admin_user,
                    'avg_rating': data['rating'],
                    'address_text': 'شارع تعز، إب',
                    'latitude': 13.9700,
                    'longitude': 44.1900
                }
            )
            if created:
                self.stdout.write(f"Created Hotel: {h.name}")

        self.stdout.write(self.style.SUCCESS('Database populated successfully with realistic Ibb data!'))
