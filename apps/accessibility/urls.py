from django.urls import path
from . import views

app_name = 'accessibility'

urlpatterns = [
    # Accessibility Audits
    path('audits/', views.AccessibilityAuditListView.as_view(), name='audits'),
    path('audits/<uuid:pk>/', views.AccessibilityAuditDetailView.as_view(), name='audit_detail'),
    path('audits/create/', views.AccessibilityAuditCreateView.as_view(), name='audit_create'),
    path('audits/<uuid:pk>/start/', views.start_accessibility_audit, name='start_audit'),
    path('audits/<uuid:pk>/complete/', views.complete_accessibility_audit, name='complete_audit'),
    
    # Accessibility Issues
    path('issues/', views.AccessibilityIssueListView.as_view(), name='issues'),
    path('issues/<uuid:pk>/', views.AccessibilityIssueDetailView.as_view(), name='issue_detail'),
    path('issues/create/', views.AccessibilityIssueCreateView.as_view(), name='issue_create'),
    path('issues/<uuid:pk>/update/', views.AccessibilityIssueUpdateView.as_view(), name='issue_update'),
    
    # Accessibility Remediations
    path('remediations/', views.AccessibilityRemediationListView.as_view(), name='remediations'),
    path('remediations/<uuid:pk>/', views.AccessibilityRemediationDetailView.as_view(), name='remediation_detail'),
    path('remediations/create/', views.AccessibilityRemediationCreateView.as_view(), name='remediation_create'),
    path('remediations/<uuid:pk>/update/', views.AccessibilityRemediationUpdateView.as_view(), name='remediation_update'),
    path('remediations/<uuid:pk>/verify/', views.verify_remediation, name='verify_remediation'),
]
