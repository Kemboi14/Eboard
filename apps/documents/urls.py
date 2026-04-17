from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('upload/', views.UploadDocumentView.as_view(), name='upload_document'),
    path('<uuid:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('<uuid:pk>/download/', views.download_document, name='download_document'),
    path('search/', views.document_search, name='document_search'),
    path('categories/', views.manage_categories, name='manage_categories'),
    
    # Retention Policies
    path('retention-policies/', views.RetentionPolicyListView.as_view(), name='retention_policies'),
    path('retention-policies/<uuid:pk>/', views.RetentionPolicyDetailView.as_view(), name='retention_policy_detail'),
    path('retention-policies/create/', views.RetentionPolicyCreateView.as_view(), name='retention_policy_create'),
    path('retention-policies/<uuid:pk>/update/', views.RetentionPolicyUpdateView.as_view(), name='retention_policy_update'),
    
    # Archive Records
    path('archive-records/', views.ArchiveRecordListView.as_view(), name='archive_records'),
    path('archive-records/<uuid:pk>/', views.ArchiveRecordDetailView.as_view(), name='archive_record_detail'),
    path('archive-records/<uuid:pk>/restore/', views.restore_document, name='restore_document'),
]
