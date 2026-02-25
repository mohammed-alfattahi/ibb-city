from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from places.models import Establishment, Category, SpecialOffer

User = get_user_model()

def run_verification():
    print("--- Verifying Special Offers System ---")
    
    # 1. Setup Data
    # Use existing user or create
    user, _ = User.objects.get_or_create(username='test_partner_offer', defaults={'email': 'partner_offer@test.com'})
    category, _ = Category.objects.get_or_create(name='Test Category')
    
    establishment, _ = Establishment.objects.get_or_create(
        owner=user,
        name='Test Place for Offers',
        defaults={
            'category': category,
            'approval_status': 'approved',
            'is_active': True
        }
    )
    print(f"✅ Setup Establishment: {establishment.name}")

    # 2. Create Active Offer
    now = timezone.now()
    active_offer = SpecialOffer.objects.create(
        establishment=establishment,
        title="Active Deal",
        old_price=Decimal("100.00"),
        new_price=Decimal("80.00"),
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=5),
        is_active=True
    )
    print(f"✅ Created Active Offer: {active_offer.title}")

    # 3. Create Expired Offer
    expired_offer = SpecialOffer.objects.create(
        establishment=establishment,
        title="Expired Deal",
        old_price=Decimal("50.00"),
        new_price=Decimal("40.00"),
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=5),
        is_active=True
    )
    print(f"✅ Created Expired Offer: {expired_offer.title}")
    
    # 4. Create Inactive Offer
    inactive_offer = SpecialOffer.objects.create(
        establishment=establishment,
        title="Draft Deal",
        old_price=Decimal("200.00"),
        new_price=Decimal("150.00"),
        start_date=now,
        end_date=now + timedelta(days=5),
        is_active=False
    )
    print(f"✅ Created Inactive Offer: {inactive_offer.title}")

    # 5. Verify Query Logic (Same as in View)
    active_offers_qs = SpecialOffer.objects.filter(
        establishment=establishment,
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    )
    
    count = active_offers_qs.count()
    if count == 1 and active_offers_qs.first().pk == active_offer.pk:
        print("✅ Query Verification Passed: Only 'Active Deal' returned.")
    else:
        print(f"❌ Query Verification FAILED. Expected 1, got {count}.")
        for o in active_offers_qs:
            print(f"   - Found: {o.title}")

    # 6. Verify Discount Calculation
    if active_offer.discount_percentage == 20:
        print("✅ Discount Calculation Passed: 20%")
    else:
        print(f"❌ Discount Calculation FAILED. Expected 20, got {active_offer.discount_percentage}")

    # Cleanup
    active_offer.delete()
    expired_offer.delete()
    inactive_offer.delete()
    # establishment.delete() # Keep establishment for manual verification if needed
    print("✅ Cleanup complete.")

if __name__ == "__main__":
    run_verification()
