from django.urls import path
from . import views

urlpatterns = [
    # ── Page routes ──────────────────────────────────────────────────────────
    path('',            views.auth_page,      name='auth'),
    path('dashboard/',  views.dashboard_page, name='dashboard'),

    # ── Auth API ─────────────────────────────────────────────────────────────
    path('api/auth/register/', views.register_view, name='api-register'),
    path('api/auth/login/',    views.login_view,    name='api-login'),
    path('api/auth/logout/',   views.logout_view,   name='api-logout'),

    # ── Usage API ─────────────────────────────────────────────────────────────
    path('api/usage/',   views.usage_log_view, name='api-usage'),
    path('api/summary/', views.summary_view,   name='api-summary'),
]