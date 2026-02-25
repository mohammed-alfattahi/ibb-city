import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from users.models import Role, PartnerProfile
from places.models import (
    Category, Place, Establishment, Landmark, ServicePoint, EstablishmentUnit, PlaceMedia
)
from interactions.models import Review

User = get_user_model()
fake = Faker()

# Ibb Coordinates
IBB_LAT = 13.97
IBB_LNG = 44.18

class Command(BaseCommand):
    help = 'Seeds the database with dummy data for IbbGuide'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')
        
        with transaction.atomic():
            self.clean_db()
            self.create_roles()
            self.create_users()
            self.create_categories()
            self.create_places()
            self.create_interactions()

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))

    def clean_db(self):
        self.stdout.write('Cleaning old data...')
        Review.objects.all().delete()
        Place.objects.all().delete()
        Category.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        Role.objects.all().delete()

    def create_roles(self):
        self.role_admin = Role.objects.create(name='Admin', description='System Admin')
        self.role_partner = Role.objects.create(name='Partner', description='Business Partner')
        self.role_tourist = Role.objects.create(name='Tourist', description='Regular User')

    def create_users(self):
        self.stdout.write('Creating users...')
        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@admin.com', 'admin', role=self.role_admin)
        
        # Partners
        self.partners = []
        for _ in range(5):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password',
                role=self.role_partner,
                full_name=fake.name(),
                phone_number=fake.phone_number()
            )
            PartnerProfile.objects.create(user=user, commercial_reg_no=fake.bothify(text='###-###'), is_approved=True)
            self.partners.append(user)

        # Tourists
        self.tourists = []
        for _ in range(20):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password',
                role=self.role_tourist,
                full_name=fake.name(),
                phone_number=fake.phone_number()
            )
            self.tourists.append(user)

    def create_categories(self):
        self.stdout.write('Creating categories...')
        self.cat_accommodation = Category.objects.create(name='Accommodation')
        Category.objects.create(name='Hotels', parent=self.cat_accommodation)
        Category.objects.create(name='Resorts', parent=self.cat_accommodation)

        self.cat_nature = Category.objects.create(name='Nature')
        Category.objects.create(name='Waterfalls', parent=self.cat_nature)
        Category.objects.create(name='Mountains', parent=self.cat_nature)
        Category.objects.create(name='Valleys', parent=self.cat_nature)

        self.cat_services = Category.objects.create(name='Services')
        Category.objects.create(name='Hospitals', parent=self.cat_services)
        Category.objects.create(name='ATMs', parent=self.cat_services)

    def get_random_coords(self):
        # Random offset roughly within city limits
        lat = IBB_LAT + random.uniform(-0.02, 0.02)
        lng = IBB_LNG + random.uniform(-0.02, 0.02)
        return lat, lng

    def create_places(self):
        self.stdout.write('Creating places...')
        
        # Establishments (Hotels)
        hotel_cat = Category.objects.get(name='Hotels')
        for i in range(5):
            owner = random.choice(self.partners)
            lat, lng = self.get_random_coords()
            est = Establishment.objects.create(
                name=f"{fake.company()} Hotel",
                description=fake.text(),
                latitude=lat,
                longitude=lng,
                category=hotel_cat,
                owner=owner,
                avg_rating=random.uniform(3.0, 5.0),
                contact_info={'phone': fake.phone_number()},
                working_hours={'open': '08:00', 'close': '22:00'}
            )
            self.add_media(est)
            # Units
            for _ in range(random.randint(2, 5)):
                EstablishmentUnit.objects.create(
                    establishment=est,
                    name=f"Room {random.randint(100, 999)}",
                    unit_type='Room',
                    price=random.uniform(50.0, 200.0),
                    description=fake.sentence()
                )

        # Landmarks
        nature_cats = Category.objects.filter(parent=self.cat_nature)
        for i in range(5):
            lat, lng = self.get_random_coords()
            cat = random.choice(nature_cats)
            landmark = Landmark.objects.create(
                name=f"{fake.city()} {cat.name}",
                description=fake.text(),
                latitude=lat,
                longitude=lng,
                category=cat,
                avg_rating=random.uniform(4.0, 5.0),
                landmark_type='Natural',
                best_visit_time='Summer'
            )
            self.add_media(landmark)

        # Service Points
        service_cats = Category.objects.filter(parent=self.cat_services)
        for i in range(5):
            lat, lng = self.get_random_coords()
            cat = random.choice(service_cats)
            sp = ServicePoint.objects.create(
                name=f"Ibb {cat.name} {i+1}",
                description=fake.sentence(),
                latitude=lat,
                longitude=lng,
                category=cat,
                service_type=cat.name,
                is_24_hours=random.choice([True, False])
            )
            # No media usually for ATM but maybe for Hospital

    def add_media(self, place):
        for i in range(random.randint(1, 3)):
            PlaceMedia.objects.create(
                place=place,
                media_url=f"https://picsum.photos/seed/{random.randint(1, 1000)}/800/600",
                is_cover=(i==0)
            )
            if i == 0: # Mock setup for cover image string URL if not using file field
                pass

    def create_interactions(self):
        self.stdout.write('Creating reviews...')
        places = Place.objects.all()
        for place in places:
            # Random 3-5 reviews
            reviewers = random.sample(self.tourists, k=random.randint(3, 5))
            for user in reviewers:
                Review.objects.create(
                    user=user,
                    place=place,
                    rating=random.randint(1, 5),
                    comment=fake.sentence()
                )
