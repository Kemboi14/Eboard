from django.contrib import admin
from .models import CalendarEvent, CalendarConfigurator, UserCalendarPreference


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ["title", "event_type", "source_app", "source_model", "start_date", "user"]
    list_filter = ["event_type", "source_app", "status"]
    search_fields = ["title", "description"]
    date_hierarchy = "start_date"
    readonly_fields = ["created_at", "updated_at"]


@admin.register(CalendarConfigurator)
class CalendarConfiguratorAdmin(admin.ModelAdmin):
    list_display = ["name", "source_app", "source_model", "event_type", "is_active"]
    list_filter = ["source_app", "event_type", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(UserCalendarPreference)
class UserCalendarPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "default_view", "show_my_events_only", "email_reminders"]
    list_filter = ["default_view", "show_my_events_only", "email_reminders"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["created_at", "updated_at"]
