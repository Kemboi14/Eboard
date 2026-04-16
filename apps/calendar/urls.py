from django.urls import path
from . import views

app_name = "calendar"

urlpatterns = [
    path("", views.calendar_view, name="calendar"),
    path("event/<uuid:event_id>/", views.event_detail, name="event_detail"),
    path("preferences/", views.calendar_preferences, name="preferences"),
]
