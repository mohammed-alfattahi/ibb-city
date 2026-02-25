from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from .models import Survey, SurveyQuestion, SurveyResponse


class SurveyListView(ListView):
    """عرض قائمة الاستبيانات النشطة"""
    model = Survey
    template_name = 'surveys/survey_list.html'
    context_object_name = 'surveys'

    def get_queryset(self):
        return Survey.objects.filter(is_active=True)


class SurveyDetailView(DetailView):
    """عرض تفاصيل استبيان وتعبئته"""
    model = Survey
    template_name = 'surveys/survey_detail.html'
    context_object_name = 'survey'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        
        # التحقق من أن المستخدم قد أجاب مسبقاً
        if self.request.user.is_authenticated:
            context['already_responded'] = SurveyResponse.objects.filter(
                survey=self.object, 
                user=self.request.user
            ).exists()
        else:
            context['already_responded'] = False
        
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول للمشاركة في الاستبيان.')
            return redirect('login') # Assuming 'login' is the name of the login URL
            
        if not self.object.is_open:
            messages.error(request, 'هذا الاستبيان مغلق حالياً.')
            return redirect('survey_list')
        
        # التحقق من عدم الإجابة مسبقاً
        if request.user.is_authenticated:
            if SurveyResponse.objects.filter(survey=self.object, user=request.user).exists():
                messages.warning(request, 'لقد أجبت على هذا الاستبيان مسبقاً.')
                return redirect('survey_detail', pk=self.object.pk)
        
        # جمع الإجابات
        answers = {}
        for question in self.object.questions.all():
            if question.question_type == 'checkbox':
                answer = request.POST.getlist(f'question_{question.id}')
            else:
                answer = request.POST.get(f'question_{question.id}', '')
                
            if question.is_required and not answer:
                messages.error(request, f'السؤال "{question.question_text}" مطلوب.')
                return self.get(request, *args, **kwargs)
            answers[str(question.id)] = answer
        
        # حفظ الإجابة
        SurveyResponse.objects.create(
            survey=self.object,
            user=request.user if request.user.is_authenticated else None,
            answers=answers
        )
        
        messages.success(request, 'شكراً لمشاركتك! تم حفظ إجاباتك.')
        return redirect('survey_list')


class SurveyResultsView(LoginRequiredMixin, DetailView):
    """عرض نتائج الاستبيان (للإدارة)"""
    model = Survey
    template_name = 'surveys/survey_results.html'
    context_object_name = 'survey'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'لا تملك صلاحية الوصول لهذه الصفحة.')
            return redirect('survey_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        survey = self.object
        questions = survey.questions.all()
        responses = survey.responses.all()
        
        # تحليل النتائج لكل سؤال
        results = []
        for question in questions:
            q_results = {
                'question': question,
                'answers': [],
                'stats': {}
            }
            
            # جمع الإجابات
            for response in responses:
                answer = response.answers.get(str(question.id), '')
                if answer:
                    q_results['answers'].append(answer)
            
            # إحصائيات حسب نوع السؤال
            if question.question_type == 'rating':
                try:
                    ratings = [int(a) for a in q_results['answers'] if a.isdigit()]
                    if ratings:
                        q_results['stats']['avg'] = sum(ratings) / len(ratings)
                        q_results['stats']['count'] = len(ratings)
                        q_results['stats']['distribution'] = {
                            i: ratings.count(i) for i in range(1, 6)
                        }
                except:
                    pass
            
            elif question.question_type in ['choice', 'yesno', 'select']:
                # توزيع الإجابات
                answer_counts = {}
                for a in q_results['answers']:
                    answer_counts[a] = answer_counts.get(a, 0) + 1
                q_results['stats']['distribution'] = answer_counts
                
            elif question.question_type == 'checkbox':
                # توزيع الاختيارات المتعددة
                answer_counts = {}
                for a_list in q_results['answers']:
                    if isinstance(a_list, list):
                        for a in a_list:
                            answer_counts[a] = answer_counts.get(a, 0) + 1
                    else:
                        # Fallback if just a string
                        answer_counts[a_list] = answer_counts.get(a_list, 0) + 1
                q_results['stats']['distribution'] = answer_counts
            
            results.append(q_results)
        
        context['results'] = results
        context['total_responses'] = responses.count()
        
        return context


class SurveyExportCSVView(LoginRequiredMixin, DetailView):
    """تصدير ردود الاستبيان إلى ملف CSV (للإدارة)"""
    model = Survey

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('survey_list')
            
        import csv
        from django.http import HttpResponse
        
        survey = self.get_object()
        responses = survey.responses.all().order_by('-created_at')
        questions = survey.questions.all()
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="survey_{survey.id}_responses.csv"'
        
        writer = csv.writer(response)
        
        # العناوين
        header = ['التاريخ', 'المستخدم']
        for q in questions:
            header.append(q.question_text)
        writer.writerow(header)
        
        # الردود
        for res in responses:
            row = [
                res.created_at.strftime('%Y-%m-%d %H:%M'),
                res.user.username if res.user else 'زائر'
            ]
            for q in questions:
                answer = res.answers.get(str(q.id), '')
                # التعامل مع المصفوفات (مثل checkbox)
                if isinstance(answer, list):
                    answer = ", ".join(answer)
                row.append(answer)
            writer.writerow(row)
            
        return response


@staff_member_required
@require_POST
def toggle_survey_active(request, pk):
    """تبديل حالة نشاط الاستبيان بسرعة (خاص بالإدارة)"""
    from .models import Survey
    try:
        survey = Survey.objects.get(pk=pk)
        survey.is_active = not survey.is_active
        survey.save(update_fields=['is_active'])
        
        status = "تم فتح" if survey.is_active else "تم إغلاق"
        messages.success(request, f"{status} الاستبيان بنجاح.")
    except Survey.DoesNotExist:
        messages.error(request, "الاستبيان غير موجود.")
        
    return redirect(request.META.get('HTTP_REFERER', 'survey_list'))
