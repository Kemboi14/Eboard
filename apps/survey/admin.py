from django.contrib import admin
from .models import Survey, SurveyQuestion, SurveyResponse, SurveyAnswer


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'survey_type', 'start_date', 'end_date', 'created_by', 'created_at')
    list_filter = ('survey_type', 'created_at', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'target_audience')
    ordering = ('-created_at',)
    list_per_page = 25


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ('survey', 'question_text', 'question_type', 'required', 'order')
    list_filter = ('question_type', 'required', 'survey')
    search_fields = ('question_text', 'survey__title')
    ordering = ('survey', 'order')
    list_per_page = 25


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'user', 'is_anonymous', 'submitted_at')
    list_filter = ('is_anonymous', 'submitted_at', 'survey')
    search_fields = ('user__email', 'survey__title')
    ordering = ('-submitted_at',)
    list_per_page = 25


@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ('response', 'question', 'answer_text')
    list_filter = ('question__question_type', 'response__survey')
    search_fields = ('answer_text', 'response__user__email', 'question__question_text')
    ordering = ('response', 'question')
    list_per_page = 25
