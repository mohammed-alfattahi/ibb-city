# 📚 دليل عضو الفريق - مشروع دليل إب السياحي

> **هذا الملف يحتوي على كل المعلومات التي يحتاجها عضو الفريق الجديد للبدء في العمل على المشروع**

---

## 📋 معلومات المشروع الأساسية

| البند | القيمة |
|-------|--------|
| **اسم المشروع** | دليل إب السياحي (Ibb Tourist Guide) |
| **نوع المشروع** | تطبيق سياحي متكامل |
| **الهدف** | ربط السياح بالمنشآت السياحية في مدينة إب |
| **المستخدمون** | السياح، الشركاء التجاريين، الإدارة |
| **البنية** | Django Backend + Flutter Mobile App |

---

## 🛠️ التقنيات المستخدمة

### Backend (هذا المشروع)
| التقنية | الإصدار | الغرض |
|---------|---------|-------|
| Python | 3.10+ | لغة البرمجة |
| Django | 4.2 | إطار العمل الخلفي |
| Django REST Framework | 3.16 | API للتطبيق |
| Simple JWT | 5.5 | المصادقة بالتوكن |
| PostgreSQL | - | قاعدة البيانات (Production) |
| SQLite | - | قاعدة البيانات (Development) |
| Firebase | - | إشعارات Push |
| OneSignal | - | إشعارات Push (بديل) |

### Frontend (Flutter - مشروع منفصل)
| التقنية | الغرض |
|---------|-------|
| Flutter/Dart | تطبيق الموبايل |
| GetX | إدارة الحالة |
| Dio | طلبات HTTP |

---

## 💻 إعداد بيئة التطوير

### الخطوة 1: استنساخ المشروع
```powershell
git clone <repository_url>
cd ibb
```

### الخطوة 2: إنشاء البيئة الافتراضية
```powershell
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### الخطوة 3: تثبيت الحزم
```powershell
pip install -r requirements.txt
```

### الخطوة 4: إعداد ملف البيئة
```powershell
# انسخ ملف المثال
copy .env.example .env

# عدل الملف وأضف القيم المطلوبة
```

**محتوى ملف `.env`:**
```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (للتطوير SQLite تلقائي)
# DB_NAME=ibb_db
# DB_USER=ibb_user
# DB_PASSWORD=your_password

# Email (اختياري للتطوير)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Push Notifications (اختياري)
ONESIGNAL_APP_ID=
ONESIGNAL_API_KEY=

# Google OAuth (اختياري)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### الخطوة 5: تشغيل الترحيلات
```powershell
python manage.py migrate
```

### الخطوة 6: إنشاء مستخدم مدير
```powershell
python manage.py createsuperuser
```

### الخطوة 7: تشغيل الخادم
```powershell
python manage.py runserver
```

### الخطوة 8: الوصول للتطبيق
| الرابط | الوصف |
|--------|-------|
| http://127.0.0.1:8000/ | الصفحة الرئيسية |
| http://127.0.0.1:8000/admin/ | لوحة Django Admin |
| http://127.0.0.1:8000/api/ | API الرئيسي |

---

## 📁 هيكل المشروع الكامل

```
ibb/
│
├── 📂 ibb_guide/              # ⚙️ الإعدادات الرئيسية للمشروع
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py           # ✅ الإعدادات المشتركة (INSTALLED_APPS, MIDDLEWARE)
│   │   ├── dev.py            # إعدادات التطوير (DEBUG=True)
│   │   └── prod.py           # إعدادات الإنتاج (DEBUG=False, Security)
│   ├── urls.py               # ✅ جميع روابط المشروع
│   ├── wsgi.py               # نقطة دخول Gunicorn
│   ├── asgi.py               # نقطة دخول ASGI
│   │
│   ├── 📂 domain/            # 🏛️ قواعد العمل (Business Rules)
│   │   ├── workflows.py      # سير عمل الموافقات (ApprovalWorkflow)
│   │   ├── policies.py       # سياسات الإشراف (ModerationPolicy)
│   │   └── boundaries.py     # صلاحيات الوصول (AccessBoundaryPolicy)
│   │
│   ├── 📂 infrastructure/    # 🔧 الخدمات الخارجية
│   │   ├── external_apis.py  # ✅ Weather API, Maps API, Push Notifications
│   │   └── repositories.py   # أنماط الوصول للبيانات
│   │
│   ├── validators.py         # التحقق من صحة البيانات
│   ├── mixins.py             # Mixins للصلاحيات
│   └── middleware.py         # Middleware مخصص
│
├── 📂 users/                  # 👤 تطبيق المستخدمين
│   ├── models.py             # ✅ User, PartnerProfile, UserLoginLog
│   ├── views.py              # واجهات تسجيل الدخول
│   ├── views_partner.py      # واجهات الشركاء
│   ├── serializers.py        # تحويل البيانات للAPI
│   ├── backends.py           # ✅ مصادقة بالإيميل أو اسم المستخدم
│   ├── forms.py              # نماذج الإدخال
│   ├── admin.py              # تسجيل في Django Admin
│   └── migrations/           # ترحيلات قاعدة البيانات
│
├── 📂 places/                 # 📍 تطبيق الأماكن
│   ├── 📂 models/
│   │   ├── __init__.py       # تصدير النماذج
│   │   ├── base.py           # ✅ Place, Category, Amenity, PlaceMedia
│   │   ├── establishments.py # ✅ Establishment, EstablishmentUnit
│   │   ├── landmarks.py      # معالم سياحية
│   │   └── routes.py         # مسارات سياحية
│   │
│   ├── 📂 services/          # ⚙️ خدمات الأعمال
│   │   ├── place_service.py          # البحث، الأماكن القريبة
│   │   ├── establishment_service.py  # إدارة المنشآت
│   │   └── recommendation_service.py # التوصيات
│   │
│   ├── views_public.py       # ✅ واجهات السياح (HomeView, PlaceDetailView)
│   ├── views_partner.py      # ✅ واجهات الشركاء (Dashboard, Add/Edit)
│   ├── views.py              # ViewSets للـ API
│   ├── serializers.py        # ✅ PlaceListSerializer, PlaceDetailSerializer
│   ├── filters.py            # فلاتر البحث
│   ├── forms.py              # نماذج الإدخال
│   ├── admin.py
│   └── migrations/
│
├── 📂 interactions/           # 💬 تطبيق التفاعلات
│   ├── 📂 models/
│   │   ├── reviews.py        # ✅ Review, ReviewReply, PlaceComment
│   │   ├── favorites.py      # ✅ Favorite
│   │   ├── reports.py        # Report (البلاغات)
│   │   └── notifications.py  # ✅ Notification
│   │
│   ├── 📂 services/
│   │   └── review_service.py # إدارة التقييمات
│   │
│   ├── firebase_service.py   # ✅ إرسال إشعارات Firebase
│   ├── onesignal_service.py  # إرسال إشعارات OneSignal
│   ├── signals.py            # ✅ المحفزات التلقائية (عند إضافة تقييم)
│   ├── views.py              # ViewSets للـ API
│   ├── views_public.py       # واجهات عامة
│   ├── serializers.py        # ✅ ReviewSerializer, NotificationSerializer
│   └── context_processors.py # إضافة عدد الإشعارات للقوالب
│
├── 📂 management/             # 🏢 تطبيق الإدارة
│   ├── 📂 models/
│   │   ├── ads.py            # Advertisement (الإعلانات)
│   │   ├── requests.py       # ApprovalRequest (طلبات الموافقة)
│   │   └── investments.py    # Investment (فرص الاستثمار)
│   │
│   ├── 📂 services/
│   │   ├── approval_service.py # إدارة الموافقات
│   │   └── ad_service.py       # إدارة الإعلانات
│   │
│   ├── views_admin.py        # ✅ واجهات المدير (الموافقات، التقارير)
│   ├── views_partner.py      # واجهات الشريك للإعلانات
│   ├── views_public.py       # الاستثمارات العامة
│   └── utils.py              # أدوات مساعدة
│
├── 📂 communities/            # 👥 تطبيق المجتمع
│   ├── models.py             # CommunityPost, PostComment
│   ├── views.py
│   └── urls.py
│
├── 📂 surveys/                # 📊 تطبيق الاستبيانات
│   └── ...
│
├── 📂 templates/              # 🎨 قوالب HTML
│   ├── base.html             # ✅ القالب الأساسي
│   ├── home.html             # الصفحة الرئيسية
│   ├── place_detail.html     # ✅ تفاصيل المكان
│   ├── place_list.html       # قائمة الأماكن
│   ├── 📂 users/             # قوالب المستخدمين
│   │   ├── login.html
│   │   └── profile.html
│   ├── 📂 partners/          # قوالب الشركاء
│   │   ├── dashboard.html
│   │   └── add_establishment.html
│   └── 📂 pages/             # صفحات ثابتة
│       ├── emergency.html
│       └── transport.html
│
├── 📂 static/                 # 📁 الملفات الثابتة
│   ├── 📂 css/
│   │   ├── modern_home.css   # ✅ تنسيق الصفحة الرئيسية
│   │   └── modern_place.css  # ✅ تنسيق صفحة المكان
│   ├── 📂 js/
│   └── 📂 images/
│
├── 📂 media/                  # 🖼️ الملفات المرفوعة (صور، ملفات)
│
├── 📂 .github/workflows/      # 🔄 CI/CD
│   └── ci.yml                # ✅ GitHub Actions للاختبارات
│
├── .env                       # ⚠️ متغيرات البيئة (لا ترفعه!)
├── .env.example               # مثال لملف البيئة
├── .gitignore
├── requirements.txt           # ✅ الحزم المطلوبة
├── manage.py                  # أداة إدارة Django
├── ARCHITECTURE.md            # ✅ توثيق البنية التقنية
├── DEPLOYMENT.md              # ✅ دليل النشر
├── OPS_MANUAL.md              # ✅ دليل التشغيل
└── README.md                  # ✅ نظرة عامة
```

---

## 🗄️ قاعدة البيانات

### النماذج الرئيسية

#### 1. المستخدمون (`users/models.py`)

```python
class User(AbstractUser):
    # حقول إضافية
    user_type = 'tourist' / 'partner' / 'admin'
    account_status = 'active' / 'pending' / 'rejected'
    profile_image = ImageField()
    phone = CharField()

class PartnerProfile(Model):
    user = OneToOneField(User)
    company_name = CharField()
    status = 'pending' / 'approved' / 'rejected'
    tax_number = CharField()
```

#### 2. الأماكن (`places/models/`)

```python
class Place(Model):
    name = CharField()
    description = TextField()
    category = ForeignKey(Category)
    latitude, longitude = DecimalField()
    cover_image = ImageField()
    avg_rating = DecimalField()
    operational_status = 'active' / 'closed' / 'maintenance'
    directorate = CharField()  # المديرية

class Establishment(Place):  # يرث من Place
    owner = ForeignKey(User)
    working_hours = JSONField()
    is_verified = BooleanField()
    is_open_status = BooleanField()
    license_image = ImageField()

class EstablishmentUnit(Model):  # غرف، خدمات
    establishment = ForeignKey(Establishment)
    name = CharField()
    price = DecimalField()
```

#### 3. التفاعلات (`interactions/models/`)

```python
class Review(Model):
    user = ForeignKey(User)
    place = ForeignKey(Place)
    rating = IntegerField(1-5)
    comment = TextField()
    status = 'approved' / 'hidden' / 'pending'
    
    class Meta:
        unique_together = ('user', 'place')  # تقييم واحد لكل مستخدم

class Favorite(Model):
    user = ForeignKey(User)
    place = ForeignKey(Place)

class Notification(Model):
    user = ForeignKey(User)
    notification_type = CharField()
    title = CharField()
    message = TextField()
    is_read = BooleanField()
```

---

## 🌐 نقاط API

### المصادقة (Authentication)

| Endpoint | Method | الوصف | Body |
|----------|--------|-------|------|
| `/api/token/` | POST | الحصول على توكن | `{email, password}` |
| `/api/token/refresh/` | POST | تجديد التوكن | `{refresh}` |
| `/api/register/` | POST | تسجيل جديد | `{username, email, password}` |

**مثال تسجيل الدخول:**
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "123456"}'
```

**الرد:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### الأماكن (Places)

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/places/` | GET | قائمة الأماكن |
| `/api/places/{id}/` | GET | تفاصيل مكان |

**مثال:**
```bash
curl -X GET http://127.0.0.1:8000/api/places/ \
  -H "Authorization: Bearer <access_token>"
```

**الرد:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "name": "فندق السلام",
      "cover_image": "/media/places/covers/hotel.jpg",
      "avg_rating": 4.5,
      "latitude": "13.9667",
      "longitude": "44.1833",
      "category_name": "فنادق",
      "place_type": "Establishment"
    }
  ]
}
```

### التقييمات (Reviews)

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/reviews/` | GET | قائمة التقييمات |
| `/api/reviews/` | POST | إضافة تقييم |

**إضافة تقييم:**
```bash
curl -X POST http://127.0.0.1:8000/api/reviews/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"place": 1, "rating": 5, "comment": "فندق رائع!"}'
```

### المفضلة (Favorites)

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/favorites/` | GET | قائمة المفضلة |
| `/api/favorites/` | POST | إضافة للمفضلة |
| `/api/favorites/{id}/` | DELETE | حذف من المفضلة |

---

## 🔧 الأوامر المهمة

### التطوير اليومي
```powershell
# تشغيل الخادم
python manage.py runserver

# تشغيل الخادم على IP محدد (للوصول من Flutter)
python manage.py runserver 0.0.0.0:8000

# إنشاء ترحيلات جديدة
python manage.py makemigrations

# تطبيق الترحيلات
python manage.py migrate

# إنشاء مستخدم مدير
python manage.py createsuperuser

# فتح Django Shell
python manage.py shell
```

### الاختبارات
```powershell
# تشغيل جميع الاختبارات
python manage.py test

# تشغيل اختبارات تطبيق معين
python manage.py test places

# تشغيل اختبار محدد
python manage.py test places.tests.test_views
```

### قاعدة البيانات
```powershell
# عرض الترحيلات
python manage.py showmigrations

# إعادة تعيين قاعدة البيانات (حذر!)
python manage.py flush

# تحميل بيانات تجريبية
python manage.py loaddata initial_data.json
```

### الإنتاج
```powershell
# جمع الملفات الثابتة
python manage.py collectstatic

# التحقق من الأخطاء
python manage.py check --deploy
```

---

## 🔐 نظام المصادقة

### أنواع المستخدمين

| النوع | الوصف | الصلاحيات |
|-------|-------|----------|
| **Tourist** | سائح عادي | عرض، تقييم، مفضلة |
| **Partner** | شريك تجاري | + إدارة منشآته |
| **Admin** | مدير النظام | كل الصلاحيات |

### تدفق المصادقة

```
1. Flutter يرسل POST /api/token/ {email, password}
2. Django يتحقق من البيانات
3. Django يُرجع {access_token, refresh_token}
4. Flutter يحفظ التوكن في Secure Storage
5. Flutter يرسل كل الطلبات مع Header:
   Authorization: Bearer <access_token>
6. عند انتهاء الصلاحية (30 دقيقة):
   POST /api/token/refresh/ {refresh}
7. Django يُرجع توكن جديد
```

---

## 🔔 نظام الإشعارات

### الإعداد
1. **Firebase**: ضع ملف `firebase-credentials.json` في الجذر
2. **OneSignal**: أضف `ONESIGNAL_APP_ID` في `.env`

### إرسال إشعار برمجياً
```python
from interactions.firebase_service import send_to_user

send_to_user(
    user_id=1,
    title="تقييم جديد",
    body="لديك تقييم جديد على فندق السلام",
    data={"type": "review", "place_id": 5}
)
```

---

## 📦 CI/CD

### GitHub Actions (`.github/workflows/ci.yml`)

```yaml
# يعمل تلقائياً عند:
# - Push إلى main أو develop
# - Pull Request إلى main أو develop

# الخطوات:
# 1. تثبيت Python 3.11/3.12
# 2. تثبيت الحزم
# 3. تشغيل الاختبارات
```

---

## 🚀 النشر (Deployment)

### البيئات

| البيئة | قاعدة البيانات | الإعدادات |
|--------|---------------|-----------|
| Development | SQLite | `ibb_guide.settings.dev` |
| Production | PostgreSQL | `ibb_guide.settings.prod` |

### متغيرات الإنتاج المطلوبة

```env
DEBUG=False
SECRET_KEY=<secure-random-key>
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgres://user:pass@host:5432/dbname
DJANGO_SETTINGS_MODULE=ibb_guide.settings.prod
```

### Render.com
المشروع مُعد للنشر على Render باستخدام `render.yaml`

---

## 📝 معايير كتابة الكود

### التسمية
- **Models**: PascalCase (`Establishment`)
- **Views**: PascalCase + View (`PlaceDetailView`)
- **Services**: snake_case (`review_service.py`)
- **Variables**: snake_case (`user_name`)

### الهيكل المفضل
```python
# views_public.py
class PlaceDetailView(DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # استخدم Service بدلاً من الاستعلام المباشر
        context['reviews'] = ReviewService.get_place_reviews(self.object)
        return context
```

### التعليقات
```python
"""
وصف الدالة بالعربية أو الإنجليزية

Args:
    user_id: معرف المستخدم
    
Returns:
    قائمة التقييمات
"""
```

---

## 🆘 المشاكل الشائعة وحلولها

| المشكلة | الحل |
|---------|------|
| `ModuleNotFoundError` | تأكد من تفعيل البيئة: `.venv\Scripts\activate` |
| `CORS Error` في Flutter | أضف `django-cors-headers` وأعده |
| قاعدة البيانات مقفلة | أغلق أي اتصالات مفتوحة |
| Static files لا تظهر | `python manage.py collectstatic` |
| التوكن منتهي | استخدم refresh token |

---

## 📞 التواصل والموارد

### الملفات المهمة للقراءة
1. `ARCHITECTURE.md` - البنية التقنية
2. `README.md` - نظرة عامة
3. `DEPLOYMENT.md` - دليل النشر
4. `OPS_MANUAL.md` - دليل التشغيل

### روابط مفيدة
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)

---

## ✅ قائمة التحقق للبدء

- [ ] استنساخ المشروع
- [ ] إنشاء البيئة الافتراضية
- [ ] تثبيت الحزم (`pip install -r requirements.txt`)
- [ ] إنشاء ملف `.env`
- [ ] تشغيل الترحيلات (`python manage.py migrate`)
- [ ] إنشاء مستخدم مدير (`python manage.py createsuperuser`)
- [ ] تشغيل الخادم (`python manage.py runserver`)
- [ ] فتح http://127.0.0.1:8000/admin/ والدخول
- [ ] قراءة `ARCHITECTURE.md`
- [ ] تجربة API باستخدام Postman أو curl

---

*آخر تحديث: 2026-01-04*
