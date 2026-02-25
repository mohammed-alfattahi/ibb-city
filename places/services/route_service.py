from django.utils import timezone
from management.models import RouteLog, VehicleProfile

class RouteService:
    """
    Middleware Service for Smart Routing.
    Analyzes safety before handing off to Maps.
    """

    @staticmethod
    def analyze_route(user, place):
        """
        Analyze the route from User -> Place.
        Returns: (status, warnings_list)
        Status: SAFE, WARNING, DANGER
        """
        warnings = []
        status = 'SAFE'

        # 1. Get User Profile
        try:
            profile = user.vehicle_profile
            vehicle_type = profile.vehicle_type
        except Exception:
            vehicle_type = 'SEDAN' # Default assumption

        # 2. Night Check
        hour = timezone.now().hour
        is_night = hour < 5 or hour > 18
        
        # Hypothetical Place Attributes (would be in Place model)
        # place.is_mountainous = True/False
        # place.road_type = 'PAVED' / 'OFFROAD'
        
        # Check 1: Night + Mountain
        # Assuming we add is_mountainous to Place or infer from category/location
        # For now, simplistic Category check
        is_mountain = place.category.name in ['Jibal', 'Mountain', 'Nature']
        
        if is_night and is_mountain:
            warnings.append("القيادة في الطرق الجبلية ليلاً قد تكون خطرة. يرجى توخي الحذر الشديد.")
            status = 'WARNING'

        # Check 2: Offroad + Sedan
        # Use place.road_condition if available
        is_offroad = getattr(place, 'road_condition', '') in ['offroad', 'difficult', 'unpaved']
        
        if is_offroad and vehicle_type == 'SEDAN':
            warnings.append("الطريق لهذا المعلم قد يكون وعراً ولا يناسب السيارات الصغيرة.")
            status = 'DANGER'

        # Check 3: Weather Integration (Mock)
        # if WeatherService.is_raining(place.location):
        #    warnings.append("يوجد تحذير أمطار في المنطقة. تجنب الأودية.")
        #    status = 'DANGER'

        # Log Request
        RouteLog.objects.create(
            user=user,
            destination_place=place,
            safety_status=status,
            warnings=warnings
        )

        return status, warnings
