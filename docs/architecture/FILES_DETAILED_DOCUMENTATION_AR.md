# 📁 التوثيق التفصيلي لملفات مشروع دليل إب السياحي

> **شرح كل ملف ووظيفته والعلاقات بينها**

---

## 📋 فهرس التطبيقات

1. [تطبيق المستخدمين (users)](#-تطبيق-المستخدمين-users)
2. [تطبيق الأماكن (places)](#-تطبيق-الأماكن-places)
3. [تطبيق التفاعلات (interactions)](#-تطبيق-التفاعلات-interactions)
4. [تطبيق الإدارة (management)](#-تطبيق-الإدارة-management)
5. [إعدادات المشروع (ibb_guide)](#-إعدادات-المشروع-ibb_guide)
6. [مخطط العلاقات الكامل](#-مخطط-العلاقات-الكامل)

---

# 👥 تطبيق المستخدمين (users)

## 📊 مخطط العلاقات

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         تطبيق المستخدمين (users/)                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   models.py ◄──────────────────┐                                         │
│      │                         │                                         │
│      │ يستخدم النماذج          │ يستورد النماذج                          │
│      ▼                         │                                         │
│   ┌──────────┐   ┌──────────┐  │  ┌──────────┐                           │
│   │ forms.py │   │ admin.py │──┘  │ views.py │                           │
│   └────┬─────┘   └──────────┘     └────┬─────┘                           │
│        │                               │                                 │
│        │ يستخدم الفورمات               │ يستخدم الفورمات والنماذج         │
│        │                               ▼                                 │
│        └──────────────────────► templates/                               │
│                                                                           │
│   services/                    signals.py                                │
│      │                            │                                      │
│      └────► email_service.py      └────► ينطلق عند حفظ User              │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 📄 الملفات بالتفصيل

### 1️⃣ `models.py` - النماذج (قاعدة البيانات)

```
الموقع: users/models.py
الحجم: ~450 سطر
```

**الوظيفة**: يحدد هيكل البيانات في قاعدة البيانات

**النماذج المُعرَّفة**:

| النموذج               | الوظيفة             | الحقول الرئيسية                               |
| --------------------- | ------------------- | --------------------------------------------- |
| `Role`                | الأدوار والصلاحيات  | name, description, permissions                |
| `JobPosition`         | المناصب الوظيفية    | title, department                             |
| `Interest`            | اهتمامات المستخدمين | name, icon                                    |
| `User`                | المستخدم الرئيسي    | full_name, phone, email, role, account_status |
| `PartnerProfile`      | ملف الشريك التجاري  | organization_name, commercial_reg_no, status  |
| `UserRegistrationLog` | سجل التسجيلات       | email, ip_address, status                     |
| `UserLoginLog`        | سجل تسجيلات الدخول  | username_or_email, status                     |

**العلاقات**:

```
User ←────OneToOne────→ PartnerProfile
User ←────ForeignKey───→ Role
User ←────ManyToMany───→ Interest
User ←────ManyToMany───→ JobPosition
```

**يستخدمه**: forms.py, views.py, admin.py, signals.py

---

### 2️⃣ `forms.py` - نماذج الإدخال

```
الموقع: users/forms.py
الحجم: ~280 سطر
```

**الوظيفة**: تعريف نماذج HTML للإدخال والتحقق من البيانات

**الفورمات**:

| الفورم               | الوظيفة            | يستخدم نموذج   |
| -------------------- | ------------------ | -------------- |
| `VisitorSignUpForm`  | تسجيل زائر جديد    | User           |
| `PartnerProfileForm` | تحديث ملف الشريك   | PartnerProfile |
| `UserUpdateForm`     | تحديث الملف الشخصي | User           |

**يعتمد على**: models.py
**يُستخدم في**: views.py, views_partner.py

---

### 3️⃣ `forms_auth.py` - فورمات المصادقة

```
الموقع: users/forms_auth.py
الحجم: ~290 سطر
```

**الوظيفة**: نماذج خاصة بالتسجيل والترقية

**الفورمات**:

| الفورم               | الوظيفة             |
| -------------------- | ------------------- |
| `PartnerSignUpForm`  | تسجيل شريك جديد     |
| `TouristUpgradeForm` | ترقية سائح إلى شريك |

**يعتمد على**: models.py (User, PartnerProfile)
**يُستخدم في**: views_partner.py

---

### 4️⃣ `forms_login.py` - فورم تسجيل الدخول

```
الموقع: users/forms_login.py
الحجم: ~60 سطر
```

**الوظيفة**: نموذج تسجيل الدخول الموحد

**الفورمات**:

| الفورم             | الوظيفة                             |
| ------------------ | ----------------------------------- |
| `UnifiedLoginForm` | تسجيل دخول بالإيميل أو اسم المستخدم |

**يُستخدم في**: views.py (UnifiedLoginView)

---

### 5️⃣ `views.py` - العروض الرئيسية

```
الموقع: users/views.py
الحجم: ~420 سطر
```

**الوظيفة**: معالجة الطلبات وعرض الصفحات

**العروض (Views)**:

| الكلاس                  | الوظيفة           | يستخدم             | URL                 |
| ----------------------- | ----------------- | ------------------ | ------------------- |
| `VisitorSignUpView`     | تسجيل زائر        | VisitorSignUpForm  | /signup/            |
| `RegisterView`          | تسجيل API         | RegisterSerializer | /api/register/      |
| `UserProfileView`       | الملف الشخصي      | UserUpdateForm     | /profile/           |
| `UnifiedLoginView`      | تسجيل الدخول      | UnifiedLoginForm   | /login/             |
| `VerificationSentView`  | صفحة التحقق       | -                  | /verification-sent/ |
| `EmailVerificationView` | التحقق من الإيميل | -                  | /verify/<token>/    |

**يعتمد على**: forms.py, models.py, email_service.py
**يُستخدم من**: urls.py

---

### 6️⃣ `views_partner.py` - عروض الشريك

```
الموقع: users/views_partner.py
الحجم: ~140 سطر
```

**الوظيفة**: عروض خاصة بالشريك التجاري

**العروض**:

| الكلاس                        | الوظيفة          |
| ----------------------------- | ---------------- |
| `PartnerSignUpView`           | تسجيل شريك جديد  |
| `PartnerProfileUpdateView`    | تحديث ملف الشريك |
| `PartnerPendingView`          | عرض حالة الطلب   |
| `TouristToPartnerUpgradeView` | ترقية سائح لشريك |

**يعتمد على**: forms_auth.py, models.py, services/partner_service.py

---

### 7️⃣ `admin.py` - لوحة الإدارة

```
الموقع: users/admin.py
الحجم: ~330 سطر
```

**الوظيفة**: تخصيص Django Admin لإدارة المستخدمين

**الكلاسات**:

| الكلاس                     | يدير                | الميزات                                  |
| -------------------------- | ------------------- | ---------------------------------------- |
| `CustomUserAdmin`          | User                | شارات ملونة، إجراءات جماعية، استيراد CSV |
| `PartnerProfileAdmin`      | PartnerProfile      | موافقة/رفض الشركاء                       |
| `RoleAdmin`                | Role                | عرض عدد المستخدمين                       |
| `UserRegistrationLogAdmin` | UserRegistrationLog | للقراءة فقط                              |

**يعتمد على**: models.py

---

### 8️⃣ `email_service.py` - خدمة البريد

```
الموقع: users/email_service.py
الحجم: ~130 سطر
```

**الوظيفة**: إرسال رسائل التحقق

**الدوال**:

| الدالة                                     | الوظيفة                        |
| ------------------------------------------ | ------------------------------ |
| `generate_verification_token()`            | توليد رمز آمن                  |
| `send_verification_email(user, request)`   | إرسال إيميل التحقق             |
| `resend_verification_email(user, request)` | إعادة الإرسال مع Rate Limiting |

**يُستخدم في**: views.py (VisitorSignUpView)

---

### 9️⃣ `signals.py` - الإشارات

```
الموقع: users/signals.py
الحجم: ~25 سطر
```

**الوظيفة**: تنفيذ إجراءات تلقائية عند أحداث معينة

**الإشارات**:

| الإشارة                   | الحدث              | الإجراء                |
| ------------------------- | ------------------ | ---------------------- |
| `sync_user_role_to_group` | post_save على User | مزامنة الدور مع Groups |

**يعتمد على**: models.py (User, Role)

---

### 🔟 `mixins.py` - خلطات الصلاحيات

```
الموقع: users/mixins.py
الحجم: ~65 سطر
```

**الوظيفة**: توفير فحوصات صلاحيات قابلة لإعادة الاستخدام

**الخلطات**:

| الخلطة                         | الوظيفة                          |
| ------------------------------ | -------------------------------- |
| `RbacPermissionRequiredMixin`  | التحقق من صلاحية معينة           |
| `ApprovedPartnerRequiredMixin` | التحقق من أن المستخدم شريك معتمد |

**يُستخدم في**: views في تطبيقات أخرى (places/, management/)

---

### 1️⃣1️⃣ `backends.py` - نظام المصادقة

```
الموقع: users/backends.py
الحجم: ~30 سطر
```

**الوظيفة**: السماح بتسجيل الدخول بالإيميل أو اسم المستخدم

**الكلاسات**:

| الكلاس                        | الوظيفة     |
| ----------------------------- | ----------- |
| `EmailOrUsernameModelBackend` | مصادقة مرنة |

**يُستخدم في**: settings.py (AUTHENTICATION_BACKENDS)

---

### 1️⃣2️⃣ `serializers.py` - محولات API

```
الموقع: users/serializers.py
الحجم: ~70 سطر
```

**الوظيفة**: تحويل النماذج لـ JSON (لـ REST API)

**المحولات**:

| المحول               | يحول           |
| -------------------- | -------------- |
| `RegisterSerializer` | User (للتسجيل) |
| `UserSerializer`     | User (للعرض)   |

**يُستخدم في**: views_api.py

---

## 🔗 سلسلة الاعتماديات (users/)

```
models.py (الأساس)
    ↓
    ├── forms.py ────────────► views.py
    ├── forms_auth.py ───────► views_partner.py
    ├── forms_login.py ──────► views.py
    ├── admin.py
    ├── serializers.py ──────► views_api.py
    ├── signals.py
    └── services/
            └── email_service.py ──► views.py

mixins.py ──────► أي view يحتاج فحص صلاحيات
backends.py ────► settings.py
```

---

# 📍 تطبيق الأماكن (places)

## 📊 مخطط العلاقات

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         تطبيق الأماكن (places/)                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   models/                                                                 │
│      ├── base.py ─────────────────┐                                      │
│      │   (Category, Place)        │                                      │
│      ├── establishments.py ◄──────┤ يرث من Place                         │
│      │   (Establishment, Unit)    │                                      │
│      ├── landmarks.py ◄───────────┤ يرث من Place                         │
│      │   (Landmark, ServicePoint) │                                      │
│      └── routes.py                │                                      │
│          (TouristRoute)           │                                      │
│                                   │                                      │
│   forms.py ◄──────────────────────┘                                      │
│      │                                                                   │
│      │ يستخدم الفورمات                                                   │
│      ▼                                                                   │
│   views_public.py ─────────► templates/places/                           │
│   views_partner.py ────────► templates/partners/                         │
│                                                                           │
│   services/                                                              │
│      ├── place_service.py                                                │
│      ├── establishment_service.py                                        │
│      └── analytics_service.py                                            │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 📄 الملفات بالتفصيل

### 1️⃣ `models/base.py` - النماذج الأساسية

**النماذج**:

| النموذج      | الوظيفة               | الحقول الرئيسية                        |
| ------------ | --------------------- | -------------------------------------- |
| `Category`   | فئات الأماكن          | name, icon, parent                     |
| `Amenity`    | المرافق               | name, icon                             |
| `Place`      | المكان الأساسي (مجرد) | name, description, latitude, longitude |
| `PlaceMedia` | صور وفيديوهات المكان  | place, file, media_type                |

---

### 2️⃣ `models/establishments.py` - المنشآت

**النماذج**:

| النموذج             | الوظيفة                         | يرث من           |
| ------------------- | ------------------------------- | ---------------- |
| `Establishment`     | منشأة تجارية (فندق، مطعم)       | Place            |
| `EstablishmentUnit` | وحدة داخل المنشأة (غرفة، طاولة) | TimeStampedModel |

**العلاقات**:

```
Establishment ←────ForeignKey────→ User (owner)
Establishment ←────ForeignKey────→ Category
EstablishmentUnit ←────ForeignKey────→ Establishment
```

---

### 3️⃣ `models/landmarks.py` - المعالم

**النماذج**:

| النموذج        | الوظيفة                    | يرث من |
| -------------- | -------------------------- | ------ |
| `Landmark`     | معلم سياحي/تاريخي          | Place  |
| `ServicePoint` | نقطة خدمة (ATM، محطة وقود) | Place  |

---

### 4️⃣ `views_public.py` - العروض العامة

**العروض**:

| الكلاس               | الوظيفة         | URL             |
| -------------------- | --------------- | --------------- |
| `HomeView`           | الصفحة الرئيسية | /               |
| `PlaceListView`      | قائمة الأماكن   | /places/        |
| `PlaceDetailView`    | تفاصيل مكان     | /places/<id>/   |
| `CategoryPlacesView` | أماكن فئة معينة | /category/<id>/ |
| `SearchView`         | البحث           | /search/        |

---

### 5️⃣ `views_partner.py` - عروض الشريك

**العروض**:

| الكلاس                    | الوظيفة          |
| ------------------------- | ---------------- |
| `PartnerDashboardView`    | لوحة تحكم الشريك |
| `EstablishmentCreateView` | إضافة منشأة      |
| `EstablishmentUpdateView` | تعديل منشأة      |
| `EstablishmentDeleteView` | حذف منشأة        |
| `UnitListView`            | قائمة الوحدات    |
| `UnitCreateView`          | إضافة وحدة       |

**يعتمد على**: users/mixins.py (ApprovedPartnerRequiredMixin)

---

### 6️⃣ `services/` - الخدمات

| الملف                      | الوظيفة            |
| -------------------------- | ------------------ |
| `place_service.py`         | منطق الأماكن       |
| `establishment_service.py` | منطق المنشآت       |
| `analytics_service.py`     | إحصائيات المشاهدات |
| `search_service.py`        | خدمة البحث         |

---

# 💬 تطبيق التفاعلات (interactions)

## 📊 مخطط العلاقات

```
┌───────────────────────────────────────────────────────────────────────────┐
│                       تطبيق التفاعلات (interactions/)                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   models/                                                                 │
│      ├── favorites.py ─────► Favorite, Itinerary, ItineraryItem          │
│      ├── reviews.py ───────► Review, PlaceComment                        │
│      ├── reports.py ───────► Report                                      │
│      ├── follows.py ───────► EstablishmentFollow                         │
│      └── notifications.py ─► Notification, NotificationPreference        │
│                                                                           │
│   notifications/                (مجلد فرعي)                              │
│      ├── base.py               ► الكلاس الأساسي للإشعارات               │
│      ├── dispatcher.py         ► موزع الإشعارات                         │
│      ├── handlers.py           ► معالجات الإشعارات                       │
│      ├── types.py              ► أنواع الإشعارات                         │
│      └── push_service.py       ► خدمة Push                              │
│                                                                           │
│   signals.py ──────────────────► إشارات لإنشاء إشعارات تلقائية           │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 📄 الملفات بالتفصيل

### 1️⃣ `models/favorites.py` - المفضلة

**النماذج**:

| النموذج         | الوظيفة        | العلاقات          |
| --------------- | -------------- | ----------------- |
| `Favorite`      | مكان مفضل      | User → Place      |
| `Itinerary`     | جدول رحلة      | User              |
| `ItineraryItem` | عنصر في الجدول | Itinerary → Place |

---

### 2️⃣ `models/reviews.py` - التقييمات

**النماذج**:

| النموذج        | الوظيفة        | العلاقات     |
| -------------- | -------------- | ------------ |
| `Review`       | تقييم مكان     | User → Place |
| `PlaceComment` | تعليق على مكان | User → Place |

---

### 3️⃣ `models/notifications.py` - الإشعارات

**النماذج**:

| النموذج                  | الوظيفة           |
| ------------------------ | ----------------- |
| `Notification`           | إشعار للمستخدم    |
| `NotificationPreference` | تفضيلات الإشعارات |
| `SystemAlert`            | تنبيه نظام        |

---

### 4️⃣ `signals.py` - الإشارات

**الإشارات**:

| الإشارة                  | الحدث     | الإجراء                  |
| ------------------------ | --------- | ------------------------ |
| عند إنشاء Review         | post_save | إرسال إشعار لصاحب المكان |
| عند الموافقة على Partner | post_save | إرسال إشعار للشريك       |
| عند بلاغ جديد            | post_save | إرسال إشعار للأدمن       |

---

# ⚙️ تطبيق الإدارة (management)

## 📊 مخطط العلاقات

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         تطبيق الإدارة (management/)                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   models/                                                                 │
│      ├── advertisements.py ─► Advertisement, Invoice                     │
│      ├── requests.py ───────► Request, ApprovalAssignment                │
│      ├── alerts.py ─────────► EmergencyAlert, EmergencyContact           │
│      ├── content.py ────────► HeroSlide, SiteSetting, Menu, etc.         │
│      ├── audit.py ──────────► AuditLog, ErrorLog                         │
│      └── moderation.py ─────► ModerationRule, BannedWord                 │
│                                                                           │
│   views_admin.py ───────────► لوحة التحكم المخصصة                        │
│   views_approvals.py ───────► معالجة الموافقات                           │
│   views_ads.py ─────────────► إدارة الإعلانات                            │
│                                                                           │
│   services/                                                              │
│      ├── approval_service.py                                             │
│      ├── notification_service.py                                         │
│      └── moderation_service.py                                           │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

# ⚙️ إعدادات المشروع (ibb_guide)

## 📄 الملفات

| الملف              | الوظيفة            |
| ------------------ | ------------------ |
| `settings/base.py` | الإعدادات الأساسية |
| `settings/dev.py`  | إعدادات التطوير    |
| `settings/prod.py` | إعدادات الإنتاج    |
| `urls.py`          | جميع مسارات URL    |
| `base_models.py`   | TimeStampedModel   |
| `validators.py`    | دوال التحقق        |
| `policies.py`      | سياسات الأمان      |
| `middleware.py`    | Middleware مخصص    |
| `mixins.py`        | خلطات مشتركة       |

---

# 🔗 مخطط العلاقات الكامل

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          العلاقات بين التطبيقات                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌──────────────┐                                                             │
│   │    users     │                                                             │
│   │  ──────────  │                                                             │
│   │  User        │◄────────────────────────────────────────────────┐           │
│   │  PartnerProfile                                                │           │
│   └──────┬───────┘                                                 │           │
│          │                                                         │           │
│          │ ForeignKey (owner)                                      │           │
│          ▼                                                         │           │
│   ┌──────────────┐         ┌──────────────┐                       │           │
│   │    places    │         │ interactions │                       │           │
│   │  ──────────  │◄────────│  ──────────  │                       │           │
│   │  Place       │         │  Review      │───────────────────────┘           │
│   │  Establishment         │  Favorite    │  (ForeignKey - user)              │
│   │  Category    │         │  Notification│                                   │
│   └──────┬───────┘         └──────────────┘                                   │
│          │                                                                     │
│          │ ForeignKey (place)                                                  │
│          ▼                                                                     │
│   ┌──────────────┐                                                             │
│   │  management  │                                                             │
│   │  ──────────  │                                                             │
│   │  Advertisement                                                             │
│   │  Request     │◄─── يربط بين المستخدمين والأماكن                            │
│   │  AuditLog    │                                                             │
│   └──────────────┘                                                             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 ملخص العلاقات الرئيسية

| العلاقة              | من                | إلى            | النوع      |
| -------------------- | ----------------- | -------------- | ---------- |
| المستخدم يملك منشأة  | User              | Establishment  | ForeignKey |
| المستخدم له ملف شريك | User              | PartnerProfile | OneToOne   |
| المستخدم يقيّم مكان  | User              | Review         | ForeignKey |
| المستخدم يفضّل مكان  | User              | Favorite       | ForeignKey |
| التقييم لمكان        | Review            | Place          | ForeignKey |
| المنشأة تتبع فئة     | Establishment     | Category       | ForeignKey |
| الوحدة داخل منشأة    | EstablishmentUnit | Establishment  | ForeignKey |
| الإعلان لمستخدم      | Advertisement     | User           | ForeignKey |
| الإشعار لمستخدم      | Notification      | User           | ForeignKey |

---

## 🔄 تدفق البيانات

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Request │ ──► │  View   │ ──► │  Model  │ ──► │Database │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
     ▲               │               │
     │               │               │
     │          ┌────▼────┐     ┌────▼────┐
     │          │  Form   │     │ Service │
     │          └─────────┘     └─────────┘
     │               │
     │          ┌────▼────┐
     └──────────│Template │
                └─────────┘
```

---

> **تم إنشاء هذا التوثيق بتاريخ**: 2026-02-08
