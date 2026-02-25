# Ibb Tourist Guide - Operations Manual

## 1. System Overview
This is a production-grade Django application serving the Ibb Tourist Guide platform.
- **Backend**: Django 5.2 (Python 3.12+)
- **Database**: PostgreSQL (Prod) / SQLite (Dev)
- **Cache**: Redis / LocMem
- **Storage**: S3 (Media) / WhiteNoise (Static)

## 2. Environments
### 2.1 Development
- **Settings**: `ibb_guide.settings.dev`
- **Run**: `python manage.py runserver`
- **Debug**: Enabled.
- **Emails**: Console.

### 2.2 Production
- **Settings**: `ibb_guide.settings.prod`
- **Run**: `gunicorn ibb_guide.wsgi:application`
- **Debug**: Disabled.
- **Security**: Forced SSL, Secure Cookies.

## 3. Deployment (Render/Docker)
1. **Push to GitHub**: Service auto-deploys via Render hooks (if configured).
2. **Environment Variables**:
   - `DATABASE_URL`: Postgres Connection String.
   - `SECRET_KEY`: High-entropy string.
   - `ALLOWED_HOSTS`: Domain names.
   - `DJANGO_SETTINGS_MODULE`: `ibb_guide.settings.prod`

## 4. Maintenance Tasks
### 4.1 Backups
- **Database**: Automated Daily WAL archiving via Cloud Provider.
- **Media**: S3 Versioning enabled.

### 4.2 Updates
- Run `pip install -r requirements.txt`
- Run `python manage.py migrate`
- Run `python manage.py collectstatic --noinput`

## 5. Troubleshooting
### 5.1 "500 Server Error"
- Check Sentry/Logs.
- Standard causes: Missing migrations, Environment logic error.

### 5.2 "Slow Performance"
- Check Database CPU.
- Verify Index usage.
- Ensure `DEBUG=False` in Prod.

## 6. Disaster Recovery
- **RPO (Recovery Point Objective)**: < 1 Hour (Database), Immediate (Code).
- **RTO (Recovery Time Objective)**: < 4 Hours.
- **Protocol**:
    1. Assess damage scope.
    2. Spin up fresh instance.
    3. Restore DB from last snapshot.
    4. DNS failover.
