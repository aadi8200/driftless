# Driftless — Changelog

This document summarizes all improvements and fixes applied across the Driftless application, categorized by the master prompt section numbers.

---

### Section 1: One Unified Theme (Dashboard + Popup + Login)
- Created shared design token CSS file `dashboard/core/static/css/theme.css` and `extension/theme.css` with unified variables (`--pri: #7C3AED`, `--accent: #EC4899`, `--bg: #FDF2F8`, `--card: #FFFFFF`, `--ink: #2A1B3D`, `--prod: #10B981`, `--soc: #F59E0B`, `--ent: #F43F5E`, `--other: #94A3B8`, `--grad: linear-gradient(135deg, var(--pri), var(--accent))`, `--radius: 14px`).
- Updated Hero card on dashboard to utilize `--grad`.
- Replaced the blue-green gradient on the login and sign-up page (`auth.html`) with the rich theme gradient.
- Updated the active sidebar indicator to use `--pri` and fixed the bug where **Settings** was erroneously highlighted on dashboard load.
- Updated Chart.js color palette and canvas datasets to use the exact theme category variables.
- Restyled the extension popup (`popup.html`) with the unified theme tokens, Inter typography, and 14px border radii.

### Section 2: Productive Time Tracking & Category Management
- Re-architected `extension/background.js` to track all active domains visited while the tab is active, window is focused, and user is active (using `chrome.tabs`, `chrome.windows`, and `chrome.idle`).
- Replaced the previous flaw where non-social sites were ignored or wrongly categorized with a comprehensive server-side `CATEGORY_MAP` and classification engine (`Productivity`, `Social`, `Entertainment`, `Other`).
- Added educational and academic domain pattern matching (`*.edu`, `*.ac.in` -> `Productivity`).
- Implemented `CategoryOverride` model, migration, serializer, and API endpoints (`GET /api/categories/`, `POST /api/categories/`, `DELETE /api/categories/<id>/`).
- Added a "Manage Categories" panel in dashboard Settings for custom domain categorization.
- Added persona presets (Student, Professional, Influencer, Creator) that configure intelligent category rules (e.g. Influencers categorize Instagram/YouTube as work/productive).
- Standardized focus efficiency formula: `productive / (productive + social + entertainment)`.

### Section 3: Per-Site Timers, Limits & 3-Tier Escalation
- Added `SiteLimit` model (`user`, `domain`, `daily_limit_minutes`, `enabled`), database migration, serializer, and CRUD API endpoints (`GET / POST / PATCH / DELETE /api/limits/`).
- Updated extension popup with a list of tracked sites, each displaying its own limit input, live timer, and colored mini progress bar, plus an "Add site + limit" form.
- Connected dashboard "Distraction Tracker" with an editable **Manage Limits Modal** providing bidirectional synchronization with the extension.
- Implemented 3-tier escalation logic:
  1. **80% of limit**: Gentle Chrome notification nudge.
  2. **100% of limit**: Alert notification warning that daily streak is at risk.
  3. **100% + 5m grace period**: Dynamic blocking via `declarativeNetRequest` dynamic rules redirecting to `blocked.html`.
- Implemented `extension/blocked.html` displaying time spent, streak preservation notice, and a "Back to work" action button.
- Added local midnight reset alarm (`chrome.alarms`) clearing daily timers and removing DNR limit block rules.
- Implemented `FocusSession` model and popup focus sprint buttons (25m, 45m, 60m) that trigger strict focus mode and record session metrics.

### Section 4: Sync & Data Consistency
- Unified server as the single source of truth; extension caches locally and flushes incremental deltas every 60s and on popup open.
- Fixed streak calculation: a day counts towards streak strictly if no site exceeded its daily limit.
- Created management command `python manage.py seed_demo` generating an evaluator account (`demo@driftless.app` / `demo123456`) pre-seeded with 14 days of realistic, mathematically consistent data and a 14-day streak.

### Section 5: Security & Privacy
- Masked API token on the dashboard by default with 1-click copy and added a "Regenerate Token" button (`POST /api/auth/regenerate-token/`).
- Added a confirmation dialog modal before executing "Reset All Timers" in the extension popup.
- Enforced strict per-user data isolation across all endpoints (filtering by `request.user`).
- Added comprehensive unit and API test suite in `dashboard/core/tests.py` testing auth, classification, and data isolation.
- Implemented rate limiting (`120/min`) on the usage sync endpoint and added domain sanitization (stripping protocols, www, ports, paths).
- Created `.env.example` and configured `python-dotenv` for environment variable loading (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`).
- Added Privacy & Data Control panel in dashboard settings with 1-click **Export My Data (JSON)** (`/api/data/export/`) and **Erase All Data** (`/api/data/delete/`).

### Section 6: UI/UX Polish
- Added empty states for new accounts ("No live browsing data yet — browse with the extension on and come back!").
- Suppressed fake insights until at least 2 distinct days of data are recorded.
- Fixed text grammar: corrected "1 days" to "1 day" using pluralization helpers, capitalized "YouTube", and added time-based greetings ("Good morning", "Good afternoon", "Good evening").
- Added Today/Weekly view and Bar/Trend line chart toggles.
- Added a circular SVG **Focus Goal Ring** tracking daily progress towards the user's focus goal (e.g., 3 hours).
- Added Whitelist and Blocked lists in dashboard settings with an optional "Require typing challenge sentence" toggle.
- Ensured responsiveness down to 360px viewport width with a collapsible mobile navigation drawer.
- Enhanced accessibility with visible focus rings, ARIA labels, and color contrast >= 4.5:1.

### Section 7: Deployment & Distribution
- Configured WhiteNoise for static asset serving (`CompressedStaticFilesStorage`) and verified with `python manage.py collectstatic`.
- Pinned production requirements in `requirements.txt` including `whitenoise`, `python-dotenv`, and `gunicorn`.
- Added `Procfile` and `render.yaml` for Render, alongside detailed step-by-step instructions in `DEPLOY.md` for PythonAnywhere and Render.
- Created extension packaging scripts `scripts/build_extension.py` and `scripts/build_extension.sh` producing `driftless-extension.zip`.
