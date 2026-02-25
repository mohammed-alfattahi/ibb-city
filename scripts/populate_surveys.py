import os
import sys
import django
import random
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.dev')
django.setup()

from surveys.models import Survey, SurveyQuestion, SurveyResponse

def create_survey_data():
    print("--- Starting Survey Population ---")
    User = get_user_model()
    
    # Ensure we have an admin and some users
    admin_user, _ = User.objects.get_or_create(username='admin', defaults={'is_superuser': True, 'is_staff': True})
    admin_user.set_password('admin123')
    admin_user.save()

    # Create dummy users for responses
    users = []
    for i in range(1, 21):
        u, _ = User.objects.get_or_create(username=f'user_{i}')
        users.append(u)
    
    # 1. Tourism Satisfaction Survey
    s1, _ = Survey.objects.get_or_create(
        title="استبيان رضا الزوار عن المعالم السياحية",
        defaults={
            'description': "نرجو منكم تقييم تجربتكم في زيارة المعالم السياحية في إب.",
            'created_by': admin_user,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timezone.timedelta(days=30),
            'is_active': True
        }
    )
    
    # Questions for S1
    if not s1.questions.exists():
        SurveyQuestion.objects.create(survey=s1, question_text="كيف تقيم نظافة المعالم السياحية؟", question_type="rating", order=1)
        SurveyQuestion.objects.create(survey=s1, question_text="هل كانت الخدمات متوفرة (مطاعم، حمامات)؟", question_type="yesno", order=2)
        SurveyQuestion.objects.create(survey=s1, question_text="ما هو أكثر معلم أعجبك؟", question_type="text", order=3)
        SurveyQuestion.objects.create(survey=s1, question_text="مستوى الأسعار في الأماكن السياحية", question_type="choice", choices=["رخيص", "متوسط", "غالي"], order=4)
    
    # 2. Website Feedback Survey
    s2, _ = Survey.objects.get_or_create(
        title="رأيك في موقع دليل إب",
        defaults={
            'description': "ساعدنا في تحسين الموقع من خلال ملاحظاتك.",
            'created_by': admin_user,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timezone.timedelta(days=60),
            'is_active': True
        }
    )

    # Questions for S2
    if not s2.questions.exists():
        SurveyQuestion.objects.create(survey=s2, question_text="سهولة استخدام الموقع", question_type="rating", order=1)
        SurveyQuestion.objects.create(survey=s2, question_text="هل واجهت مشاكل تقنية؟", question_type="yesno", order=2)
        SurveyQuestion.objects.create(survey=s2, question_text="أي الأقسام تزورها أكثر؟", question_type="choice", choices=["الرئيسية", "الخريطة", "الأماكن", "الأحداث"], order=3)

    # Generate Responses
    surveys = [s1, s2]
    
    for survey in surveys:
        print(f"Generating responses for: {survey.title}")
        questions = survey.questions.all()
        
        for user in users:
            # Check if user already responded
            if SurveyResponse.objects.filter(survey=survey, user=user).exists():
                continue
                
            answers = {}
            for q in questions:
                if q.question_type == 'rating':
                    answers[str(q.id)] = str(random.randint(1, 5))
                elif q.question_type == 'yesno':
                    answers[str(q.id)] = random.choice(['نعم', 'لا'])
                elif q.question_type == 'choice':
                    answers[str(q.id)] = random.choice(q.choices)
                elif q.question_type == 'text':
                    answers[str(q.id)] = random.choice(["ممتاز", "جيد جداً", "يحتاج تحسين", "لا تعليق"])
            
            SurveyResponse.objects.create(survey=survey, user=user, answers=answers)
            print(f"  - Response added for user: {user.username}")

    print("--- Population Complete ---")

if __name__ == "__main__":
    create_survey_data()
