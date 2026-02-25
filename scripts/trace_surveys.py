import os
import sys
import django
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

# Setup Django environment
# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.dev')
django.setup()

from surveys.models import Survey, SurveyQuestion, SurveyResponse

def trace_survey_flow():
    print("--- starting survey trace ---")
    User = get_user_model()
    
    # 1. Create a test user (admin)
    admin_user, created = User.objects.get_or_create(username='trace_admin')
    if created:
        admin_user.set_password('admin123')
        admin_user.is_superuser = True
        admin_user.save()
        print(f"created admin user: {admin_user.username}")
    else:
        print(f"found admin user: {admin_user.username}")
    
    # 2. Create a test user (respondent)
    user, created = User.objects.get_or_create(username='trace_user')
    if created:
        user.set_password('user123')
        user.save()
        print(f"created respondent user: {user.username}")
    else:
        print(f"found respondent user: {user.username}")

    # 3. Create a Survey
    survey = Survey.objects.create(
        title=f"Trace Survey {timezone.now().strftime('%H:%M:%S')}",
        description="A survey created by the trace script.",
        created_by=admin_user,
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timezone.timedelta(days=7),
        is_active=True
    )
    print(f"created survey: {survey.title} (ID: {survey.id})")

    # 4. Add Questions
    q1 = SurveyQuestion.objects.create(
        survey=survey,
        question_text="How satisfied are you?",
        question_type="rating",
        order=1
    )
    print(f"added question 1: {q1.question_text} ({q1.question_type})")

    q2 = SurveyQuestion.objects.create(
        survey=survey,
        question_text="Any comments?",
        question_type="text",
        order=2
    )
    print(f"added question 2: {q2.question_text} ({q2.question_type})")

    # 5. Simulate Response
    answers = {
        str(q1.id): "5",
        str(q2.id): "Great system!"
    }
    
    response = SurveyResponse.objects.create(
        survey=survey,
        user=user,
        answers=answers
    )
    print(f"submitted response by {user.username}: {answers}")

    # 6. Verify Results
    print(f"survey response count: {survey.response_count}")
    
    # Verify Data Integrity
    saved_response = SurveyResponse.objects.get(id=response.id)
    print("verified saved answers:")
    for q_id, ans in saved_response.answers.items():
        q_text = SurveyQuestion.objects.get(id=q_id).question_text
        print(f"  - {q_text}: {ans}")

    print("--- trace complete ---")

if __name__ == "__main__":
    trace_survey_flow()
