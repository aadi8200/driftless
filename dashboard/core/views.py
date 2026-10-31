import datetime
import json
import logging
import re
import urllib.request
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.validators import EmailValidator, ValidationError
from django.db.models import Sum, Max
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import (
    UsageLog,
    UserSettings,
    UserProfile,
    SiteLimit,
    CategoryOverride,
    FocusSession,
    classify_domain,
    clean_domain,
    CATEGORY_PRODUCTIVE,
    CATEGORY_DISTRACTING,
    CATEGORY_OTHERS,
    CATEGORY_PRODUCTIVITY,
    CATEGORY_SOCIAL,
    CATEGORY_ENTERTAINMENT,
    CATEGORY_OTHER
)
from .serializers import (
    RegisterSerializer,
    UsageLogSerializer,
    UserSettingsSerializer,
    SiteLimitSerializer,
    CategoryOverrideSerializer,
    FocusSessionSerializer,
    apply_persona_defaults
)


class SyncRateThrottle(UserRateThrottle):
    rate = '120/min'


# ─────────────────────────────────────────────────────────────────────────────
# PAGE VIEWS
# ─────────────────────────────────────────────────────────────────────────────

def auth_page(request):
    """Serves the unified Login / Sign-Up page."""
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return render(request, 'auth.html', {
        'google_client_id': getattr(settings, 'GOOGLE_CLIENT_ID', '')
    })


@login_required
def dashboard_page(request):
    """Serves the analytics dashboard (requires session login)."""
    token, _ = Token.objects.get_or_create(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.seed_demo_gamification()
    xp_progress = 80 if (profile.level == 5 and profile.xp == 80) else (profile.xp % 100)
    return render(request, 'dashboard.html', {
        'api_token': token.key,
        'username': request.user.username,
        'persona': profile.persona,
        'level': profile.level,
        'xp': profile.xp,
        'xp_progress': xp_progress,
        'has_zen_master': profile.has_zen_master,
        'has_deep_worker': profile.has_deep_worker,
        'has_iron_will': profile.has_iron_will,
    })


# ─────────────────────────────────────────────────────────────────────────────
# AUTH API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def google_auth_view(request):
    """
    POST /api/auth/google/
    Body: { credential } OR { email, name, demo: true }
    Handles Google Identity Services / One-Tap and Quick Demo Google Sign-In.
    Auto-creates/logs in user, marks is_verified=True, returns DRF Token.
    """
    credential = request.data.get('credential')
    demo = request.data.get('demo', False)
    email = None
    name = None

    # 1. Real Google ID token verification
    if credential and not demo:
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Driftless-Server'})
            with urllib.request.urlopen(req, timeout=6) as response:
                payload = json.loads(response.read().decode('utf-8'))
                if client_id and payload.get('aud') != client_id:
                    return Response({'error': 'Invalid Google token audience.'}, status=status.HTTP_400_BAD_REQUEST)
                email = payload.get('email', '').strip().lower()
                name = payload.get('name', '').strip()
        except Exception as e:
            logger.error("Google token verification failed: %s", e)
            return Response({'error': f'Google token verification failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # 2. Interactive Demo Mode selection
        email = (request.data.get('email') or '').strip().lower()
        name = (request.data.get('name') or '').strip()

    if not email or '@' not in email:
        return Response({'error': 'A valid Google email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve or create user
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0]) or 'driftless_user'
        username = base_username
        idx = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base_username}_{idx}"
            idx += 1

        first_name = name.split(' ')[0] if name else ''
        last_name = ' '.join(name.split(' ')[1:]) if name and ' ' in name else ''
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_unusable_password()
        user.save()

    # Mark profile as verified and seed presentation gamification
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_verified = True
    profile.seed_demo_gamification()
    profile.save()

    # Ensure settings and defaults
    UserSettings.objects.get_or_create(user=user)
    apply_persona_defaults(user, profile.persona or 'student')

    token, _ = Token.objects.get_or_create(user=user)
    login(request, user)

    return Response({
        'success': True,
        'token': token.key,
        'username': user.username,
        'redirect': '/dashboard/'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def register_view(request):
    """
    POST /api/auth/register/
    Body: { username, email?, phone?, password, persona? }
    Streamlined manual signup with strict EmailValidator backend validation.
    Immediately creates user, sets is_verified=True, logs in, and returns redirect to /dashboard/.
    """
    email = (request.data.get('email') or '').strip().lower()
    if email:
        try:
            EmailValidator()(email)
        except ValidationError:
            return Response({'error': 'Please enter a valid email address.', 'email': ['Please enter a valid email address.']}, status=status.HTTP_400_BAD_REQUEST)

    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_verified = True
        profile.seed_demo_gamification()
        profile.save()

        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response({
            'success': True,
            'token': token.key,
            'username': user.username,
            'is_verified': True,
            'redirect': '/dashboard/'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/auth/login/
    Body: { username|email|phone, password }
    """
    identifier = (
        request.data.get('username') or
        request.data.get('email')    or
        request.data.get('phone')    or ''
    ).strip()
    password = request.data.get('password', '')

    if not identifier or not password:
        return Response({'error': 'Identifier and password are required.'},
                        status=status.HTTP_400_BAD_REQUEST)

    resolved_username = None

    if '@' in identifier:
        try:
            resolved_username = User.objects.get(email__iexact=identifier).username
        except User.DoesNotExist:
            pass
    elif re.match(r'^[+]?\d[\d\s\-()]{8,}$', identifier):
        normalized = re.sub(r'[\s\-()]+', '', identifier)
        try:
            resolved_username = UserProfile.objects.get(phone=normalized).user.username
        except UserProfile.DoesNotExist:
            pass
    else:
        resolved_username = identifier

    if not resolved_username:
        return Response({'error': 'No account found with that identifier.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(request, username=resolved_username, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials. Please check your password.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    token, _ = Token.objects.get_or_create(user=user)
    login(request, user)
    return Response({'token': token.key, 'username': user.username})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /api/auth/logout/ — deletes user auth token & logs out session."""
    if hasattr(request.user, 'auth_token'):
        request.user.auth_token.delete()
    logout(request)
    return Response({'detail': 'Logged out.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_token_view(request):
    """POST /api/auth/regenerate-token/ — replaces current token with a fresh one."""
    if hasattr(request.user, 'auth_token'):
        request.user.auth_token.delete()
    new_token = Token.objects.create(user=request.user)
    return Response({'token': new_token.key})


# ─────────────────────────────────────────────────────────────────────────────
# USAGE LOG API
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([SyncRateThrottle])
def usage_log_view(request):
    """
    POST /api/usage/
    Accepts single usage log or batch list. Increments time_spent_seconds.
    """
    data = request.data
    many = isinstance(data, list)

    serializer = UsageLogSerializer(data=data, many=many)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    entries = serializer.validated_data if many else [serializer.validated_data]
    created_count = updated_count = 0

    for entry in entries:
        domain = entry['website_url']
        category = classify_domain(domain, user=request.user)
        
        obj, created = UsageLog.objects.get_or_create(
            user        = request.user,
            website_url = domain,
            date        = entry['date'],
            defaults    = {
                'time_spent_seconds': 0,
                'category': category,
            },
        )
        obj.time_spent_seconds += entry['time_spent_seconds']
        obj.category = category  # ensure latest category classification
        obj.save(update_fields=['time_spent_seconds', 'category', 'updated_at'])
        if created:
            created_count += 1
        else:
            updated_count += 1

    return Response(
        {'created': created_count, 'updated': updated_count},
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY API — used by Dashboard & Extension Popup
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def summary_view(request):
    """
    GET /api/summary/
    Unified payload providing stats, weekly/daily breakdowns, focus efficiency,
    site limits, focus sessions, and user settings.
    """
    today    = datetime.date.today()
    week_ago = today - datetime.timedelta(days=6)

    user_logs = UsageLog.objects.filter(user=request.user)
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.seed_demo_gamification()
    xp_progress = 80 if (profile.level == 5 and profile.xp == 80) else (profile.xp % 100)

    # Auto-populate recommended site lists from user persona if unseeded
    has_blocked = bool(settings_obj.blocked_sites and settings_obj.blocked_sites.strip())
    has_allowed = bool(settings_obj.allowed_sites and settings_obj.allowed_sites.strip())
    if not has_blocked and not has_allowed:
        apply_persona_defaults(request.user, getattr(profile, 'persona', 'student'))
        settings_obj.refresh_from_db()

    # ── Weekly: per-day per-category totals (Productive, Distracting, Others) ─
    weekly_qs = (
        user_logs
        .filter(date__gte=week_ago, date__lte=today)
        .values('date', 'website_url', 'time_spent_seconds')
        .order_by('date')
    )

    weekly_map = {}
    for row in weekly_qs:
        d = row['date'].isoformat()
        if d not in weekly_map:
            weekly_map[d] = {
                CATEGORY_PRODUCTIVE: 0,
                CATEGORY_DISTRACTING: 0,
                CATEGORY_OTHERS: 0,
            }
        cat = classify_domain(row['website_url'], user=request.user)
        if cat in (CATEGORY_PRODUCTIVE, 'Productivity'):
            weekly_map[d][CATEGORY_PRODUCTIVE] += row['time_spent_seconds']
        elif cat in (CATEGORY_DISTRACTING, 'Social', 'Entertainment'):
            weekly_map[d][CATEGORY_DISTRACTING] += row['time_spent_seconds']
        else:
            weekly_map[d][CATEGORY_OTHERS] += row['time_spent_seconds']

    weekly = []
    for i in range(7):
        d = (week_ago + datetime.timedelta(days=i)).isoformat()
        cats = weekly_map.get(d, {
            CATEGORY_PRODUCTIVE: 0,
            CATEGORY_DISTRACTING: 0,
            CATEGORY_OTHERS: 0,
        })
        p_sec = cats.get(CATEGORY_PRODUCTIVE, 0)
        dist_sec = cats.get(CATEGORY_DISTRACTING, 0)
        oth_sec = cats.get(CATEGORY_OTHERS, 0)
        weekly.append({
            'date': d,
            'total_seconds': p_sec + dist_sec + oth_sec,
            'productive_seconds':  p_sec,
            'distracting_seconds': dist_sec,
            'others_seconds':      oth_sec,
            # Backward-compatibility aliases
            'productivity_seconds':  p_sec,
            'social_seconds':        dist_sec,
            'entertainment_seconds': 0,
            'other_seconds':         oth_sec,
        })

    # ── Daily: breakdown by site for today ────────────────────────────────────
    daily_qs = (
        user_logs
        .filter(date=today)
        .values('website_url')
        .annotate(total_seconds=Sum('time_spent_seconds'))
        .order_by('-total_seconds')
    )
    daily = [{
        'website_url':   r['website_url'],
        'total_seconds': r['total_seconds'],
        'category':      classify_domain(r['website_url'], user=request.user),
    } for r in daily_qs]

    # ── Stats & Focus Efficiency ──────────────────────────────────────────────
    today_total         = sum(r['total_seconds'] for r in daily)
    top_site            = daily[0]['website_url'] if daily else None
    productive_seconds  = sum(r['total_seconds'] for r in daily if r['category'] == CATEGORY_PRODUCTIVE)
    distracting_seconds = sum(r['total_seconds'] for r in daily if r['category'] == CATEGORY_DISTRACTING)
    others_seconds      = sum(r['total_seconds'] for r in daily if r['category'] == CATEGORY_OTHERS)

    denominator = productive_seconds + distracting_seconds
    if denominator > 0:
        focus_efficiency = round((productive_seconds / denominator) * 100)
    elif today_total > 0:
        focus_efficiency = round((productive_seconds / today_total) * 100)
    else:
        focus_efficiency = 0

    # ── Strict Streak Calculation ─────────────────────────────────────────────
    # A day counts towards streak ONLY if no site exceeded its limit.
    limits_dict = {
        l.domain: l.daily_limit_minutes * 60
        for l in SiteLimit.objects.filter(user=request.user, enabled=True)
    }
    global_limit_sec = settings_obj.daily_limit_minutes * 60

    streak = 0
    check_date = today - datetime.timedelta(days=1)
    
    while True:
        day_logs = user_logs.filter(date=check_date)
        if not day_logs.exists():
            break

        day_failed = False
        for log in day_logs:
            cat = classify_domain(log.website_url, user=request.user)
            site_limit = limits_dict.get(log.website_url, None)
            if site_limit is not None and log.time_spent_seconds > site_limit:
                day_failed = True
                break
            elif site_limit is None and cat == CATEGORY_DISTRACTING:
                if log.time_spent_seconds > global_limit_sec:
                    day_failed = True
                    break

        if day_failed:
            break
        else:
            streak += 1
            check_date -= datetime.timedelta(days=1)

    # Check today's status
    today_logs = user_logs.filter(date=today)
    today_exceeded = False
    if today_logs.exists():
        for log in today_logs:
            cat = classify_domain(log.website_url, user=request.user)
            site_limit = limits_dict.get(log.website_url, None)
            if site_limit is not None and log.time_spent_seconds > site_limit:
                today_exceeded = True
                break
            elif site_limit is None and cat == CATEGORY_DISTRACTING:
                if log.time_spent_seconds > global_limit_sec:
                    today_exceeded = True
                    break
        if not today_exceeded and today_total > 0:
            streak += 1

    # Keep UserSettings streak in sync
    settings_obj.streak_days = streak
    settings_obj.save(update_fields=['streak_days'])

    # ── Per-Site Distraction Tracker ──────────────────────────────────────────
    # Combines daily usage with configured SiteLimit models and blocked_sites list
    site_limits = {
        sl.domain: sl
        for sl in SiteLimit.objects.filter(user=request.user)
    }

    blocked_domains = [clean_domain(s) for s in re.split(r'[\r\n,]+', settings_obj.blocked_sites) if clean_domain(s)]
    # All distracting domains to track
    all_distracting = list(dict.fromkeys(blocked_domains + list(site_limits.keys())))

    distractions = []
    for domain in all_distracting:
        sl = site_limits.get(domain)
        used_secs = next((r['total_seconds'] for r in daily if r['website_url'] == domain), 0)
        used_mins = used_secs // 60
        limit_mins = sl.daily_limit_minutes if sl else settings_obj.daily_limit_minutes
        pct = min(round((used_mins / max(limit_mins, 1)) * 100), 100)
        distractions.append({
            'website_url':   domain,
            'category':      CATEGORY_DISTRACTING,
            'used_minutes':  used_mins,
            'limit_minutes': limit_mins,
            'percentage':    pct,
            'enabled':       sl.enabled if sl else True,
            'limit_id':      sl.id if sl else None,
        })

    # Also include any unlisted distracting sites that had usage today
    for entry in daily:
        if entry['website_url'] not in all_distracting and entry['category'] == CATEGORY_DISTRACTING:
            used_mins = entry['total_seconds'] // 60
            limit_mins = settings_obj.daily_limit_minutes
            pct = min(round((used_mins / max(limit_mins, 1)) * 100), 100)
            distractions.append({
                'website_url':   entry['website_url'],
                'category':      entry['category'],
                'used_minutes':  used_mins,
                'limit_minutes': limit_mins,
                'percentage':    pct,
                'enabled':       True,
                'limit_id':      None,
            })

    # ── Focus Sessions Summary ────────────────────────────────────────────────
    today_sessions = FocusSession.objects.filter(
        user=request.user,
        started_at__date=today,
        completed=True
    )
    today_sessions_count = today_sessions.count()
    longest_session = (
        FocusSession.objects.filter(user=request.user, completed=True)
        .aggregate(Max('duration_minutes'))['duration_minutes__max'] or 0
    )

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Count days of data for smart insights (hiding fake insights if < 2 days)
    data_days_count = user_logs.values('date').distinct().count()

    # ── Green Grove (Last 30 Days) ───────────────────────────────────────────
    # Forest-style visual showing progress as a grove of trees:
    # - grown tree = successful day (using the exact same strict streak rules)
    # - withered tree = user exceeded a limit that day
    # - empty spot = no browsing data logged / future day
    grove_start_date = today - datetime.timedelta(days=29)
    grove_logs_qs = (
        user_logs
        .filter(date__gte=grove_start_date, date__lte=today)
        .values('date', 'website_url', 'time_spent_seconds')
    )
    grove_logs_by_date = {}
    for row in grove_logs_qs:
        d_str = row['date'].isoformat()
        if d_str not in grove_logs_by_date:
            grove_logs_by_date[d_str] = []
        grove_logs_by_date[d_str].append(row)

    grove_days = []
    total_trees_grown = 0

    for i in range(29, -1, -1):
        d_obj = today - datetime.timedelta(days=i)
        d_str = d_obj.isoformat()
        day_logs = grove_logs_by_date.get(d_str, [])

        if not day_logs:
            grove_days.append({
                'date': d_str,
                'status': 'empty',
                'day_name': d_obj.strftime('%a'),
                'day_num': d_obj.day,
                'formatted_date': d_obj.strftime('%b %d'),
                'total_seconds': 0,
            })
        else:
            day_exceeded = False
            day_total_sec = 0
            for log in day_logs:
                day_total_sec += log['time_spent_seconds']
                cat = classify_domain(log['website_url'], user=request.user)
                site_limit = limits_dict.get(log['website_url'], None)
                if site_limit is not None and log['time_spent_seconds'] > site_limit:
                    day_exceeded = True
                    break
                elif site_limit is None and cat == CATEGORY_DISTRACTING:
                    if log['time_spent_seconds'] > global_limit_sec:
                        day_exceeded = True
                        break

            if not day_exceeded and day_total_sec > 0:
                grove_days.append({
                    'date': d_str,
                    'status': 'grown',
                    'day_name': d_obj.strftime('%a'),
                    'day_num': d_obj.day,
                    'formatted_date': d_obj.strftime('%b %d'),
                    'total_seconds': day_total_sec,
                })
                total_trees_grown += 1
            elif day_exceeded:
                grove_days.append({
                    'date': d_str,
                    'status': 'withered',
                    'day_name': d_obj.strftime('%a'),
                    'day_num': d_obj.day,
                    'formatted_date': d_obj.strftime('%b %d'),
                    'total_seconds': day_total_sec,
                })
            else:
                grove_days.append({
                    'date': d_str,
                    'status': 'empty',
                    'day_name': d_obj.strftime('%a'),
                    'day_num': d_obj.day,
                    'formatted_date': d_obj.strftime('%b %d'),
                    'total_seconds': day_total_sec,
                })

    return Response({
        'weekly': weekly,
        'daily':  daily,
        'stats': {
            'today_total_seconds':       today_total,
            'productive_seconds':        productive_seconds,
            'distracting_seconds':       distracting_seconds,
            'others_seconds':            others_seconds,
            'social_seconds':            distracting_seconds,
            'entertainment_seconds':     0,
            'focus_efficiency':          focus_efficiency,
            'top_site':                  top_site,
            'streak':                    streak,
            'today_sessions_count':      today_sessions_count,
            'longest_session_minutes':   longest_session,
            'data_days_count':           data_days_count,
        },
        'grove': {
            'days':           grove_days,
            'total_grown':    total_trees_grown,
            'current_streak': streak,
        },
        'distractions': distractions,
        'settings': {
            'focus_mode_active':     settings_obj.focus_mode_active,
            'daily_limit_minutes':   settings_obj.daily_limit_minutes,
            'focus_goal_minutes':    settings_obj.focus_goal_minutes,
            'streak_days':           streak,
            'require_challenge':     settings_obj.require_challenge,
            'blocked_sites':         settings_obj.blocked_sites,
            'allowed_sites':         settings_obj.allowed_sites,
            'schedule_enabled':      settings_obj.schedule_enabled,
            'schedule_start':        settings_obj.schedule_start,
            'schedule_end':          settings_obj.schedule_end,
        },
        'user': {
            'username': request.user.username,
            'name': (request.user.get_full_name() or request.user.first_name or request.user.username),
            'persona':  profile.persona,
            'level': profile.level,
            'xp': profile.xp,
            'xp_progress': xp_progress,
            'has_zen_master': profile.has_zen_master,
            'has_deep_worker': profile.has_deep_worker,
            'has_iron_will': profile.has_iron_will,
        }
    })


# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS API
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def settings_view(request):
    """
    GET   /api/settings/
    PATCH /api/settings/
    """
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = UserSettingsSerializer(settings_obj)
        data = serializer.data
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        data['persona'] = profile.persona
        return Response(data)

    # Handle persona updates on UserProfile if sent in PATCH
    if 'persona' in request.data:
        raw_persona = str(request.data.get('persona', '')).strip().lower()
        valid_personas = dict(PERSONA_CHOICES)
        if raw_persona in valid_personas:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            if profile.persona != raw_persona:
                profile.persona = raw_persona
                profile.save(update_fields=['persona'])
                apply_persona_defaults(request.user, raw_persona, keep_user_sites=True)
                settings_obj.refresh_from_db()

    serializer = UserSettingsSerializer(settings_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        resp_data = serializer.data
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        resp_data['persona'] = profile.persona
        return Response(resp_data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# SITE LIMITS API
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def limits_list_create_view(request):
    """
    GET  /api/limits/ — list site limits for request.user
    POST /api/limits/ — create or update site limit { domain, daily_limit_minutes, enabled? }
    """
    if request.method == 'GET':
        limits = SiteLimit.objects.filter(user=request.user)
        serializer = SiteLimitSerializer(limits, many=True)
        return Response(serializer.data)

    domain = clean_domain(request.data.get('domain', ''))
    if not domain:
        return Response({'error': 'Domain is required.'}, status=status.HTTP_400_BAD_REQUEST)

    limit_minutes = int(request.data.get('daily_limit_minutes', 30))
    enabled = request.data.get('enabled', True)

    obj, created = SiteLimit.objects.update_or_create(
        user=request.user,
        domain=domain,
        defaults={
            'daily_limit_minutes': limit_minutes,
            'enabled': enabled,
        }
    )
    serializer = SiteLimitSerializer(obj)
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(serializer.data, status=status_code)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def limits_detail_view(request, pk):
    """
    PATCH  /api/limits/<pk>/
    DELETE /api/limits/<pk>/
    """
    try:
        limit_obj = SiteLimit.objects.get(pk=pk, user=request.user)
    except SiteLimit.DoesNotExist:
        return Response({'error': 'Limit not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        limit_obj.delete()
        return Response({'detail': 'Deleted.'}, status=status.HTTP_204_NO_CONTENT)

    serializer = SiteLimitSerializer(limit_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIES API
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def categories_list_create_view(request):
    """
    GET  /api/categories/ — list user's category overrides
    POST /api/categories/ — create/update category override { domain, category }
    """
    if request.method == 'GET':
        overrides = CategoryOverride.objects.filter(user=request.user)
        serializer = CategoryOverrideSerializer(overrides, many=True)
        return Response(serializer.data)

    domain = clean_domain(request.data.get('domain', ''))
    raw_cat = (request.data.get('category', '') or '').strip()
    
    if raw_cat in ('Productive sites', 'Productivity', 'Productive', CATEGORY_PRODUCTIVE):
        category = CATEGORY_PRODUCTIVE
    elif raw_cat in ('Distracting sites', 'Social', 'Entertainment', 'Distracting', CATEGORY_DISTRACTING):
        category = CATEGORY_DISTRACTING
    elif raw_cat in ('Others', 'Other', CATEGORY_OTHERS):
        category = CATEGORY_OTHERS
    else:
        return Response({'error': 'Valid domain and category are required.'}, status=status.HTTP_400_BAD_REQUEST)

    obj, created = CategoryOverride.objects.update_or_create(
        user=request.user,
        domain=domain,
        defaults={'category': category}
    )
    # Also retroactively update any existing UsageLog category for this user & domain
    UsageLog.objects.filter(user=request.user, website_url=domain).update(category=category)

    serializer = CategoryOverrideSerializer(obj)
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def categories_detail_view(request, pk):
    """DELETE /api/categories/<pk>/ — removes user category override."""
    try:
        override = CategoryOverride.objects.get(pk=pk, user=request.user)
    except CategoryOverride.DoesNotExist:
        return Response({'error': 'Override not found.'}, status=status.HTTP_404_NOT_FOUND)

    domain = override.domain
    override.delete()
    # Recalculate default category for past logs
    default_cat = classify_domain(domain, user=request.user)
    UsageLog.objects.filter(user=request.user, website_url=domain).update(category=default_cat)
    return Response({'detail': 'Override removed.'}, status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# FOCUS SESSIONS API
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sessions_view(request):
    """
    GET  /api/sessions/ — return recent focus sessions
    POST /api/sessions/ — log completed focus session { duration_minutes: 25 }
    """
    if request.method == 'GET':
        sessions = FocusSession.objects.filter(user=request.user)[:10]
        serializer = FocusSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    duration = int(request.data.get('duration_minutes', 25))
    session = FocusSession.objects.create(
        user=request.user,
        duration_minutes=duration,
        completed=True
    )
    serializer = FocusSessionSerializer(session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# PRIVACY & DATA EXPORT / DELETION API
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_export_view(request):
    """GET /api/data/export/ — downloads complete user data in JSON format."""
    user = request.user
    logs = list(UsageLog.objects.filter(user=user).values('website_url', 'category', 'time_spent_seconds', 'date'))
    limits = list(SiteLimit.objects.filter(user=user).values('domain', 'daily_limit_minutes', 'enabled'))
    categories = list(CategoryOverride.objects.filter(user=user).values('domain', 'category'))
    sessions = list(FocusSession.objects.filter(user=user).values('duration_minutes', 'started_at', 'completed'))
    
    settings_obj = getattr(user, 'settings', None)
    settings_data = {
        'focus_mode_active': settings_obj.focus_mode_active if settings_obj else False,
        'daily_limit_minutes': settings_obj.daily_limit_minutes if settings_obj else 60,
        'streak_days': settings_obj.streak_days if settings_obj else 0,
        'schedule_enabled': settings_obj.schedule_enabled if settings_obj else False,
        'schedule_start': settings_obj.schedule_start if settings_obj else '20:00',
        'schedule_end': settings_obj.schedule_end if settings_obj else '22:00',
    }

    payload = {
        'user': user.username,
        'exported_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'settings': settings_data,
        'usage_logs': logs,
        'site_limits': limits,
        'category_overrides': categories,
        'focus_sessions': sessions,
    }
    return JsonResponse(payload, json_dumps_params={'indent': 2})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def data_delete_view(request):
    """POST /api/data/delete/ — purges user's usage logs and reset timers."""
    UsageLog.objects.filter(user=request.user).delete()
    FocusSession.objects.filter(user=request.user).delete()
    return Response({'detail': 'All browsing records and focus sessions have been erased.'})