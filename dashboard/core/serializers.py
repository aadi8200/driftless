from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UsageLog, UserSettings


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


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
        # Strip protocol and www for consistency
        url = value.strip().lower()
        url = url.replace('https://', '').replace('http://', '').lstrip('www.')
        url = url.split('/')[0]
        return url


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserSettings
        fields = ('focus_mode_active', 'daily_limit_minutes', 'streak_days')