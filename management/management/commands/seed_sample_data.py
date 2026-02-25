"""
Management command to seed the database with sample data.
Creates categories, places, users, reviews, and events for testing.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write("🌱 Starting database seeding...")
        
        self.create_categories()
        self.create_users()
        self.create_places()
        self.create_reviews()
        self.create_events()
        
        self.stdout.write(self.style.SUCCESS("✅ Database seeding completed!"))

    def create_categories(self):
        from places.models import Category
        
        categories_data = [
            {'name': 'طبيعة', 'name_en': 'Nature', 'icon': 'fas fa-tree'},
            {'name': 'معالم', 'name_en': 'Landmarks', 'icon': 'fas fa-landmark'},
            {'name': 'فنادق', 'name_en': 'Hotels', 'icon': 'fas fa-hotel'},
            {'name': 'مطاعم', 'name_en': 'Restaurants', 'icon': 'fas fa-utensils'},
            {'name': 'متنزهات', 'name_en': 'Parks', 'icon': 'fas fa-leaf'},
            {'name': 'شلالات', 'name_en': 'Waterfalls', 'icon': 'fas fa-water'},
            {'name': 'آثار', 'name_en': 'Heritage', 'icon': 'fas fa-monument'},
            {'name': 'أسواق', 'name_en': 'Markets', 'icon': 'fas fa-store'},
        ]
        
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data.get('icon', 'fas fa-map-marker-alt')}
            )
            if created:
                self.stdout.write(f"   Created category: {cat.name}")

    def create_users(self):
        # Create test tourists
        for i in range(1, 4):
            user, created = User.objects.get_or_create(
                username=f'tourist{i}',
                defaults={
                    'email': f'tourist{i}@example.com',
                    'full_name': f'سائح تجريبي {i}',
                    'phone_number': f'77700000{i}',
                }
            )
            if created:
                user.set_password('test123')
                user.save()
                self.stdout.write(f"   Created tourist: {user.username}")
        
        # Create test partner
        from users.models import PartnerProfile, Role
        partner_role, _ = Role.objects.get_or_create(name='Partner')
        
        partner, created = User.objects.get_or_create(
            username='partner_demo',
            defaults={
                'email': 'partner@example.com',
                'full_name': 'شريك تجريبي',
                'phone_number': '777111222',
                'role': partner_role,
                'account_status': 'active',
            }
        )
        if created:
            partner.set_password('test123')
            partner.save()
            PartnerProfile.objects.create(
                user=partner,
                status='approved',
                is_approved=True,
                commercial_reg_no='CR-DEMO-001'
            )
            self.stdout.write(f"   Created partner: {partner.username}")

    def create_places(self):
        from places.models import Place, Category, Establishment
        
        # Sample places data
        places_data = [
            {
                'name': 'جبل صبر',
                'description': 'أعلى قمة في محافظة إب، يوفر إطلالات خلابة على المدينة والوديان المحيطة. يعتبر من أجمل المناطق الطبيعية في اليمن.',
                'category': 'طبيعة',
                'latitude': 13.9721,
                'longitude': 44.1792,
            },
            {
                'name': 'سد سحار',
                'description': 'سد تاريخي يعود للقرن السادس الميلادي، يعكس براعة الهندسة اليمنية القديمة في إدارة المياه.',
                'category': 'آثار',
                'latitude': 13.9621,
                'longitude': 44.1692,
            },
            {
                'name': 'مسجد الجند',
                'description': 'من أقدم المساجد في اليمن، بناه الصحابي معاذ بن جبل رضي الله عنه في عهد الرسول ﷺ.',
                'category': 'معالم',
                'latitude': 13.8567,
                'longitude': 44.1234,
            },
            {
                'name': 'وادي بنا',
                'description': 'وادٍ أخضر خلاب يضم مزارع البن والقات والفواكه، ويشتهر بمناظره الطبيعية الساحرة.',
                'category': 'طبيعة',
                'latitude': 13.9421,
                'longitude': 44.1892,
            },
            {
                'name': 'شلالات الدملوة',
                'description': 'شلالات طبيعية رائعة تتدفق من الجبال، وجهة مثالية للاستجمام والتصوير.',
                'category': 'شلالات',
                'latitude': 13.9321,
                'longitude': 44.2092,
            },
            {
                'name': 'قلعة جبلة',
                'description': 'قلعة تاريخية تطل على مدينة جبلة، شاهدة على حضارة الدولة الصليحية.',
                'category': 'معالم',
                'latitude': 13.9167,
                'longitude': 44.0833,
            },
            {
                'name': 'متنزه إب الأخضر',
                'description': 'متنزه عائلي جميل في قلب المدينة، يوفر مساحات خضراء وألعاب للأطفال.',
                'category': 'متنزهات',
                'latitude': 13.9671,
                'longitude': 44.1742,
            },
            {
                'name': 'سوق إب القديم',
                'description': 'سوق شعبي تقليدي يعرض الحرف اليدوية والمنتجات المحلية والتوابل اليمنية الأصيلة.',
                'category': 'أسواق',
                'latitude': 13.9681,
                'longitude': 44.1752,
            },
        ]
        
        for place_data in places_data:
            try:
                category = Category.objects.get(name=place_data['category'])
            except Category.DoesNotExist:
                continue
            
            place, created = Place.objects.get_or_create(
                name=place_data['name'],
                defaults={
                    'description': place_data['description'],
                    'category': category,
                    'latitude': place_data['latitude'],
                    'longitude': place_data['longitude'],
                    'is_active': True,
                    'operational_status': 'active',
                    'avg_rating': round(random.uniform(3.5, 5.0), 1),
                    'view_count': random.randint(100, 1000),
                }
            )
            if created:
                self.stdout.write(f"   Created place: {place.name}")

    def create_reviews(self):
        from places.models import Place
        from interactions.models import Review
        
        users = User.objects.filter(username__startswith='tourist')
        places = Place.objects.all()[:5]
        
        sample_comments = [
            "مكان رائع جداً، أنصح بزيارته!",
            "تجربة ممتازة، سأعود مرة أخرى بالتأكيد.",
            "جميل ولكن يحتاج بعض التحسينات.",
            "من أجمل الأماكن التي زرتها في إب.",
            "استمتعت كثيراً، الطبيعة خلابة!",
        ]
        
        for place in places:
            for user in users:
                review, created = Review.objects.get_or_create(
                    user=user,
                    place=place,
                    defaults={
                        'rating': random.randint(3, 5),
                        'comment': random.choice(sample_comments),
                    }
                )
                if created:
                    self.stdout.write(f"   Created review for {place.name} by {user.username}")

    def create_events(self):
        from events.models import Event, Season
        
        now = timezone.now()
        
        # Create season
        season, created = Season.objects.get_or_create(
            name='موسم الربيع',
            defaults={
                'description': 'موسم الربيع في إب - أجمل أوقات السنة',
                'start_date': now.date(),
                'end_date': (now + timedelta(days=90)).date(),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f"   Created season: {season.name}")
        
        # Create events
        events_data = [
            {
                'title': 'مهرجان البن اليمني',
                'description': 'مهرجان سنوي للاحتفاء بالبن اليمني الأصيل وتراث زراعته.',
                'event_type': 'festival',
                'location': 'ساحة المدينة',
            },
            {
                'title': 'جولة تراثية في جبلة',
                'description': 'جولة إرشادية لاستكشاف معالم مدينة جبلة التاريخية.',
                'event_type': 'tour',
                'location': 'مدينة جبلة',
            },
            {
                'title': 'رحلة تسلق جبل صبر',
                'description': 'رحلة مغامرة لتسلق أعلى قمة في المحافظة.',
                'event_type': 'adventure',
                'location': 'جبل صبر',
            },
        ]
        
        for i, event_data in enumerate(events_data):
            start = now + timedelta(days=(i+1)*7)
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                defaults={
                    'description': event_data['description'],
                    'event_type': event_data.get('event_type', 'other'),
                    'location': event_data['location'],
                    'start_datetime': start,
                    'end_datetime': start + timedelta(hours=5),
                    'season': season,
                    'is_featured': i == 0,
                }
            )
            if created:
                self.stdout.write(f"   Created event: {event.title}")
