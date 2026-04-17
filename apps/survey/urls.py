from django.urls import path
from . import views

app_name = 'survey'

urlpatterns = [
    # Surveys
    path('surveys/', views.SurveyListView.as_view(), name='surveys'),
    path('surveys/<uuid:pk>/', views.SurveyDetailView.as_view(), name='survey_detail'),
    path('surveys/create/', views.SurveyCreateView.as_view(), name='survey_create'),
    path('surveys/<uuid:pk>/respond/', views.submit_survey_response, name='submit_survey_response'),
    path('surveys/questions/create/', views.SurveyQuestionCreateView.as_view(), name='survey_question_create'),
    path('survey-responses/', views.SurveyResponseListView.as_view(), name='survey_responses'),
    
    # Polls
    path('polls/', views.PollListView.as_view(), name='polls'),
    path('polls/<uuid:pk>/', views.PollDetailView.as_view(), name='poll_detail'),
    path('polls/create/', views.PollCreateView.as_view(), name='poll_create'),
    path('polls/options/create/', views.PollOptionCreateView.as_view(), name='poll_option_create'),
    path('polls/<uuid:pk>/vote/', views.cast_poll_vote, name='cast_poll_vote'),
    path('poll-votes/', views.PollVoteListView.as_view(), name='poll_votes'),
]
