from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    # Branch URLs
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.branch_create, name='branch_create'),
    path('branches/<uuid:pk>/', views.branch_detail, name='branch_detail'),
    path('branches/<uuid:pk>/update/', views.branch_update, name='branch_update'),
    
    # Committee URLs
    path('committees/', views.committee_list, name='committee_list'),
    path('committees/create/', views.committee_create, name='committee_create'),
    path('committees/<uuid:pk>/', views.committee_detail, name='committee_detail'),
    path('committees/<uuid:pk>/update/', views.committee_update, name='committee_update'),
    path('committees/<uuid:pk>/add-member/', views.committee_add_member, name='committee_add_member'),
    path('committees/<uuid:pk>/remove-member/<uuid:member_id>/', views.committee_remove_member, name='committee_remove_member'),
]
