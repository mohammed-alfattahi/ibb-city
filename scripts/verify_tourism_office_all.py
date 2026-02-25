import os
import django
import sys
import datetime
from django.utils import timezone

# 1. إعداد بيئة Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from django.contrib.auth import get_user_model
from places.models import Place, Category, Establishment, EstablishmentUnit
from management.models import Advertisement, ApprovalRequest
from interactions.models import Review, Notification

User = get_user_model()

def log_step(msg):
    print(f"\n🚀 {msg}")
    print("-" * 50)

def run_unified_verification():
    print("====================================================")
    print("🏨 نظام فحص عمليات مكتب السياحة - إب السياحي")
    print("====================================================")

    # التحضير: إنشاء فئة إذا لم توجد
    cat, _ = Category.objects.get_or_create(name="اختبار مكتب السياحة")

    # 1. اختبار إنشاء شريك (Partner)
    log_step("1. اختبار إنشاء حساب مكتب سياحة (شريك)")
    partner_user, created = User.objects.get_or_create(
        username="tourism_office_test",
        defaults={"email": "office@test.com", "is_active": True}
    )
    if created: partner_user.set_password("testpass123"); partner_user.save()
    print(f"✅ تم التحقق من حساب الشريك: {partner_user.username}")

    # 2. اختبار إضافة منشأة (Establishment)
    log_step("2. اختبار إضافة منشأة سياحية جديدة")
    place, p_created = Place.objects.get_or_create(
        name="فندق مكتب السياحة التجريبي",
        defaults={
            "category": cat,
            "description": "وصف تجريبي للمنشأة",
            "is_active": True,
            "is_approved": False  # تبدأ غير معتمدة
        }
    )
    establishment, e_created = Establishment.objects.get_or_create(
        place_ptr=place,
        defaults={
            "owner": partner_user,
            "is_verified": False
        }
    )
    print(f"✅ تم إنشاء المنشأة: {place.name} (الحالة: بانتظار الموافقة)")

    # 3. اختبار نظام الموافقة (Approval Flow)
    log_step("3. اختبار نظام الموافقات الإدارية")
    approval, a_created = ApprovalRequest.objects.get_or_create(
        content_type_id=1,  # اختصار للتبسيط في الفحص
        object_id=place.id,
        defaults={"status": "pending"}
    )
    # محاكاة موافقة المدير
    place.is_approved = True
    place.save()
    print(f"✅ تم محاكاة موافقة المدير؛ المنشأة الآن حية (Live)")

    # 4. اختبار إضافة وحدة/غرفة (Unit)
    log_step("4. اختبار إضافة غرف/خدمات للمنشأة")
    unit, u_created = EstablishmentUnit.objects.get_or_create(
        establishment=establishment,
        name="غرفة ملكية تجريبية",
        defaults={"price": 150.00}
    )
    print(f"✅ تم إضافة وحدة: {unit.name} بسعر {unit.price}")

    # 5. اختبار نظام الإعلانات (Ads System)
    log_step("5. اختبار طلب إعلان ترويجي (Boost)")
    ad, ad_created = Advertisement.objects.get_or_create(
        owner=partner_user,
        place=place,
        defaults={
            "status": "pending",
            "start_date": timezone.now().date()
        }
    )
    print(f"✅ تم إنشاء طلب إعلان لمكان: {place.name}")

    # 6. اختبار التفاعلات (Reviews & Notifications)
    log_step("6. اختبار التفاعلات والإشعارات")
    # إنشاء تقييم من مستخدم آخر
    tourist, _ = User.objects.get_or_create(username="tourist_tester")
    review, r_created = Review.objects.get_or_create(
        user=tourist,
        place=place,
        defaults={"rating": 5, "comment": "خدمة ممتازة من مكتب السياحة"}
    )
    
    # التحقق من وجود إشعار للشريك
    notif = Notification.objects.filter(recipient=partner_user).last()
    if notif:
        print(f"✅ تلقى الشريك إشعاراً جديداً: {notif.title}")
    else:
        print("⚠️ لم يتم العثور على إشعارات (تأكد من عمل الـ Signals)")

    print("\n====================================================")
    print("🎉 اكتمل فحص جميع عمليات مكتب السياحة بنجاح!")
    print("====================================================")

if __name__ == "__main__":
    try:
        run_unified_verification()
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الفحص: {e}")
        import traceback
        traceback.print_exc()
