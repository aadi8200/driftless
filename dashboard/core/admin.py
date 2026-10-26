from django.contrib import admin
from .models import (
    UserProfile,
    UsageLog,
    UserSettings,
    SiteLimit,
    CategoryOverride,
    FocusSession
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'persona', 'phone')
    list_filter = ('persona',)
    search_fields = ('user__username', 'phone')


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'website_url', 'category', 'time_spent_seconds', 'date')
    list_filter   = ('date', 'category')
    search_fields = ('website_url', 'user__username')


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'focus_mode_active', 'daily_limit_minutes', 'focus_goal_minutes', 'streak_days')


@admin.register(SiteLimit)
class SiteLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'domain', 'daily_limit_minutes', 'enabled', 'updated_at')
    list_filter = ('enabled',)
    search_fields = ('domain', 'user__username')


@admin.register(CategoryOverride)
class CategoryOverrideAdmin(admin.ModelAdmin):
    list_display = ('user', 'domain', 'category', 'updated_at')
    list_filter = ('category',)
    search_fields = ('domain', 'user__username')


@admin.register(FocusSession)
class FocusSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'duration_minutes', 'started_at', 'completed')
    list_filter = ('completed', 'duration_minutes')
    search_fields = ('user__username',)