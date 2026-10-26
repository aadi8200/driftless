import re
from rest_framework import serializers
from django.contrib.auth.models import User
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


def apply_persona_defaults(user, persona: str):
    """Initializes default site limits according to the chosen persona."""
    persona_limits = {
        'student': [
            ('instagram.com', 30),
            ('youtube.com', 45),
            ('reddit.com', 20),
            ('netflix.com', 40),
        ],
        'professional': [
            ('twitter.com', 20),
            ('x.com', 20),
            ('instagram.com', 15),
            ('youtube.com', 30),
            ('reddit.com', 15),
        ],
        'influencer': [
            ('netflix.com', 30),
            ('twitch.tv', 25),
            ('reddit.com', 20),
        ],
        'creator': [
            ('instagram.com', 45),
            ('youtube.com', 60),
            ('reddit.com', 20),
            ('netflix.com', 30),
        ],
        'other': [
            ('instagram.com', 30),
            ('youtube.com', 45),
            ('reddit.com', 20),
        ],
    }

    limits_to_apply = persona_limits.get(persona, persona_limits['student'])
    for domain, mins in limits_to_apply:
        SiteLimit.objects.get_or_create(
            user=user,
            domain=domain,
            defaults={'daily_limit_minutes': mins, 'enabled': True}
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
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value.lower() if value else value

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
            'allowed_sites'
        )