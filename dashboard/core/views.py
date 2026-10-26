import datetime
import re
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Max
from django.http import JsonResponse
from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
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
    FocusSessionSerializer
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
    return render(request, 'auth.html')


@login_required
def dashboard_page(request):
    """Serves the analytics dashboard (requires session login)."""
    token, _ = Token.objects.get_or_create(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'dashboard.html', {
        'api_token': token.key,
        'username': request.user.username,
        'persona': profile.persona,
    })


# ─────────────────────────────────────────────────────────────────────────────
# AUTH API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    POST /api/auth/register/
    Body: { username, email?, phone?, password, persona? }
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response({
            'token': token.key,
            'username': user.username
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
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

    # ── Weekly: per-day per-category totals ──────────────────────────────────
    weekly_qs = (
        user_logs
        .filter(date__gte=week_ago, date__lte=today)
        .values('date', 'category')
        .annotate(total_seconds=Sum('time_spent_seconds'))
        .order_by('date')
    )

    weekly_map = {}
    for row in weekly_qs:
        d = row['date'].isoformat()
        if d not in weekly_map:
            weekly_map[d] = {
                CATEGORY_PRODUCTIVITY: 0,
                CATEGORY_SOCIAL: 0,
                CATEGORY_ENTERTAINMENT: 0,
                CATEGORY_OTHER: 0,
            }
        cat = row['category'] or CATEGORY_OTHER
        if cat in weekly_map[d]:
            weekly_map[d][cat] = row['total_seconds']
        else:
            weekly_map[d][CATEGORY_OTHER] += row['total_seconds']

    weekly = []
    for i in range(7):
        d = (week_ago + datetime.timedelta(days=i)).isoformat()
        cats = weekly_map.get(d, {
            CATEGORY_PRODUCTIVITY: 0,
            CATEGORY_SOCIAL: 0,
            CATEGORY_ENTERTAINMENT: 0,
            CATEGORY_OTHER: 0,
        })
        weekly.append({
            'date': d,
            'total_seconds': sum(cats.values()),
            'productivity_seconds':  cats.get(CATEGORY_PRODUCTIVITY, 0),
            'social_seconds':        cats.get(CATEGORY_SOCIAL, 0),
            'entertainment_seconds': cats.get(CATEGORY_ENTERTAINMENT, 0),
            'other_seconds':         cats.get(CATEGORY_OTHER, 0),
        })

    # ── Daily: breakdown by site for today ────────────────────────────────────
    daily_qs = (
        user_logs
        .filter(date=today)
        .values('website_url', 'category')
        .annotate(total_seconds=Sum('time_spent_seconds'))
        .order_by('-total_seconds')
    )
    daily = [{
        'website_url':   r['website_url'],
        'total_seconds': r['total_seconds'],
        'category':      r['category'] or CATEGORY_OTHER,
    } for r in daily_qs]

    # ── Stats & Focus Efficiency ──────────────────────────────────────────────
    today_total        = sum(r['total_seconds'] for r in daily)
    top_site           = daily[0]['website_url'] if daily else None
    productive_seconds = sum(r['total_seconds'] for r in daily if r['category'] == CATEGORY_PRODUCTIVITY)
    social_seconds     = sum(r['total_seconds'] for r in daily if r['category'] == CATEGORY_SOCIAL)
    entertainment_sec  = sum(r['total_seconds'] for r in daily if r['category'] == CATEGORY_ENTERTAINMENT)

    denominator = productive_seconds + social_seconds + entertainment_sec
    if denominator > 0:
        focus_efficiency = round((productive_seconds / denominator) * 100)
    else:
        focus_efficiency = 0

    # ── Strict Streak Calculation ─────────────────────────────────────────────
    # A day counts towards streak ONLY if no site exceeded its limit.
    limits_dict = {
        l.domain: l.daily_limit_minutes * 60
        for l in SiteLimit.objects.filter(user=request.user, enabled=True)
    }
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    global_limit_sec = settings_obj.daily_limit_minutes * 60

    streak = 0
    check_date = today - datetime.timedelta(days=1)
    
    while True:
        day_logs = user_logs.filter(date=check_date)
        if not day_logs.exists():
            break

        day_failed = False
        for log in day_logs:
            site_limit = limits_dict.get(log.website_url, None)
            if site_limit is not None and log.time_spent_seconds > site_limit:
                day_failed = True
                break
            elif site_limit is None and log.category in (CATEGORY_SOCIAL, CATEGORY_ENTERTAINMENT):
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
            site_limit = limits_dict.get(log.website_url, None)
            if site_limit is not None and log.time_spent_seconds > site_limit:
                today_exceeded = True
                break
            elif site_limit is None and log.category in (CATEGORY_SOCIAL, CATEGORY_ENTERTAINMENT):
                if log.time_spent_seconds > global_limit_sec:
                    today_exceeded = True
                    break
        if not today_exceeded and today_total > 0:
            streak += 1

    # Keep UserSettings streak in sync
    settings_obj.streak_days = streak
    settings_obj.save(update_fields=['streak_days'])

    # ── Per-Site Distraction Tracker ──────────────────────────────────────────
    # Combines daily usage with configured SiteLimit models
    site_limits = {
        sl.domain: sl
        for sl in SiteLimit.objects.filter(user=request.user)
    }

    distractions = []
    # Include all configured limits even if 0 seconds today
    for domain, sl in site_limits.items():
        used_secs = next((r['total_seconds'] for r in daily if r['website_url'] == domain), 0)
        used_mins = used_secs // 60
        limit_mins = sl.daily_limit_minutes
        pct = min(round((used_mins / max(limit_mins, 1)) * 100), 100)
        distractions.append({
            'website_url':   domain,
            'category':      classify_domain(domain, user=request.user),
            'used_minutes':  used_mins,
            'limit_minutes': limit_mins,
            'percentage':    pct,
            'enabled':       sl.enabled,
            'limit_id':      sl.id,
        })

    # Also include any unlisted distracting sites that had usage today
    for entry in daily:
        if entry['website_url'] not in site_limits and entry['category'] in (CATEGORY_SOCIAL, CATEGORY_ENTERTAINMENT):
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

    return Response({
        'weekly': weekly,
        'daily':  daily,
        'stats': {
            'today_total_seconds':       today_total,
            'productive_seconds':        productive_seconds,
            'social_seconds':            social_seconds,
            'entertainment_seconds':     entertainment_sec,
            'focus_efficiency':          focus_efficiency,
            'top_site':                  top_site,
            'streak':                    streak,
            'today_sessions_count':      today_sessions_count,
            'longest_session_minutes':   longest_session,
            'data_days_count':           data_days_count,
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
        },
        'user': {
            'username': request.user.username,
            'persona':  profile.persona,
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
        return Response(serializer.data)

    serializer = UserSettingsSerializer(settings_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
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
    category = request.data.get('category', '').capitalize()
    
    if not domain or category not in (CATEGORY_PRODUCTIVITY, CATEGORY_SOCIAL, CATEGORY_ENTERTAINMENT, CATEGORY_OTHER):
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