import re
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
    Extends the built-in User with phone number, persona, and gamification level & badges.
    Persona presets adjust default limits and domain categories.
    """
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone       = models.CharField(max_length=32, blank=True, default='')
    persona     = models.CharField(max_length=20, choices=PERSONA_CHOICES, default='student')
    is_verified = models.BooleanField(default=True)  # True by default so existing users are never locked out

    # Gamification: Level, XP & Badges
    xp              = models.IntegerField(default=0)
    level           = models.IntegerField(default=1)
    has_zen_master  = models.BooleanField(default=False)
    has_deep_worker = models.BooleanField(default=False)
    has_iron_will   = models.BooleanField(default=False)

    def seed_demo_gamification(self, force=False):
        """Pre-seeds Level 5, 80% XP progress, and all 3 presentation badges."""
        if force or (self.level <= 1 and self.xp == 0):
            self.level = 5
            self.xp = 80
            self.has_zen_master = True
            self.has_deep_worker = True
            self.has_iron_will = True
            self.save(update_fields=['level', 'xp', 'has_zen_master', 'has_deep_worker', 'has_iron_will'])
        return self

    def __str__(self):
        return f'{self.user.username} (Lvl {self.level}, {self.persona})'


# ─── Site Categorisation ──────────────────────────────────────────────────────
CATEGORY_PRODUCTIVE   = 'Productive sites'
CATEGORY_DISTRACTING  = 'Distracting sites'
CATEGORY_OTHERS       = 'Others'

# Backward compatibility aliases
CATEGORY_PRODUCTIVITY  = CATEGORY_PRODUCTIVE
CATEGORY_SOCIAL        = CATEGORY_DISTRACTING
CATEGORY_ENTERTAINMENT = CATEGORY_DISTRACTING
CATEGORY_OTHER         = CATEGORY_OTHERS

CATEGORY_CHOICES = [
    (CATEGORY_PRODUCTIVE,   'Productive sites'),
    (CATEGORY_DISTRACTING,  'Distracting sites'),
    (CATEGORY_OTHERS,       'Others'),
]

# Static master category mapping
CATEGORY_MAP = {
    # Productive
    'github.com':            CATEGORY_PRODUCTIVE,
    'stackoverflow.com':     CATEGORY_PRODUCTIVE,
    'docs.google.com':       CATEGORY_PRODUCTIVE,
    'leetcode.com':          CATEGORY_PRODUCTIVE,
    'geeksforgeeks.org':     CATEGORY_PRODUCTIVE,
    'coursera.org':          CATEGORY_PRODUCTIVE,
    'notion.so':             CATEGORY_PRODUCTIVE,
    'canva.com':             CATEGORY_PRODUCTIVE,
    'figma.com':             CATEGORY_PRODUCTIVE,
    'behance.net':           CATEGORY_PRODUCTIVE,
    'drive.google.com':      CATEGORY_PRODUCTIVE,
    'chat.openai.com':       CATEGORY_PRODUCTIVE,
    'chatgpt.com':           CATEGORY_PRODUCTIVE,
    'claude.ai':             CATEGORY_PRODUCTIVE,
    'w3schools.com':         CATEGORY_PRODUCTIVE,
    'developer.mozilla.org': CATEGORY_PRODUCTIVE,
    'kaggle.com':            CATEGORY_PRODUCTIVE,
    'slack.com':             CATEGORY_PRODUCTIVE,
    'jira.atlassian.com':    CATEGORY_PRODUCTIVE,

    # Distracting (Social & Entertainment)
    'instagram.com':         CATEGORY_DISTRACTING,
    'facebook.com':          CATEGORY_DISTRACTING,
    'twitter.com':           CATEGORY_DISTRACTING,
    'x.com':                 CATEGORY_DISTRACTING,
    'reddit.com':            CATEGORY_DISTRACTING,
    'snapchat.com':          CATEGORY_DISTRACTING,
    'tiktok.com':            CATEGORY_DISTRACTING,
    'threads.net':           CATEGORY_DISTRACTING,
    'web.whatsapp.com':      CATEGORY_DISTRACTING,
    'whatsapp.com':          CATEGORY_DISTRACTING,
    'pinterest.com':         CATEGORY_DISTRACTING,
    'tumblr.com':            CATEGORY_DISTRACTING,
    'mastodon.social':       CATEGORY_DISTRACTING,
    'youtube.com':           CATEGORY_DISTRACTING,
    'netflix.com':           CATEGORY_DISTRACTING,
    'primevideo.com':        CATEGORY_DISTRACTING,
    'hotstar.com':           CATEGORY_DISTRACTING,
    'twitch.tv':             CATEGORY_DISTRACTING,
    'spotify.com':           CATEGORY_DISTRACTING,
    'disneyplus.com':        CATEGORY_DISTRACTING,
    'crunchyroll.com':       CATEGORY_DISTRACTING,
    'hulu.com':              CATEGORY_DISTRACTING,
    '9gag.com':              CATEGORY_DISTRACTING,
    'buzzfeed.com':          CATEGORY_DISTRACTING,
    'imdb.com':              CATEGORY_DISTRACTING,
    'soundcloud.com':        CATEGORY_DISTRACTING,
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
    Classifies a domain into exactly three categories:
    1. Productive sites
    2. Distracting sites
    3. Others

    Decision hierarchy:
    1. User's custom CategoryOverride (supports new and legacy category names)
    2. User's popup/dashboard lists:
       - Whitelisted work sites (allowed_sites) -> Productive sites
       - Distracting sites (blocked_sites) -> Distracting sites
    3. Academic domain pattern (*.edu, *.ac.in) -> Productive sites
    4. CATEGORY_MAP dictionary lookup
    5. Fallback -> Others
    """
    d = clean_domain(domain)
    if not d:
        return CATEGORY_OTHERS

    # 1. User manual override
    if user and user.is_authenticated:
        override = CategoryOverride.objects.filter(user=user, domain=d).first()
        if override:
            cat = override.category
            if cat in ('Productivity', 'Productive', CATEGORY_PRODUCTIVE):
                return CATEGORY_PRODUCTIVE
            elif cat in ('Social', 'Entertainment', 'Distracting', CATEGORY_DISTRACTING):
                return CATEGORY_DISTRACTING
            return CATEGORY_OTHERS

    # 2. User's popup & dashboard lists
    if user and user.is_authenticated:
        settings = getattr(user, 'settings', None)
        if settings:
            allowed = [clean_domain(s) for s in re.split(r'[\r\n,]+', settings.allowed_sites) if clean_domain(s)]
            blocked = [clean_domain(s) for s in re.split(r'[\r\n,]+', settings.blocked_sites) if clean_domain(s)]
            if d in allowed:
                return CATEGORY_PRODUCTIVE
            if d in blocked:
                return CATEGORY_DISTRACTING

    # 3. Academic domains
    if d.endswith('.edu') or d.endswith('.ac.in') or '.edu.' in d:
        return CATEGORY_PRODUCTIVE

    # 4. Global map lookup
    if d in CATEGORY_MAP:
        return CATEGORY_MAP[d]

    # Partial match for subdomains (e.g., lms.harvard.edu)
    for known_domain, cat in CATEGORY_MAP.items():
        if d.endswith('.' + known_domain):
            return cat

    # 5. Fallback to Others
    return CATEGORY_OTHERS


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
    schedule_enabled    = models.BooleanField(default=False)
    schedule_start      = models.CharField(max_length=5, default='20:00') # HH:MM (24h)
    schedule_end        = models.CharField(max_length=5, default='22:00') # HH:MM (24h)
    updated_at          = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} settings'

