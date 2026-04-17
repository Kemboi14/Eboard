from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import (
    CalendarEvent, UserCalendarPreference,
    ExternalCalendarConnection, CalendarSyncLog
)
import calendar


@login_required
def calendar_view(request):
    """
    Main calendar view with multiple views (month, week, day, agenda).
    """
    # Get or create user preferences
    preferences, created = UserCalendarPreference.objects.get_or_create(
        user=request.user
    )
    
    # Get view type from query params or preferences
    view_type = request.GET.get("view", preferences.default_view)
    
    # Get date from query params or use today
    date_str = request.GET.get("date")
    if date_str:
        current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        current_date = timezone.now().date()
    
    # Get filter parameters
    event_type_filter = request.GET.get("event_type")
    my_events_only = request.GET.get("my_events_only") == "true"
    
    # Build base queryset
    events = CalendarEvent.objects.all()
    
    # Apply filters
    if event_type_filter:
        events = events.filter(event_type=event_type_filter)
    
    if my_events_only:
        events = events.filter(user=request.user)
    
    # Filter by date range based on view
    if view_type == "month":
        # Get first and last day of month
        first_day = current_date.replace(day=1)
        last_day = calendar.monthrange(current_date.year, current_date.month)[1]
        last_day = current_date.replace(day=last_day)
        
        # Extend to include full weeks
        weekday = first_day.weekday()
        if preferences.start_of_week == 1:  # Monday start
            first_day = first_day - timedelta(days=weekday)
        else:  # Sunday start
            first_day = first_day - timedelta(days=(weekday + 1) % 7)
        
        events = events.filter(
            start_date__gte=first_day,
            start_date__lte=last_day + timedelta(days=6)
        )
    
    elif view_type == "week":
        # Get start of week
        weekday = current_date.weekday()
        if preferences.start_of_week == 1:  # Monday start
            start_date = current_date - timedelta(days=weekday)
        else:  # Sunday start
            start_date = current_date - timedelta(days=(weekday + 1) % 7)
        
        end_date = start_date + timedelta(days=6)
        
        events = events.filter(
            start_date__gte=start_date,
            start_date__lte=end_date
        )
    
    elif view_type == "day":
        # Single day
        events = events.filter(
            start_date__date=current_date
        )
    
    elif view_type == "agenda":
        # Next 30 days
        end_date = current_date + timedelta(days=30)
        events = events.filter(
            start_date__gte=current_date,
            start_date__lte=end_date
        ).order_by("start_date")
    
    context = {
        "view_type": view_type,
        "current_date": current_date,
        "events": events,
        "preferences": preferences,
        "event_type_filter": event_type_filter,
        "my_events_only": my_events_only,
        "event_types": CalendarEvent.EVENT_TYPE_CHOICES,
    }
    
    return render(request, "calendar/calendar.html", context)


@login_required
def event_detail(request, event_id):
    """
    Detail view for a specific calendar event.
    """
    event = get_object_or_404(CalendarEvent, id=event_id)
    
    # Get source object if possible
    source_object = None
    try:
        model_class = event.source_model
        if model_class:
            # Import the model dynamically
            from django.apps import apps
            try:
                model = apps.get_model(event.source_app, model_class)
                source_object = model.objects.get(id=event.source_object_id)
            except Exception:
                pass
    except Exception:
        pass
    
    context = {
        "event": event,
        "source_object": source_object,
    }
    
    return render(request, "calendar/event_detail.html", context)


@login_required
def calendar_preferences(request):
    """
    View for managing user calendar preferences.
    """
    preferences, created = UserCalendarPreference.objects.get_or_create(
        user=request.user
    )
    
    if request.method == "POST":
        # Update preferences
        preferences.default_view = request.POST.get("default_view", preferences.default_view)
        preferences.show_weekends = request.POST.get("show_weekends") == "on"
        preferences.start_of_week = int(request.POST.get("start_of_week", 0))
        preferences.show_my_events_only = request.POST.get("show_my_events_only") == "on"
        preferences.email_reminders = request.POST.get("email_reminders") == "on"
        preferences.reminder_hours_before = int(request.POST.get("reminder_hours_before", 24))
        
        # Update event types filter
        show_event_types = request.POST.getlist("show_event_types")
        preferences.show_event_types = show_event_types
        
        preferences.save()
        
        from django.contrib import messages
        messages.success(request, "Calendar preferences updated successfully.")
        return render(request, "calendar/preferences.html", {"preferences": preferences})
    
    context = {
        "preferences": preferences,
        "event_types": CalendarEvent.EVENT_TYPE_CHOICES,
    }
    
    return render(request, "calendar/preferences.html", context)


# ─── External Calendar Integration Views ───────────────────────────────────────

class ExternalCalendarConnectionListView(LoginRequiredMixin, ListView):
    """List all external calendar connections"""
    model = ExternalCalendarConnection
    template_name = 'calendar/external_connections.html'
    context_object_name = 'connections'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset


class ExternalCalendarConnectionDetailView(LoginRequiredMixin, DetailView):
    """View external calendar connection details"""
    model = ExternalCalendarConnection
    template_name = 'calendar/external_connection_detail.html'
    context_object_name = 'connection'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sync_logs'] = self.object.sync_logs.all()[:20]
        return context


class ExternalCalendarConnectionCreateView(LoginRequiredMixin, CreateView):
    """Create a new external calendar connection"""
    model = ExternalCalendarConnection
    template_name = 'calendar/external_connection_form.html'
    fields = ['provider', 'account_email', 'sync_direction', 'auto_sync', 'sync_interval_hours']
    success_url = reverse_lazy('calendar:external_connections')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'pending'
        messages.success(self.request, 'External calendar connection created. Complete the authorization to activate.')
        return super().form_valid(form)


@login_required
def authorize_external_calendar(request, pk):
    """Authorize an external calendar connection"""
    connection = get_object_or_404(ExternalCalendarConnection, pk=pk, user=request.user)
    
    # In production, this would redirect to the OAuth flow for the specific provider
    # For now, we'll mark as connected
    connection.status = 'connected'
    connection.last_synced_at = timezone.now()
    connection.save()
    
    # Create a sync log
    CalendarSyncLog.objects.create(
        connection=connection,
        sync_type='full',
        status='success',
        events_synced=0,
        sync_duration_seconds=0,
    )
    
    messages.success(request, 'External calendar authorized successfully.')
    return redirect('calendar:external_connection_detail', pk=pk)


@login_required
def sync_external_calendar(request, pk):
    """Manually trigger a sync for an external calendar"""
    connection = get_object_or_404(ExternalCalendarConnection, pk=pk, user=request.user)
    
    if connection.status != 'connected':
        messages.error(request, 'Calendar connection is not active.')
        return redirect('calendar:external_connection_detail', pk=pk)
    
    # In production, this would trigger actual sync with the external API
    sync_log = CalendarSyncLog.objects.create(
        connection=connection,
        sync_type='manual',
        status='in_progress',
    )
    
    # Mock sync completion
    sync_log.status = 'success'
    sync_log.events_synced = 5
    sync_log.sync_duration_seconds = 2
    sync_log.completed_at = timezone.now()
    sync_log.save()
    
    connection.last_synced_at = timezone.now()
    connection.save()
    
    messages.success(request, 'Calendar sync completed successfully.')
    return redirect('calendar:external_connection_detail', pk=pk)


@login_required
def disconnect_external_calendar(request, pk):
    """Disconnect an external calendar"""
    connection = get_object_or_404(ExternalCalendarConnection, pk=pk, user=request.user)
    
    connection.status = 'disconnected'
    connection.save()
    
    messages.success(request, 'External calendar disconnected.')
    return redirect('calendar:external_connections')


class CalendarSyncLogListView(LoginRequiredMixin, ListView):
    """List calendar sync logs"""
    model = CalendarSyncLog
    template_name = 'calendar/sync_logs.html'
    context_object_name = 'logs'
    ordering = ['-started_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        connection_id = self.request.GET.get('connection')
        if connection_id:
            queryset = queryset.filter(connection_id=connection_id)
        return queryset
