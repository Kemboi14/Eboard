from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Messages
    path('messages/', views.MessageListView.as_view(), name='messages'),
    path('messages/<uuid:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('messages/<uuid:pk>/read/', views.mark_message_read, name='mark_read'),
    path('messages/<uuid:pk>/delete/', views.delete_message, name='delete_message'),
    
    # Message Threads
    path('threads/', views.MessageThreadListView.as_view(), name='threads'),
    path('threads/<uuid:pk>/', views.MessageThreadDetailView.as_view(), name='thread_detail'),
    
    # Announcements
    path('announcements/', views.AnnouncementListView.as_view(), name='announcements'),
    path('announcements/<uuid:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('announcements/<uuid:pk>/publish/', views.publish_announcement, name='publish_announcement'),
    path('announcements/<uuid:pk>/archive/', views.archive_announcement, name='archive_announcement'),
]
