import re
from django.db import models
from django.contrib.auth.models import User


# ─── User Profile & Personas ──────────────────────────────────────────────────
PERSONA_CHOICES = [
    ('student',      'Student'),
    ('professional', 'Professional'),
    ('influencer',   'Influencer'),
    ('creator',      'Creator'),
    ('other',        'Other'),
]


class UserProfile(models.Model):
    """
    Extends the built-in User with phone number and persona.
    Persona presets adjust default limits and domain categories.
    """
    user    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone   = models.CharField(max_length=32, blank=True, default='')
    persona = models.CharField(max_length=20, choices=PERSONA_CHOICES, default='student')

    def __str__(self):
        return f'{self.user.username} ({self.persona})'


# ─── Site Categorisation ──────────────────────────────────────────────────────
CATEGORY_PRODUCTIVITY  = 'Productivity'
CATEGORY_SOCIAL        = 'Social'
CATEGORY_ENTERTAINMENT = 'Entertainment'
CATEGORY_OTHER         = 'Other'

CATEGORY_CHOICES = [
    (CATEGORY_PRODUCTIVITY,  'Productivity'),
    (CATEGORY_SOCIAL,        'Social'),
    (CATEGORY_ENTERTAINMENT, 'Entertainment'),
    (CATEGORY_OTHER,         'Other'),
]

# Static master category mapping as required by Section 2
CATEGORY_MAP = {
    # Productive
    'github.com':         CATEGORY_PRODUCTIVITY,
    'stackoverflow.com':  CATEGORY_PRODUCTIVITY,
    'docs.google.com':    CATEGORY_PRODUCTIVITY,
    'leetcode.com':       CATEGORY_PRODUCTIVITY,
    'geeksforgeeks.org':  CATEGORY_PRODUCTIVITY,
    'coursera.org':       CATEGORY_PRODUCTIVITY,
    'notion.so':          CATEGORY_PRODUCTIVITY,
    'chat.openai.com':    CATEGORY_PRODUCTIVITY,
    'chatgpt.com':        CATEGORY_PRODUCTIVITY,
    'claude.ai':          CATEGORY_PRODUCTIVITY,
    'w3schools.com':      CATEGORY_PRODUCTIVITY,
    'developer.mozilla.org': CATEGORY_PRODUCTIVITY,
    'kaggle.com':         CATEGORY_PRODUCTIVITY,
    'figma.com':          CATEGORY_PRODUCTIVITY,
    'slack.com':          CATEGORY_PRODUCTIVITY,
    'jira.atlassian.com': CATEGORY_PRODUCTIVITY,

    # Social
    'instagram.com':      CATEGORY_SOCIAL,
    'facebook.com':       CATEGORY_SOCIAL,
    'twitter.com':        CATEGORY_SOCIAL,
    'x.com':              CATEGORY_SOCIAL,
    'reddit.com':         CATEGORY_SOCIAL,
    'snapchat.com':       CATEGORY_SOCIAL,
    'tiktok.com':         CATEGORY_SOCIAL,
    'threads.net':        CATEGORY_SOCIAL,
    'linkedin.com':       CATEGORY_SOCIAL,
    'web.whatsapp.com':   CATEGORY_SOCIAL,
    'whatsapp.com':       CATEGORY_SOCIAL,
    'pinterest.com':      CATEGORY_SOCIAL,
    'tumblr.com':         CATEGORY_SOCIAL,
    'mastodon.social':    CATEGORY_SOCIAL,

    # Entertainment
    'youtube.com':        CATEGORY_ENTERTAINMENT,
    'netflix.com':        CATEGORY_ENTERTAINMENT,
    'primevideo.com':     CATEGORY_ENTERTAINMENT,
    'hotstar.com':        CATEGORY_ENTERTAINMENT,
    'twitch.tv':          CATEGORY_ENTERTAINMENT,
    'spotify.com':        CATEGORY_ENTERTAINMENT,
    'disneyplus.com':     CATEGORY_ENTERTAINMENT,
    'crunchyroll.com':    CATEGORY_ENTERTAINMENT,
    'hulu.com':           CATEGORY_ENTERTAINMENT,
    '9gag.com':           CATEGORY_ENTERTAINMENT,
    'buzzfeed.com':       CATEGORY_ENTERTAINMENT,
    'imdb.com':           CATEGORY_ENTERTAINMENT,
    'soundcloud.com':     CATEGORY_ENTERTAINMENT,
}


def clean_domain(domain: str) -> str:
    """Normalize domain: remove protocol, www, port, and trailing paths."""
    if not domain:
        return ''
    d = domain.strip().lower()
    d = re.sub(r'^https?://', '', d)
    d = re.sub(r'^www\.', '', d)
    d = d.split('/')[0].split('?')[0].split(':')[0]
    return d


def classify_domain(domain: str, user=None) -> str:
    """
    Classifies a domain based on:
    1. User's custom CategoryOverride
    2. User persona rules (e.g. Influencers treat instagram/youtube as work/Productivity)
    3. Academic domain pattern (*.edu, *.ac.in) -> Productivity
    4. CATEGORY_MAP dictionary lookup
    5. Fallback -> 'Other' (neutral grey, not counted in productive ratio)
    """
    d = clean_domain(domain)
    if not d:
        return CATEGORY_OTHER

    # 1. User manual override
    if user and user.is_authenticated:
        override = CategoryOverride.objects.filter(user=user, domain=d).first()
        if override:
            return override.category

    # 2. Persona adjustments
    if user and user.is_authenticated:
        profile = getattr(user, 'profile', None)
        if profile and profile.persona == 'influencer':
            if d in {'instagram.com', 'youtube.com', 'tiktok.com', 'threads.net'}:
                return CATEGORY_PRODUCTIVITY
        elif profile and profile.persona == 'professional':
            if d in {'linkedin.com', 'slack.com', 'jira.atlassian.com'}:
                return CATEGORY_PRODUCTIVITY

    # 3. Academic domains
    if d.endswith('.edu') or d.endswith('.ac.in') or '.edu.' in d:
        return CATEGORY_PRODUCTIVITY

    # 4. Global map lookup
    if d in CATEGORY_MAP:
        return CATEGORY_MAP[d]

    # Partial match for subdomains (e.g., lms.harvard.edu)
    for known_domain, cat in CATEGORY_MAP.items():
        if d.endswith('.' + known_domain):
            return cat

    # 5. Default fallback to Other
    return CATEGORY_OTHER


# ─── Category Override Model ──────────────────────────────────────────────────
class CategoryOverride(models.Model):
    """Allows user to customize the category of any domain."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_overrides')
    domain     = models.CharField(max_length=255)
    category   = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'domain')
        ordering        = ['domain']

    def save(self, *args, **kwargs):
        self.domain = clean_domain(self.domain)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} | {self.domain} -> {self.category}'


# ─── Per-Site Limit Model ─────────────────────────────────────────────────────
class SiteLimit(models.Model):
    """
    Per-site daily usage limit in minutes.
    Tracks individual domain limits and enabled status for escalation/blocking.
    """
    user                 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='site_limits')
    domain               = models.CharField(max_length=255)
    daily_limit_minutes  = models.PositiveIntegerField(default=30)
    enabled              = models.BooleanField(default=True)
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'domain')
        ordering        = ['domain']

    def save(self, *args, **kwargs):
        self.domain = clean_domain(self.domain)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} | {self.domain}: {self.daily_limit_minutes}m (enabled={self.enabled})'


# ─── Focus Session Model ──────────────────────────────────────────────────────
class FocusSession(models.Model):
    """Records discrete focus timer blocks (25, 45, 60 mins)."""
    user             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_sessions')
    duration_minutes = models.PositiveIntegerField(default=25)
    started_at       = models.DateTimeField(auto_now_add=True)
    completed        = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.username} | {self.duration_minutes}m on {self.started_at.strftime("%Y-%m-%d %H:%M")}'


# ─── Usage Log Model ──────────────────────────────────────────────────────────
class UsageLog(models.Model):
    """
    Stores the total time (seconds) a user spent on a website on a given date.
    Accumulated throughout the day via periodic extension syncs.
    """
    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_logs')
    website_url        = models.CharField(max_length=255)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    category           = models.CharField(max_length=20, default=CATEGORY_OTHER)
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
        self.website_url = clean_domain(self.website_url)
        if not self.category or self.category == CATEGORY_OTHER:
            self.category = classify_domain(self.website_url, user=self.user)
        super().save(*args, **kwargs)

    def __str__(self):
        mins = self.time_spent_seconds // 60
        return f'{self.user.username} | {self.website_url} | {self.date} | {mins}m ({self.category})'


# ─── User Settings Model ──────────────────────────────────────────────────────
class UserSettings(models.Model):
    """
    User settings synchronized across dashboard and extension.
    """
    user                = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    focus_mode_active   = models.BooleanField(default=False)
    daily_limit_minutes = models.PositiveIntegerField(default=60)
    focus_goal_minutes  = models.PositiveIntegerField(default=180)  # 3-hour daily goal
    streak_days         = models.PositiveIntegerField(default=0)
    require_challenge   = models.BooleanField(default=False)       # Typing challenge to disable focus early
    blocked_sites       = models.TextField(blank=True, default='') # Custom blocked list
    allowed_sites       = models.TextField(blank=True, default='') # Whitelist
    updated_at          = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} settings'