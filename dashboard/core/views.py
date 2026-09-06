import datetime
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import UsageLog
from .serializers import RegisterSerializer, UsageLogSerializer


# ─────────────────────────────────────────────────────────────────────────────
# PAGE VIEWS — serve HTML templates
# ─────────────────────────────────────────────────────────────────────────────

def auth_page(request):
    """Serves the Login / Sign-Up page."""
    if request.user.is_authenticated:
        return __import__('django.shortcuts', fromlist=['redirect']).redirect('/dashboard/')
    return render(request, 'auth.html')


@login_required
def dashboard_page(request):
    """Serves the analytics dashboard (requires session login)."""
    token, _ = Token.objects.get_or_create(user=request.user)
    return render(request, 'dashboard.html', {'api_token': token.key, 'username': request.user.username})


# ─────────────────────────────────────────────────────────────────────────────
# AUTH API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    POST /api/auth/register/
    Body: { username, email, password }
    Returns: { token, username }
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user  = serializer.save()
        token = Token.objects.create(user=user)
        # Log the user into the session too (so the dashboard page works)
        from django.contrib.auth import login
        login(request, user)
        return Response({'token': token.key, 'username': user.username}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/auth/login/
    Body: { username, password }
    Returns: { token, username }
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    token, _ = Token.objects.get_or_create(user=user)
    # Establish a session so the dashboard page doesn't redirect back to login
    from django.contrib.auth import login
    login(request, user)
    return Response({'token': token.key, 'username': user.username})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /api/auth/logout/ — invalidates the DRF token."""
    request.user.auth_token.delete()
    from django.contrib.auth import logout
    logout(request)
    return Response({'detail': 'Logged out.'})


# ─────────────────────────────────────────────────────────────────────────────
# USAGE LOG API
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def usage_log_view(request):
    """
    POST /api/usage/
    Header: Authorization: Token <token>
    Body: { website_url, time_spent_seconds, date }  OR  a list of the above.

    Uses update_or_create so repeated POSTs accumulate rather than duplicate.
    The extension sends the INCREMENTAL seconds since last sync, not the full day total,
    so we ADD to whatever is already stored.
    """
    # Accept both a single object and a list (bulk sync)
    data = request.data
    many = isinstance(data, list)

    serializer = UsageLogSerializer(data=data, many=many)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    entries = serializer.validated_data if many else [serializer.validated_data]
    created_count = updated_count = 0

    for entry in entries:
        obj, created = UsageLog.objects.get_or_create(
            user        = request.user,
            website_url = entry['website_url'],
            date        = entry['date'],
            defaults    = {'time_spent_seconds': 0},
        )
        # Accumulate — the extension sends incremental seconds
        obj.time_spent_seconds += entry['time_spent_seconds']
        obj.save(update_fields=['time_spent_seconds', 'updated_at'])
        if created:
            created_count += 1
        else:
            updated_count += 1

    return Response(
        {'created': created_count, 'updated': updated_count},
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY API — used by the dashboard charts
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def summary_view(request):
    """
    GET /api/summary/
    Header: Authorization: Token <token>

    Returns:
    {
      "weekly": [
        { "date": "2026-09-01", "total_seconds": 3600 },
        ...
      ],
      "daily": [
        { "website_url": "youtube.com", "total_seconds": 1800 },
        ...
      ],
      "stats": {
        "today_total_seconds": 3600,
        "top_site": "youtube.com",
        "streak": 3
      }
    }
    """
    today     = datetime.date.today()
    week_ago  = today - datetime.timedelta(days=6)

    user_logs = UsageLog.objects.filter(user=request.user)

    # Weekly: total seconds per day for the last 7 days
    weekly_qs = (
        user_logs
        .filter(date__gte=week_ago, date__lte=today)
        .values('date')
        .annotate(total_seconds=Sum('time_spent_seconds'))
        .order_by('date')
    )

    # Build a full 7-day list, filling zeros for missing days
    weekly_map = {row['date'].isoformat(): row['total_seconds'] for row in weekly_qs}
    weekly = []
    for i in range(7):
        d = (week_ago + datetime.timedelta(days=i)).isoformat()
        weekly.append({'date': d, 'total_seconds': weekly_map.get(d, 0)})

    # Daily: breakdown by site for today
    daily_qs = (
        user_logs
        .filter(date=today)
        .values('website_url')
        .annotate(total_seconds=Sum('time_spent_seconds'))
        .order_by('-total_seconds')
    )
    daily = [{'website_url': r['website_url'], 'total_seconds': r['total_seconds']} for r in daily_qs]

    # Stats
    today_total = sum(r['total_seconds'] for r in daily)
    top_site    = daily[0]['website_url'] if daily else None

    # Simple streak: count consecutive days with any usage going back from yesterday
    streak = 0
    check_date = today - datetime.timedelta(days=1)
    while True:
        if user_logs.filter(date=check_date).exists():
            streak += 1
            check_date -= datetime.timedelta(days=1)
        else:
            break

    return Response({
        'weekly': weekly,
        'daily':  daily,
        'stats': {
            'today_total_seconds': today_total,
            'top_site':            top_site,
            'streak':              streak,
        }
    })