from django.contrib import admin
from .models import UsageLog, UserSettings


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'website_url', 'category', 'time_spent_seconds', 'date')
    list_filter   = ('date', 'category')
    search_fields = ('website_url', 'user__username')


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'focus_mode_active', 'daily_limit_minutes', 'streak_days')