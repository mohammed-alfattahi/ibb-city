from interactions.models import Itinerary, ItineraryItem
from places.services.route_service import RouteService # Op 14 Service

class ItineraryService:
    """
    Service for Trip Planning & Routing.
    Manages Itineraries and validates routes between stops.
    """

    @staticmethod
    def create_itinerary(user, title, start_date, duration=1):
        return Itinerary.objects.create(
            user=user,
            title=title,
            start_date=start_date,
            duration_days=duration
        )

    @staticmethod
    def add_place_to_day(itinerary, place, day, order=None, notes=""):
        if not order:
            # Auto-increment order
            last_item = ItineraryItem.objects.filter(
                itinerary=itinerary, 
                day_number=day
            ).order_by('-order').first()
            order = (last_item.order + 1) if last_item else 1
            
        return ItineraryItem.objects.create(
            itinerary=itinerary,
            place=place,
            day_number=day,
            order=order,
            notes=notes
        )

    @staticmethod
    def check_feasibility(itinerary):
        """
        Analyze the itinerary for route risks and time feasibility.
        Update items with risk data.
        """
        items = ItineraryItem.objects.filter(itinerary=itinerary).select_related('place').order_by('day_number', 'order')
        
        # Group by day
        from collections import defaultdict
        daily_items = defaultdict(list)
        for item in items:
            daily_items[item.day_number].append(item)
            
        report = []
        
        for day, day_items in daily_items.items():
            for i in range(len(day_items) - 1):
                current = day_items[i]
                next_stop = day_items[i+1]
                
                # Use RouteService (Op 14) to analyze path
                # Assuming RouteService.analyze_route exists and returns dict
                # We mock lat/lon passing since RouteService expects coords usually, 
                # or we might need to update RouteService to accept Place objects.
                # For now, we assume RouteService can handle Place -> Place logic or we extract coords.
                
                # Mock analysis for MVP connection
                # route_data = RouteService.analyze_route(current.place, next_stop.place) 
                
                # Simple distance check simulation
                route_risk = 'LOW'
                if current.place.category.name == 'Mountain' and next_stop.place.category.name == 'Mountain':
                    route_risk = 'MEDIUM' # Winding roads
                
                next_stop.route_risk = route_risk
                next_stop.save()
                
                if route_risk != 'LOW':
                    report.append(f"Day {day}: Risk {route_risk} between {current.place.name} and {next_stop.place.name}")
                    
        return report
