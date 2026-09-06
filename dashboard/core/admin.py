from django.contrib import admin
from .models import UsageLog

@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'website_url', 'time_spent_seconds', 'date')
    list_filter   = ('date', 'website_url')
    search_fields = ('user__username', 'website_url')
    ordering      = ('-date',)