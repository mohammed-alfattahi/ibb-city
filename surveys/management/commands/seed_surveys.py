from django.core.management.base import BaseCommand
from surveys.models import Survey, SurveyQuestion
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds a test survey'

    def handle(self, *args, **options):
        # Create a survey
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('No admin user found to assign survey to.'))
            return

        survey, created = Survey.objects.get_or_create(
            title='استبيان تجريبي: رأيك في دليل إب السياحي',
            defaults={
                'description': 'نود مشاركتنا رأيك في الخدمات المقدمة في الموقع والتحسينات المقترحة.',
                'created_by': admin,
                'is_active': True,
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timedelta(days=30)
            }
        )

        if created:
            # Add questions
            SurveyQuestion.objects.create(
                survey=survey,
                question_text='كيف تقيم تجربتك العامة في الموقع؟',
                question_type='rating',
                order=1
            )
            SurveyQuestion.objects.create(
                survey=survey,
                question_text='ما هي الميزة التي ترغب بإضافتها؟',
                question_type='text',
                order=2
            )
            SurveyQuestion.objects.create(
                survey=survey,
                question_text='هل واجهت صعوبة في التصفح؟',
                question_type='yesno',
                order=3
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created survey "{survey.title}"'))
        else:
            # Ensure it is active
            survey.is_active = True
            survey.start_date = timezone.now().date()
            survey.end_date = timezone.now().date() + timedelta(days=30)
            survey.save()
            self.stdout.write(self.style.SUCCESS(f'Updated existing survey "{survey.title}" to be active.'))
