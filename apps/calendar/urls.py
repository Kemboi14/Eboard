from django.urls import path
from . import views

app_name = "calendar"

urlpatterns = [
    path("", views.calendar_view, name="calendar"),
    path("event/<uuid:event_id>/", views.event_detail, name="event_detail"),
    path("preferences/", views.calendar_preferences, name="preferences"),
    
    # External Calendar Integration
    path("external-connections/", views.ExternalCalendarConnectionListView.as_view(), name="external_connections"),
    path("external-connections/<uuid:pk>/", views.ExternalCalendarConnectionDetailView.as_view(), name="external_connection_detail"),
    path("external-connections/create/", views.ExternalCalendarConnectionCreateView.as_view(), name="external_connection_create"),
    path("external-connections/<uuid:pk>/authorize/", views.authorize_external_calendar, name="authorize_calendar"),
    path("external-connections/<uuid:pk>/sync/", views.sync_external_calendar, name="sync_calendar"),
    path("external-connections/<uuid:pk>/disconnect/", views.disconnect_external_calendar, name="disconnect_calendar"),
    path("sync-logs/", views.CalendarSyncLogListView.as_view(), name="sync_logs"),
]
