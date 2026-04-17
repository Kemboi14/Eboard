import uuid
import zoneinfo

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Common timezones for the regions Enwealth operates in
TIMEZONE_CHOICES = sorted(
    [
        ("Africa/Nairobi", "Kenya / Uganda / Tanzania (EAT, UTC+3)"),
        ("Africa/Kampala", "Uganda (EAT, UTC+3)"),
        ("Indian/Mauritius", "Mauritius (MUT, UTC+4)"),
        ("Africa/Johannesburg", "South Africa (SAST, UTC+2)"),
        ("Africa/Lagos", "Nigeria (WAT, UTC+1)"),
        ("Africa/Accra", "Ghana (GMT, UTC+0)"),
        ("Africa/Cairo", "Egypt (EET, UTC+2)"),
        ("Europe/London", "United Kingdom (GMT/BST)"),
        ("Europe/Paris", "France / CET (UTC+1)"),
        ("Asia/Dubai", "UAE (GST, UTC+4)"),
        ("Asia/Kolkata", "India (IST, UTC+5:30)"),
        ("UTC", "UTC"),
    ],
    key=lambda x: x[1],
)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("board_member", "Board Member"),
        ("company_secretary", "Company Secretary"),
        ("executive_management", "Executive Management"),
        ("compliance_officer", "Compliance Officer"),
        ("it_administrator", "IT Administrator"),
        ("internal_audit", "Internal Audit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to="profiles/", null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    preferred_timezone = models.CharField(
        max_length=60,
        choices=TIMEZONE_CHOICES,
        default="Africa/Nairobi",
        help_text="Your local timezone — meeting times will be displayed in this timezone.",
    )
    preferred_language = models.CharField(
        max_length=10,
        default="en",
        help_text="Your preferred language for the interface",
    )

    # Director profile fields
    bio = models.TextField(blank=True, help_text="Professional biography and background")
    education = models.TextField(blank=True, help_text="Educational qualifications")
    experience = models.TextField(blank=True, help_text="Professional experience")
    expertise = models.TextField(blank=True, help_text="Areas of expertise")
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL")
    other_credentials = models.TextField(blank=True, help_text="Other professional credentials and certifications")
    board_tenure_start = models.DateField(null=True, blank=True, help_text="Date when board tenure started")
    board_position = models.CharField(max_length=100, blank=True, help_text="Specific position on the board")

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "auth_user"

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_timezone(self):
        """Return a zoneinfo.ZoneInfo object for this user's preferred timezone."""
        try:
            return zoneinfo.ZoneInfo(self.preferred_timezone)
        except (zoneinfo.ZoneInfoNotFoundError, Exception):
            return zoneinfo.ZoneInfo("Africa/Nairobi")

    def localise_dt(self, dt):
        """Convert a UTC-aware datetime to this user's local timezone."""
        from django.utils import timezone as dj_tz

        if dt is None:
            return None
        if dj_tz.is_naive(dt):
            dt = dj_tz.make_aware(dt, zoneinfo.ZoneInfo("UTC"))
        return dt.astimezone(self.get_timezone())

    @property
    def board_tenure_years(self):
        """Calculate years of board tenure"""
        if self.board_tenure_start:
            from django.utils import timezone
            years = (timezone.now().date() - self.board_tenure_start).days / 365.25
            return round(years, 1)
        return 0


class PasswordHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_history"
    )
    password_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.created_at}"


class SSOProvider(models.Model):
    """Single Sign-On provider configuration"""

    PROVIDER_CHOICES = [
        ('okta', 'Okta'),
        ('azure_ad', 'Azure Active Directory'),
        ('google', 'Google Workspace'),
        ('auth0', 'Auth0'),
        ('keycloak', 'Keycloak'),
        ('ping', 'Ping Identity'),
        ('saml', 'Generic SAML'),
        ('oidc', 'Generic OIDC'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('disabled', 'Disabled'),
        ('testing', 'Testing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Provider details
    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disabled')
    
    # SAML Configuration
    saml_entity_id = models.CharField(max_length=255, blank=True, help_text="Entity ID for SAML")
    saml_sso_url = models.URLField(blank=True, help_text="SSO URL for SAML")
    saml_slo_url = models.URLField(blank=True, help_text="SLO URL for SAML")
    saml_certificate = models.TextField(blank=True, help_text="X.509 certificate")
    saml_metadata_url = models.URLField(blank=True, help_text="Metadata URL")
    
    # OIDC Configuration
    oidc_client_id = models.CharField(max_length=255, blank=True)
    oidc_client_secret = models.CharField(max_length=255, blank=True)
    oidc_issuer_url = models.URLField(blank=True)
    oidc_authorization_endpoint = models.URLField(blank=True)
    oidc_token_endpoint = models.URLField(blank=True)
    oidc_userinfo_endpoint = models.URLField(blank=True)
    oidc_jwks_uri = models.URLField(blank=True)
    
    # Mapping configuration
    email_attribute = models.CharField(max_length=100, default='email', help_text="Attribute name for email")
    first_name_attribute = models.CharField(max_length=100, default='given_name', help_text="Attribute name for first name")
    last_name_attribute = models.CharField(max_length=100, default='family_name', help_text="Attribute name for last name")
    role_attribute = models.CharField(max_length=100, blank=True, help_text="Attribute name for role")
    
    # Role mapping (JSON: {"admin": ["board_member", "it_administrator"], ...})
    role_mapping = models.JSONField(null=True, blank=True, help_text="Map SSO roles to system roles")
    
    # Auto-provisioning
    auto_provision_users = models.BooleanField(default=True, help_text="Automatically create users on first login")
    default_role = models.CharField(max_length=50, blank=True, help_text="Default role for auto-provisioned users")
    
    # Security
    require_encryption = models.BooleanField(default=True)
    allowed_domains = models.TextField(blank=True, help_text="Comma-separated list of allowed email domains")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sso_providers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'SSO Provider'
        verbose_name_plural = 'SSO Providers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['provider_type', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


class UserSSOIdentity(models.Model):
    """Link between user and SSO identity"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sso_identities')
    provider = models.ForeignKey(SSOProvider, on_delete=models.CASCADE, related_name='user_identities')
    
    # SSO identity
    external_id = models.CharField(max_length=255, help_text="External user ID from SSO provider")
    external_username = models.CharField(max_length=255, blank=True)
    external_email = models.EmailField(blank=True)
    
    # SSO attributes
    attributes = models.JSONField(null=True, blank=True, help_text="Additional attributes from SSO")
    
    # Metadata
    first_login = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User SSO Identity'
        verbose_name_plural = 'User SSO Identities'
        ordering = ['-last_login_at']
        unique_together = [['provider', 'external_id']]
        indexes = [
            models.Index(fields=['user', 'provider']),
            models.Index(fields=['provider', 'external_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.provider.name}"


class UserSession(models.Model):
    """Track user sessions for concurrent login limits"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('logout', 'Logged Out'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    
    # Session details
    session_key = models.CharField(max_length=255, unique=True, help_text="Django session key")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Device info
    device_type = models.CharField(max_length=50, blank=True, help_text="e.g., desktop, mobile, tablet")
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Location (optional, from IP geolocation)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Timestamps
    login_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    
    # Security
    is_suspicious = models.BooleanField(default=False, help_text="Flagged as potentially suspicious")
    risk_score = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['status', '-last_activity']),
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.login_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_active(self):
        """Check if session is currently active"""
        if self.status != 'active':
            return False
        # Check if session has expired (24 hours of inactivity)
        if timezone.now() - self.last_activity > timezone.timedelta(hours=24):
            return False
        return True
    
    def terminate(self):
        """Terminate the session"""
        self.status = 'terminated'
        self.logout_at = timezone.now()
        self.save(update_fields=['status', 'logout_at'])


class EncryptionKey(models.Model):
    """Manage encryption keys for data encryption at rest"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('rotating', 'Rotating'),
        ('deprecated', 'Deprecated'),
        ('revoked', 'Revoked'),
    ]

    KEY_TYPE_CHOICES = [
        ('aes256', 'AES-256-GCM'),
        ('rsa4096', 'RSA-4096'),
        ('chacha20', 'ChaCha20-Poly1305'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Key details
    name = models.CharField(max_length=100, help_text="Friendly name for the key")
    key_type = models.CharField(max_length=20, choices=KEY_TYPE_CHOICES, default='aes256')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Key storage (encrypted at rest in database)
    encrypted_key = models.TextField(help_text="Encrypted key material")
    key_fingerprint = models.CharField(max_length=64, unique=True, help_text="SHA-256 fingerprint of the key")
    
    # Rotation
    rotation_interval_days = models.PositiveIntegerField(default=90, help_text="Days between key rotations")
    last_rotated_at = models.DateTimeField(auto_now_add=True)
    next_rotation_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_encryption_keys')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Encryption Key'
        verbose_name_plural = 'Encryption Keys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['key_type']),
            models.Index(fields=['next_rotation_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_key_type_display()})"
    
    @property
    def needs_rotation(self):
        """Check if key needs rotation"""
        if self.status != 'active':
            return False
        if self.next_rotation_at and timezone.now() >= self.next_rotation_at:
            return True
        return False


class Language(models.Model):
    """Supported languages for the platform"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('beta', 'Beta'),
        ('disabled', 'Disabled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Language details
    code = models.CharField(max_length=10, unique=True, help_text="ISO 639-1 language code (e.g., en, fr, sw)")
    name = models.CharField(max_length=100, help_text="Language name in English")
    native_name = models.CharField(max_length=100, help_text="Language name in the language itself")
    
    # Locale
    locale_code = models.CharField(max_length=20, help_text="Locale code (e.g., en_US, fr_FR, sw_KE)")
    
    # Direction
    direction = models.CharField(max_length=3, choices=[('ltr', 'LTR'), ('rtl', 'RTL')], default='ltr')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Translation coverage
    translation_coverage = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Percentage of strings translated")
    
    # Flag emoji (optional)
    flag_emoji = models.CharField(max_length=10, blank=True, help_text="Flag emoji (e.g., 🇺🇸, 🇫🇷, 🇰🇪)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.native_name} ({self.code})"


class Translation(models.Model):
    """Translation strings for multi-language support"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Key for the translation
    key = models.CharField(max_length=500, help_text="Translation key (e.g., common.button.submit)")
    
    # Context
    context = models.CharField(max_length=200, blank=True, help_text="Context for the translation")
    module = models.CharField(max_length=100, blank=True, help_text="Module/app this belongs to")
    
    # Translations (JSON: {"en": "Submit", "fr": "Soumettre", "sw": "Wasilisha"})
    translations = models.JSONField(default=dict, help_text="Language code to translation mapping")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Translation'
        verbose_name_plural = 'Translations'
        ordering = ['key']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['module']),
        ]
    
    def __str__(self):
        return f"{self.key}"
    
    def get_translation(self, language_code, default=None):
        """Get translation for a specific language"""
        return self.translations.get(language_code, default or self.key)
