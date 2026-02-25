import os
import django
from django.conf import settings
from django.test import RequestFactory

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from places.models import Place, Category
from places.filters import PlaceFilter
from django.db.models import Q

def verify_filters():
    print("Verifying Filters...")
    
    # Setup Data
    cat1 = Category.objects.create(name="FilterCat1")
    cat2 = Category.objects.create(name="FilterCat2")
    
    p1 = Place.objects.create(name="Place1 Family Paved", category=cat1, classification='family', road_condition='paved', is_active=True, avg_rating=4.0)
    p2 = Place.objects.create(name="Place2 General Offroad", category=cat1, classification='general', road_condition='offroad', is_active=True, avg_rating=3.0)
    p3 = Place.objects.create(name="Place3 Family Paved", category=cat2, classification='family', road_condition='paved', is_active=True, avg_rating=5.0)
    
    qs = Place.objects.all()
    
    # Test 1: Category Filter
    f = PlaceFilter(data={'category': cat1.id}, queryset=qs)
    if set(f.qs) == {p1, p2}:
        print("PASS: Category Filter")
    else:
        print(f"FAIL: Category Filter. Expected: {[p1, p2]}, Got: {list(f.qs)}")

    # Test 2: Classification Filter
    f = PlaceFilter(data={'classification': 'family'}, queryset=qs)
    if set(f.qs) == {p1, p3}:
        print("PASS: Classification Filter")
    else:
        print(f"FAIL: Classification Filter. Expected: {[p1, p3]}, Got: {list(f.qs)}")
        
    # Test 3: Road Condition Filter
    f = PlaceFilter(data={'road_condition': 'offroad'}, queryset=qs)
    if set(f.qs) == {p2}:
        print("PASS: Road Condition Filter")
    else:
        print(f"FAIL: Road Condition Filter. Expected: {[p2]}, Got: {list(f.qs)}")

    # Test 4: Combined Filter
    f = PlaceFilter(data={'category': cat1.id, 'classification': 'family'}, queryset=qs)
    if set(f.qs) == {p1}:
        print("PASS: Combined Filter")
    else:
        print(f"FAIL: Combined Filter. Expected: {[p1]}, Got: {list(f.qs)}")

    # Test 5: Search
    f = PlaceFilter(data={'search': 'General'}, queryset=qs)
    if set(f.qs) == {p2}:
        print("PASS: Search Filter")
    else:
         print(f"FAIL: Search Filter. Expected: {[p2]}, Got: {list(f.qs)}")
         
    # Cleanup
    p1.delete()
    p2.delete()
    p3.delete()
    cat1.delete()
    cat2.delete()
    print("Cleanup done.")

if __name__ == '__main__':
    verify_filters()
