import datetime
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from core.models import (
    UserProfile,
    UserSettings,
    UsageLog,
    SiteLimit,
    FocusSession,
    CATEGORY_PRODUCTIVITY,
    CATEGORY_SOCIAL,
    CATEGORY_ENTERTAINMENT,
    CATEGORY_OTHER
)


class Command(BaseCommand):
    help = 'Seeds evaluator demo account (demo@driftless.app) with 14 days of consistent data.'

    def handle(self, *args, **options):
        username = 'demo'
        email = 'demo@driftless.app'
        password = 'demo123456'

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.set_password(password)
        user.save()

        # Token
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        # Profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.persona = 'student'
        profile.save()

        # Clear existing logs & limits for clean seed
        UsageLog.objects.filter(user=user).delete()
        SiteLimit.objects.filter(user=user).delete()
        FocusSession.objects.filter(user=user).delete()

        # UserSettings
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)
        settings_obj.daily_limit_minutes = 45
        settings_obj.focus_goal_minutes  = 180  # 3 hours daily focus goal
        settings_obj.focus_mode_active   = False
        settings_obj.streak_days         = 14   # 14 days clean streak
        settings_obj.save()

        # Site Limits
        limits_config = [
            ('instagram.com', 30),
            ('youtube.com',   45),
            ('reddit.com',    20),
            ('netflix.com',   40),
        ]
        for domain, limit_mins in limits_config:
            SiteLimit.objects.create(
                user=user,
                domain=domain,
                daily_limit_minutes=limit_mins,
                enabled=True
            )

        today = datetime.date.today()

        # 14 days of realistic usage data
        # Sites with their categories and typical minutes range
        productive_sites = [
            ('github.com', 45, 90),
            ('leetcode.com', 30, 60),
            ('docs.google.com', 20, 45),
            ('notion.so', 25, 50),
            ('stackoverflow.com', 15, 30),
        ]
        social_sites = [
            ('instagram.com', 10, 25), # Always strictly < 30m limit
            ('reddit.com', 5, 15),     # Always strictly < 20m limit
        ]
        entertainment_sites = [
            ('youtube.com', 15, 35),   # Always strictly < 45m limit
        ]
        other_sites = [
            ('wikipedia.org', 10, 20),
            ('medium.com', 8, 18),
        ]

        random.seed(42) # Consistent realistic data

        for day_offset in range(13, -1, -1):
            log_date = today - datetime.timedelta(days=day_offset)

            # Seed Productive
            for domain, min_m, max_m in productive_sites:
                mins = random.randint(min_m, max_m)
                UsageLog.objects.create(
                    user=user,
                    website_url=domain,
                    time_spent_seconds=mins * 60,
                    category=CATEGORY_PRODUCTIVITY,
                    date=log_date
                )

            # Seed Social
            for domain, min_m, max_m in social_sites:
                mins = random.randint(min_m, max_m)
                UsageLog.objects.create(
                    user=user,
                    website_url=domain,
                    time_spent_seconds=mins * 60,
                    category=CATEGORY_SOCIAL,
                    date=log_date
                )

            # Seed Entertainment
            for domain, min_m, max_m in entertainment_sites:
                mins = random.randint(min_m, max_m)
                UsageLog.objects.create(
                    user=user,
                    website_url=domain,
                    time_spent_seconds=mins * 60,
                    category=CATEGORY_ENTERTAINMENT,
                    date=log_date
                )

            # Seed Other
            for domain, min_m, max_m in other_sites:
                mins = random.randint(min_m, max_m)
                UsageLog.objects.create(
                    user=user,
                    website_url=domain,
                    time_spent_seconds=mins * 60,
                    category=CATEGORY_OTHER,
                    date=log_date
                )

            # 1 to 2 completed focus sessions per day
            num_sessions = random.choice([1, 2])
            for _ in range(num_sessions):
                dur = random.choice([25, 45, 50])
                FocusSession.objects.create(
                    user=user,
                    duration_minutes=dur,
                    started_at=datetime.datetime.combine(log_date, datetime.time(random.randint(9, 17), 0)),
                    completed=True
                )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded demo account!\n'
            f'Username: {username}\n'
            f'Email:    {email}\n'
            f'Password: {password}\n'
            f'Token:    {token.key}\n'
            f'History:  14 days of realistic, consistent data generated with 14-day streak.'
        ))
