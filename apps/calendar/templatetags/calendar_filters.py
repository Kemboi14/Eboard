from django import template
from datetime import datetime, timedelta
import calendar
from django.utils import timezone

register = template.Library()


@register.filter
def calendar_days(date):
    """
    Generate a list of days for the month calendar view.
    Each day includes date, is_today flag, and events for that day.
    """
    from apps.calendar.models import CalendarEvent
    
    first_day = date.replace(day=1)
    last_day = date.replace(day=calendar.monthrange(date.year, date.month)[1])
    
    # Get the weekday of the first day (0 = Sunday)
    weekday = first_day.weekday()
    
    # Adjust to start from Sunday (0)
    days_from_previous_month = weekday + 1 if weekday < 6 else 0
    
    # Start date for the calendar grid
    start_date = first_day - timedelta(days=days_from_previous_month)
    
    # Total days to show (42 = 6 rows of 7 days)
    total_days = 42
    
    days = []
    today = timezone.now().date()
    
    for i in range(total_days):
        current_day = start_date + timedelta(days=i)
        
        # Get events for this day
        day_events = CalendarEvent.objects.filter(
            start_date__date=current_day
        )
        
        days.append({
            'date': current_day,
            'is_today': current_day == today,
            'events': day_events,
        })
    
    return days


@register.filter
def week_days(date):
    """
    Generate a list of days for the week view.
    """
    from apps.calendar.models import CalendarEvent
    
    # Get the weekday (0 = Monday, 6 = Sunday)
    weekday = date.weekday()
    
    # Start from Monday
    start_date = date - timedelta(days=weekday)
    
    days = []
    today = timezone.now().date()
    
    for i in range(7):
        current_day = start_date + timedelta(days=i)
        
        # Get events for this day
        day_events = CalendarEvent.objects.filter(
            start_date__date=current_day
        )
        
        days.append({
            'date': current_day,
            'is_today': current_day == today,
            'events': day_events,
        })
    
    return days


@register.filter
def day_hours(date):
    """
    Generate a list of hours for the day view (6 AM to 10 PM).
    """
    hours = []
    for hour in range(6, 23):
        hours.append(datetime.combine(date, datetime.min.time()).replace(hour=hour))
    return hours


@register.filter
def day_events(events, hour):
    """
    Filter events for a specific hour.
    """
    hour_events = []
    for event in events:
        if event.start_date.hour == hour.hour:
            hour_events.append(event)
    return hour_events
