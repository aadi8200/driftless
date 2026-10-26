from django.urls import path
from . import views

urlpatterns = [
    # ── Page routes ──────────────────────────────────────────────────────────
    path('',            views.auth_page,      name='auth'),
    path('dashboard/',  views.dashboard_page, name='dashboard'),

    # ── Auth API ─────────────────────────────────────────────────────────────
    path('api/auth/register/',          views.register_view,          name='api-register'),
    path('api/auth/login/',             views.login_view,             name='api-login'),
    path('api/auth/logout/',            views.logout_view,            name='api-logout'),
    path('api/auth/regenerate-token/',  views.regenerate_token_view,  name='api-regenerate-token'),

    # ── Usage & Analytics API ────────────────────────────────────────────────
    path('api/usage/',     views.usage_log_view, name='api-usage'),
    path('api/summary/',   views.summary_view,   name='api-summary'),

    # ── Settings API ─────────────────────────────────────────────────────────
    path('api/settings/',  views.settings_view,  name='api-settings'),

    # ── Per-Site Limits API ──────────────────────────────────────────────────
    path('api/limits/',         views.limits_list_create_view, name='api-limits'),
    path('api/limits/<int:pk>/', views.limits_detail_view,     name='api-limits-detail'),

    # ── Category Overrides API ───────────────────────────────────────────────
    path('api/categories/',         views.categories_list_create_view, name='api-categories'),
    path('api/categories/<int:pk>/', views.categories_detail_view,     name='api-categories-detail'),

    # ── Focus Sessions API ───────────────────────────────────────────────────
    path('api/sessions/',  views.sessions_view,  name='api-sessions'),

    # ── Privacy & Data Management API ────────────────────────────────────────
    path('api/data/export/',  views.data_export_view,  name='api-data-export'),
    path('api/data/delete/',  views.data_delete_view,  name='api-data-delete'),
]