# دليل نشر تطبيق دليل إب السياحي (Ibb Tourist Guide)

## 1. المتطلبات الأساسية
تأكد من تثبيت الأدوات التالية على الخادم:
- Python 3.10+
- PostgreSQL
- Git
- Nginx & Gunicorn (في حال استخدام Linux/Ubuntu)

## 2. إعداد المشروع

### نسخ المشروع
```bash
git clone <repository_url>
cd ibb_project
```

### إنشاء البيئة الافتراضية
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### تثبيت الحزم
```bash
pip install -r requirements.txt
```

### إعداد المتغيرات البيئية
1. انسخ ملف المثال:
   ```bash
   cp .env.example .env
   ```
2. عدل ملف `.env` وقم بتعبئة البيانات الحقيقية (قاعدة البيانات، Secret Key، البريد الإلكتروني).

### إعداد قاعدة البيانات
1. أنشئ قاعدة بيانات PostgreSQL.
2. نفذ الترحيلات:
   ```bash
   python manage.py migrate
   ```
3. (اختياري) تحميل بيانات تجريبية:
   ```bash
   python manage.py loaddata initial_data.json
   ```

### تجميع الملفات الثابتة (Static Files)
```bash
python manage.py collectstatic
```

## 3. التشغيل في البيئة الإنتاجية (Production)

### استخدام Gunicorn (Linux)
```bash
gunicorn ibb_guide.wsgi:application --bind 0.0.0.0:8000
```

### إعداد Nginx
استخدم Nginx كـ Reverse Proxy للملفات الثابتة ولتوجيه الطلبات إلى Gunicorn.

## 4. مستخدم المسؤول (Admin User)
إنشاء حساب مسؤول (Superuser):
```bash
python manage.py createsuperuser
```

## 5. ملاحظات هامة
- تأكد من تفعيل النسخ الاحتياطي لقاعدة البيانات.

## 6. خطوات تحديث الموقع على PythonAnywhere
لتطبيق التعديلات الجديدة (بعد عمل Push إلى GitHub)، اتبع الخطوات التالية في PythonAnywhere Consol:

1. **فتح الـ Console**:
   افتح Bash console جديد من لوحة تحكم PythonAnywhere.

2. **سحب التحديثات**:
   ```bash
   cd ~/ibb_guide_main
   git pull origin main
   ```

3. **تحديث قاعدة البيانات (إذا لزم الأمر)**:
   ```bash
   workon myvenv  # أو اسم البيئة الافتراضية الخاصة بك
   python manage.py migrate
   ```

4. **تجميع الملفات الثابتة**:
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **إعادة تشغيل التطبيق**:
   - اذهب إلى تبويب **Web**.
   - اضغط على الزر الأخضر **Reload <ydomain>.pythonanywhere.com**.

