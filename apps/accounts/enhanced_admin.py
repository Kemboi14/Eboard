from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html, mark_safe
from .models import User


class EnhancedUserAdmin(BaseUserAdmin):
    """Enhanced User Admin with improved UI and functionality"""
    
    list_display = (
        'get_avatar', 'email', 'get_full_name', 
        'get_role_badge', 'is_active', 
        'get_last_login', 'date_joined'
    )
    list_filter = (
        'role', 'is_active', 'is_staff', 'is_superuser',
        'mfa_enabled', 'department', 'date_joined', 'last_login'
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 25
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Account credentials and basic information'
        }),
        (_('Personal Information'), {
            'fields': ('first_name', 'last_name', 'phone_number', 'profile_photo'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Personal details and contact information'
        }),
        (_('Role & Permissions'), {
            'fields': ('role', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('wide', 'extrapretty'),
            'description': 'User role and system permissions'
        }),
        (_('Organization'), {
            'fields': ('department', 'position', 'manager', 'board_position'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Organizational structure and position'
        }),
        (_('Security'), {
            'fields': ('mfa_enabled', 'mfa_secret', 'otp_backup_codes', 'mfa_grace_period_end'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Two-factor authentication and security settings'
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Account activity and creation dates'
        }),
    )
    
    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Create new user account'
        }),
        (_('Personal Information'), {
            'fields': ('first_name', 'last_name', 'phone_number', 'profile_photo'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Personal details and contact information'
        }),
        (_('Role & Permissions'), {
            'fields': ('role', 'is_staff', 'is_superuser'),
            'classes': ('wide', 'extrapretty'),
            'description': 'User role and system permissions'
        }),
        (_('Organization'), {
            'fields': ('department', 'position', 'manager', 'board_position'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Organizational structure and position'
        }),
    )
    
    def get_avatar(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" />',
                obj.profile_photo.url
            )
        return format_html(
            '<div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">{}</div>',
            obj.get_full_name()[:2].upper() if obj.get_full_name() else obj.email[:2].upper()
        )
    get_avatar.short_description = 'Avatar'
    
    def get_full_name(self, obj):
        return obj.get_full_name() or f"{obj.first_name} {obj.last_name}".strip() or obj.email
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'
    
    def get_role_badge(self, obj):
        colors = {
            'it_administrator': '#dc3545',
            'company_secretary': '#28a745',
            'executive_management': '#007bff',
            'compliance_officer': '#fd7e14',
            'board_member': '#6f42c1',
            'shareholder': '#20c997',
            'employee': '#6c757d',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{}</span>',
            color, obj.role.replace('_', ' ').title()
        )
    get_role_badge.short_description = 'Role'
    get_role_badge.admin_order_field = 'role'
    
    def get_mfa_status(self, obj):
        if obj.mfa_enabled:
            return mark_safe(
                '<span style="color: #28a745; font-weight: bold;">✓ Enabled</span>'
            )
        return mark_safe(
            '<span style="color: #dc3545; font-weight: bold;">✗ Disabled</span>'
        )
    get_mfa_status.short_description = 'MFA'
    get_mfa_status.admin_order_field = 'mfa_enabled'
    
    def get_last_login(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%b %d, %Y %H:%M')
        return 'Never'
    get_last_login.short_description = 'Last Login'
    get_last_login.admin_order_field = 'last_login'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superusers can only manage regular users
        return qs.filter(is_superuser=False)
    
    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return ['is_superuser', 'user_permissions']
        return []
    
    actions = ['enable_mfa', 'disable_mfa']
    
    def enable_mfa(self, request, queryset):
        updated = queryset.update(mfa_enabled=True)
        self.message_user(request, f'{updated} users had MFA enabled.', level='success')
    enable_mfa.short_description = 'Enable MFA for selected users'
    
    def disable_mfa(self, request, queryset):
        updated = queryset.update(mfa_enabled=False)
        self.message_user(request, f'{updated} users had MFA disabled.', level='warning')
    disable_mfa.short_description = 'Disable MFA for selected users'

# Register User model with default admin site
admin.site.register(User, EnhancedUserAdmin)
