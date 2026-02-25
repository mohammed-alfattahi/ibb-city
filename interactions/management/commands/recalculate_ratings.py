from django.core.management.base import BaseCommand
from places.models import Place
from interactions.services.rating_service import RatingService

class Command(BaseCommand):
    help = 'Recalculates rating statistics (avg, count, distribution) for all places.'

    def handle(self, *args, **options):
        places = Place.objects.all()
        count = places.count()
        self.stdout.write(f"Found {count} places. Starting recalculation...")
        
        for i, place in enumerate(places, 1):
            RatingService.update_place_statistics(place)
            if i % 100 == 0:
                self.stdout.write(f"Processed {i}/{count} places...")
                
        self.stdout.write(self.style.SUCCESS(f"Successfully recalculated statistics for {count} places."))
