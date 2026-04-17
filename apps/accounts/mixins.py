from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from apps.agencies.models import UserBranchMembership


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin to require specific user roles for class-based views.
    Usage: class MyView(RoleRequiredMixin): allowed_roles = ['board_member']
    """
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.role not in self.allowed_roles:
            return render(request, '403.html', status=403)
        
        return super().dispatch(request, *args, **kwargs)


class BranchOrganizationFilterMixin:
    """
    Mixin to filter data by organization and branch membership.
    IT administrators see all data. Other users only see data from
    organizations and branches they have active membership in.
    """
    
    def get_user_branch_ids(self):
        """Get branch IDs the current user has active membership in"""
        user = self.request.user
        if user.role == 'it_administrator':
            return None  # No filtering for IT admins
        
        branch_ids = UserBranchMembership.objects.filter(
            user=user,
            is_active=True
        ).values_list('branch_id', flat=True)
        
        return list(branch_ids)
    
    def get_user_organization_ids(self):
        """Get organization IDs the current user has access to via branch membership"""
        user = self.request.user
        if user.role == 'it_administrator':
            return None  # No filtering for IT admins
        
        organization_ids = UserBranchMembership.objects.filter(
            user=user,
            is_active=True
        ).values_list('branch__organization_id', flat=True).distinct()
        
        return list(organization_ids)
    
    def filter_queryset_by_branch(self, queryset, branch_field='branch'):
        """
        Filter queryset to only include records from user's branches.
        Returns original queryset for IT admins.
        """
        branch_ids = self.get_user_branch_ids()
        if branch_ids is None:
            return queryset  # IT admin sees everything
        
        filter_kwargs = {f'{branch_field}__in': branch_ids}
        return queryset.filter(**filter_kwargs)
    
    def filter_queryset_by_organization(self, queryset, organization_field='organization'):
        """
        Filter queryset to only include records from user's organizations.
        Returns original queryset for IT admins.
        """
        organization_ids = self.get_user_organization_ids()
        if organization_ids is None:
            return queryset  # IT admin sees everything
        
        filter_kwargs = {f'{organization_field}__in': organization_ids}
        return queryset.filter(**filter_kwargs)
