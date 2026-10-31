import re
from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.validators import EmailValidator, ValidationError
from .models import (
    UsageLog,
    UserSettings,
    UserProfile,
    SiteLimit,
    CategoryOverride,
    FocusSession,
    clean_domain
)


def normalize_phone(phone: str) -> str:
    """Strip spaces, dashes, parens from phone strings."""
    return re.sub(r'[\s\-()]+', '', phone.strip())


PERSONA_DEFAULTS = {
    'student': {
        'distracting': ['instagram.com', 'facebook.com', 'reddit.com', 'youtube.com'],
        'productive': ['github.com', 'stackoverflow.com', 'docs.google.com', 'geeksforgeeks.org'],
        'schedule_start': '20:00',
        'schedule_end': '22:30',
    },
    'professional': {
        'distracting': ['instagram.com', 'facebook.com', 'youtube.com', 'x.com'],
        'productive': ['github.com', 'docs.google.com', 'notion.so', 'stackoverflow.com'],
        'schedule_start': '09:00',
        'schedule_end': '12:00',
    },
    'influencer': {
        'distracting': ['facebook.com', 'reddit.com', 'netflix.com', 'x.com'],
        'productive': ['canva.com', 'docs.google.com', 'drive.google.com', 'notion.so'],
        'schedule_start': '14:00',
        'schedule_end': '17:00',
    },
    'creator': {
        'distracting': ['facebook.com', 'reddit.com', 'netflix.com', 'x.com'],
        'productive': ['canva.com', 'figma.com', 'behance.net', 'docs.google.com'],
        'schedule_start': '10:00',
        'schedule_end': '13:00',
    },
    'other': {
        'distracting': ['instagram.com', 'youtube.com', 'facebook.com', 'reddit.com'],
        'productive': ['github.com', 'docs.google.com', 'stackoverflow.com', 'coursera.org'],
        'schedule_start': '19:00',
        'schedule_end': '21:00',
    },
}


def apply_persona_defaults(user, persona: str, keep_user_sites: bool = False):
    """Initializes default distracting/productive lists, limits and suggested focus schedule according to chosen persona."""
    key = (persona or 'student').lower()
    p_def = PERSONA_DEFAULTS.get(key, PERSONA_DEFAULTS['student'])

    settings, _ = UserSettings.objects.get_or_create(user=user)
    
    if keep_user_sites:
        # Collect all default domains from all personas to distinguish user-added sites from default recommendations
        all_default_distracting = set()
        all_default_productive = set()
        for p in PERSONA_DEFAULTS.values():
            all_default_distracting.update(p['distracting']) 
            all_default_productive.update(p['productive'])

        existing_blocked = [clean_domain(s) for s in re.split(r'[\r\n,]+', settings.blocked_sites or '') if clean_domain(s)]
        existing_allowed = [clean_domain(s) for s in re.split(r'[\r\n,]+', settings.allowed_sites or '') if clean_domain(s)]

        # Keep custom sites added by user (sites not belonging to any default list)
        user_added_dist = [d for d in existing_blocked if d not in all_default_distracting]
        user_added_prod = [d for d in existing_allowed if d not in all_default_productive]

        new_blocked = list(dict.fromkeys(p_def['distracting'] + user_added_dist))
        new_allowed = list(dict.fromkeys(p_def['productive'] + user_added_prod))

        settings.blocked_sites = '\n'.join(new_blocked)
        settings.allowed_sites = '\n'.join(new_allowed)
    else:
        if not settings.blocked_sites or not settings.blocked_sites.strip():
            settings.blocked_sites = '\n'.join(p_def['distracting'])
        if not settings.allowed_sites or not settings.allowed_sites.strip():
            settings.allowed_sites = '\n'.join(p_def['productive'])
    
    # Pre-fill suggested schedule times if schedule has not been explicitly configured
    if p_def.get('schedule_start') and (not settings.schedule_start or settings.schedule_start == '20:00'):
        settings.schedule_start = p_def['schedule_start']
    if p_def.get('schedule_end') and (not settings.schedule_end or settings.schedule_end == '22:00'):
        settings.schedule_end = p_def['schedule_end']

    settings.save()

    for domain in p_def['distracting']:
        SiteLimit.objects.get_or_create(
            user=user,
            domain=domain,
            defaults={'daily_limit_minutes': settings.daily_limit_minutes or 60, 'enabled': True}
        )


class RegisterSerializer(serializers.Serializer):
    """
    Flexible registration: accepts username + (email OR phone) + password + persona.
    Username must be alphanumeric/underscores; spaces are converted automatically.
    """
    username = serializers.CharField(max_length=150)
    email    = serializers.EmailField(required=False, allow_blank=True)
    phone    = serializers.CharField(required=False, allow_blank=True, max_length=32)
    password = serializers.CharField(write_only=True, min_length=6)
    persona  = serializers.ChoiceField(
        choices=['student', 'professional', 'influencer', 'creator', 'other'],
        required=False, default='student'
    )

    def validate_username(self, value):
        value = re.sub(r'\s+', '_', value.strip()).lower()
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError('Username may only contain letters, digits, and underscores.')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_email(self, value):
        if value:
            value = value.strip().lower()
            try:
                EmailValidator()(value)
            except ValidationError:
                raise serializers.ValidationError('Please enter a valid email address.')
            if User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate_phone(self, value):
        if value:
            normalized = normalize_phone(value)
            if UserProfile.objects.filter(phone=normalized).exists():
                raise serializers.ValidationError('An account with this phone number already exists.')
            return normalized
        return value

    def create(self, validated_data):
        email   = validated_data.get('email', '') or ''
        phone   = validated_data.get('phone', '') or ''
        persona = validated_data.get('persona', 'student')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=email,
            password=validated_data['password'],
        )

        UserProfile.objects.create(user=user, phone=phone, persona=persona)
        UserSettings.objects.get_or_create(user=user)
        apply_persona_defaults(user, persona)

        return user


class UsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UsageLog
        fields = ('website_url', 'time_spent_seconds', 'date')

    def validate_time_spent_seconds(self, value):
        if value < 0:
            raise serializers.ValidationError('time_spent_seconds must be non-negative.')
        if value > 86_400:
            raise serializers.ValidationError('time_spent_seconds exceeds 24 hours — likely a bug.')
        return value

    def validate_website_url(self, value):
        domain = clean_domain(value)
        if not domain:
            raise serializers.ValidationError('Invalid domain name.')
        return domain


class SiteLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SiteLimit
        fields = ('id', 'domain', 'daily_limit_minutes', 'enabled', 'updated_at')

    def validate_domain(self, value):
        domain = clean_domain(value)
        if not domain:
            raise serializers.ValidationError('Invalid domain name.')
        return domain

    def validate_daily_limit_minutes(self, value):
        if value < 1 or value > 1440:
            raise serializers.ValidationError('Limit must be between 1 and 1440 minutes.')
        return value


class CategoryOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CategoryOverride
        fields = ('id', 'domain', 'category', 'updated_at')

    def validate_domain(self, value):
        domain = clean_domain(value)
        if not domain:
            raise serializers.ValidationError('Invalid domain name.')
        return domain


class FocusSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FocusSession
        fields = ('id', 'duration_minutes', 'started_at', 'completed')


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserSettings
        fields = (
            'focus_mode_active',
            'daily_limit_minutes',
            'focus_goal_minutes',
            'streak_days',
            'require_challenge',
            'blocked_sites',
            'allowed_sites',
            'schedule_enabled',
            'schedule_start',
            'schedule_end',
        )