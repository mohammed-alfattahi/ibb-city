from django.urls import path
from . import views

urlpatterns = [
    path('', views.SurveyListView.as_view(), name='survey_list'),
    path('<int:pk>/', views.SurveyDetailView.as_view(), name='survey_detail'),
    path('<int:pk>/results/', views.SurveyResultsView.as_view(), name='survey_results'),
    path('<int:pk>/export/', views.SurveyExportCSVView.as_view(), name='survey_export'),
    path('<int:pk>/toggle-active/', views.toggle_survey_active, name='survey_toggle_active'),
]
