from django.db import models
from django.contrib.auth.models import User


# ─── Site categorisation helpers ──────────────────────────────────────────────
CATEGORY_SOCIAL = 'Social'
CATEGORY_ENTERTAINMENT = 'Entertainment'
CATEGORY_PRODUCTIVITY = 'Productivity'

SOCIAL_DOMAINS = {
    'instagram.com', 'facebook.com', 'twitter.com', 'x.com',
    'reddit.com', 'snapchat.com', 'tiktok.com', 'threads.net',
    'linkedin.com', 'pinterest.com', 'tumblr.com', 'mastodon.social',
}

ENTERTAINMENT_DOMAINS = {
    'youtube.com', 'netflix.com', 'twitch.tv', 'disneyplus.com',
    'primevideo.com', 'hulu.com', 'crunchyroll.com', 'spotify.com',
    'soundcloud.com', '9gag.com', 'buzzfeed.com', 'imdb.com',
}


def classify_domain(domain: str) -> str:
    """Return a category string for a domain."""
    d = domain.strip().lower()
    if d in SOCIAL_DOMAINS:
        return CATEGORY_SOCIAL
    if d in ENTERTAINMENT_DOMAINS:
        return CATEGORY_ENTERTAINMENT
    return CATEGORY_PRODUCTIVITY


class UsageLog(models.Model):
    """
    Stores the total time (seconds) a user spent on a website on a given date.
    The unique_together constraint ensures we accumulate, not duplicate,
    when the extension POSTs multiple times per day.
    """
    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_logs')
    website_url        = models.CharField(max_length=255)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    category           = models.CharField(max_length=20, default=CATEGORY_PRODUCTIVITY)
    date               = models.DateField()
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'website_url', 'date')
        ordering        = ['-date', 'website_url']
        indexes         = [
            models.Index(fields=['user', 'date']),
        ]

    def save(self, *args, **kwargs):
        if not self.category or self.category == CATEGORY_PRODUCTIVITY:
            self.category = classify_domain(self.website_url)
        super().save(*args, **kwargs)

    def __str__(self):
        mins = self.time_spent_seconds // 60
        return f'{self.user.username} | {self.website_url} | {self.date} | {mins}m'


class UserSettings(models.Model):
    """
    Persists dashboard/extension settings so they stay in sync.
    One row per user.
    """
    user                  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    focus_mode_active     = models.BooleanField(default=False)
    daily_limit_minutes   = models.PositiveIntegerField(default=60)
    streak_days           = models.PositiveIntegerField(default=0)
    updated_at            = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} settings'