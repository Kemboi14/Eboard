from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.http import require_POST

from .models import (
    Survey, SurveyQuestion, SurveyResponse, SurveyAnswer,
    Poll, PollOption, PollVote
)


# ─── Survey Views ─────────────────────────────────────────────────────────────

class SurveyListView(LoginRequiredMixin, ListView):
    """List all surveys"""
    model = Survey
    template_name = 'survey/surveys.html'
    context_object_name = 'surveys'
    ordering = ['-created_at']


class SurveyDetailView(LoginRequiredMixin, DetailView):
    """View survey details"""
    model = Survey
    template_name = 'survey/survey_detail.html'
    context_object_name = 'survey'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = self.object
        context['questions'] = survey.questions.all()
        
        # Check if user has already responded
        user_response = SurveyResponse.objects.filter(
            survey=survey,
            user=self.request.user
        ).first()
        context['user_response'] = user_response
        context['has_responded'] = user_response is not None
        
        return context


class SurveyCreateView(LoginRequiredMixin, CreateView):
    """Create a new survey"""
    model = Survey
    template_name = 'survey/survey_form.html'
    fields = ['title', 'description', 'survey_type', 'target_audience', 'start_date', 'end_date', 'allow_anonymous', 'max_responses', 'status']
    success_url = reverse_lazy('survey:surveys')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Survey created successfully.')
        return super().form_valid(form)


class SurveyQuestionCreateView(LoginRequiredMixin, CreateView):
    """Create a new survey question"""
    model = SurveyQuestion
    template_name = 'survey/survey_question_form.html'
    fields = ['survey', 'question_text', 'question_type', 'options', 'is_required', 'order']
    
    def get_success_url(self):
        return reverse('survey:survey_detail', kwargs={'pk': self.object.survey.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Question added successfully.')
        return super().form_valid(form)


@login_required
def submit_survey_response(request, survey_pk):
    """Submit a survey response"""
    survey = get_object_or_404(Survey, pk=survey_pk)
    
    if survey.status != 'active':
        messages.error(request, 'This survey is not currently active.')
        return redirect('survey:survey_detail', pk=survey_pk)
    
    if not survey.is_anonymous and not survey.allow_multiple_responses:
        if SurveyResponse.objects.filter(survey=survey, user=request.user).exists():
            messages.error(request, 'You have already responded to this survey.')
            return redirect('survey:survey_detail', pk=survey_pk)
    
    if request.method == 'POST':
        # Create survey response
        response = SurveyResponse.objects.create(
            survey=survey,
            user=request.user if not survey.is_anonymous else None,
            submitted_at=timezone.now()
        )
        
        # Process each question answer
        for question in survey.questions.all():
            answer_key = f'question_{question.pk}'
            answer_value = request.POST.get(answer_key)
            
            if answer_value:
                SurveyAnswer.objects.create(
                    response=response,
                    question=question,
                    answer_text=answer_value
                )
        
        messages.success(request, 'Your response has been submitted successfully.')
        return redirect('survey:survey_detail', pk=survey_pk)
    
    context = {
        'survey': survey,
        'questions': survey.questions.all(),
    }
    return render(request, 'survey/survey_response_form.html', context)


class SurveyResponseListView(LoginRequiredMixin, ListView):
    """List survey responses"""
    model = SurveyResponse
    template_name = 'survey/survey_responses.html'
    context_object_name = 'responses'
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        survey_id = self.request.GET.get('survey')
        if survey_id:
            queryset = queryset.filter(survey_id=survey_id)
        return queryset


# ─── Poll Views ───────────────────────────────────────────────────────────────

class PollListView(LoginRequiredMixin, ListView):
    """List all polls"""
    model = Poll
    template_name = 'survey/polls.html'
    context_object_name = 'polls'
    ordering = ['-created_at']


class PollDetailView(LoginRequiredMixin, DetailView):
    """View poll details"""
    model = Poll
    template_name = 'survey/poll_detail.html'
    context_object_name = 'poll'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll = self.object
        context['options'] = poll.options.all()
        
        # Check if user has voted
        user_vote = PollVote.objects.filter(
            poll=poll,
            user=self.request.user
        ).first()
        context['user_vote'] = user_vote
        context['has_voted'] = user_vote is not None
        
        # Calculate vote counts
        total_votes = poll.votes.count()
        context['total_votes'] = total_votes
        
        for option in context['options']:
            option.vote_count = option.votes.count()
            if total_votes > 0:
                option.vote_percentage = round((option.vote_count / total_votes) * 100, 1)
            else:
                option.vote_percentage = 0
        
        return context


class PollCreateView(LoginRequiredMixin, CreateView):
    """Create a new poll"""
    model = Poll
    template_name = 'survey/poll_form.html'
    fields = ['question', 'description', 'allow_multiple_options', 'start_date', 'end_date', 'is_anonymous', 'show_results_after_vote']
    success_url = reverse_lazy('survey:polls')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Poll created successfully. Add options below.')
        return super().form_valid(form)


class PollOptionCreateView(LoginRequiredMixin, CreateView):
    """Create a new poll option"""
    model = PollOption
    template_name = 'survey/poll_option_form.html'
    fields = ['poll', 'option_text', 'order']
    
    def get_success_url(self):
        return reverse('survey:poll_detail', kwargs={'pk': self.object.poll.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Option added successfully.')
        return super().form_valid(form)


@login_required
@require_POST
def cast_poll_vote(request, poll_pk):
    """Cast a vote in a poll"""
    poll = get_object_or_404(Poll, pk=poll_pk)
    
    if poll.status != 'active':
        messages.error(request, 'This poll is not currently active.')
        return redirect('survey:poll_detail', pk=poll_pk)
    
    if not poll.is_anonymous:
        if PollVote.objects.filter(poll=poll, user=request.user).exists():
            messages.error(request, 'You have already voted in this poll.')
            return redirect('survey:poll_detail', pk=poll_pk)
    
    # Get selected options
    option_ids = request.POST.getlist('options')
    
    if not option_ids:
        messages.error(request, 'Please select at least one option.')
        return redirect('survey:poll_detail', pk=poll_pk)
    
    if not poll.allow_multiple_options and len(option_ids) > 1:
        messages.error(request, 'This poll allows only one option.')
        return redirect('survey:poll_detail', pk=poll_pk)
    
    # Create votes
    for option_id in option_ids:
        option = get_object_or_404(PollOption, pk=option_id, poll=poll)
        PollVote.objects.create(
            poll=poll,
            option=option,
            user=request.user if not poll.is_anonymous else None,
            voted_at=timezone.now()
        )
    
    messages.success(request, 'Your vote has been cast successfully.')
    return redirect('survey:poll_detail', pk=poll_pk)


class PollVoteListView(LoginRequiredMixin, ListView):
    """List poll votes"""
    model = PollVote
    template_name = 'survey/poll_votes.html'
    context_object_name = 'votes'
    ordering = ['-voted_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        poll_id = self.request.GET.get('poll')
        if poll_id:
            queryset = queryset.filter(poll_id=poll_id)
        return queryset
