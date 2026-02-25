from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Role
from places.models import Place, Category
from interactions.models import Review

User = get_user_model()

class Command(BaseCommand):
    help = 'Cleans the database of dummy data (preserves Superusers)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Cleaning data...')
        
        # Delete generated data
        deleted_reviews, _ = Review.objects.all().delete()
        self.stdout.write(f'Deleted {deleted_reviews} reviews.')
        
        deleted_places, _ = Place.objects.all().delete()
        self.stdout.write(f'Deleted {deleted_places} places.')
        
        deleted_cats, _ = Category.objects.all().delete()
        self.stdout.write(f'Deleted {deleted_cats} categories.')
        
        # Delete non-superuser users
        deleted_users, _ = User.objects.exclude(is_superuser=True).delete()
        self.stdout.write(f'Deleted {deleted_users} users.')
        
        # Delete Roles (if valid to delete all)
        deleted_roles, _ = Role.objects.all().delete()
        self.stdout.write(f'Deleted {deleted_roles} roles.')

        self.stdout.write(self.style.SUCCESS('Successfully cleaned database!'))
