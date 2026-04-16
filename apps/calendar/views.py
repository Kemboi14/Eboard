from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from .models import CalendarEvent, UserCalendarPreference
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
