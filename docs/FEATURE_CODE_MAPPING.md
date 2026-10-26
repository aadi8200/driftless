# DRIFTLESS — Feature-to-Code Mapping & Cooperation Analysis

## 1. Master Feature-to-Code Traceability Matrix

| Feature | Frontend Files | Extension Files | Backend Files | API & Database Dependencies | Implementation Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **User Registration & Persona Onboarding** | `dashboard/core/templates/auth.html` | None | `core/views.py:73`, `core/serializers.py:63`, `core/models.py:16` | `POST /api/auth/register/`, `User`, `UserProfile`, `UserSettings`, `SiteLimit` | **PASS (Fully Verified)** |
| **Multi-Identifier Login (Username/Email/Phone)**| `dashboard/core/templates/auth.html` | None | `core/views.py:92`, `core/models.py:16` | `POST /api/auth/login/`, `Token`, `User`, `UserProfile` | **PASS (Fully Verified)** |
| **API Token Copy & Regeneration** | `dashboard/core/templates/dashboard.html` | `extension/popup.html`, `extension/popup.js` | `core/views.py:150` | `POST /api/auth/regenerate-token/`, `authtoken_token` | **PASS (Fully Verified)** |
| **Passive Tab Dwell Tracking** | None | `extension/background.js` | None (Local accumulation) | `chrome.tabs`, `chrome.windows`, `chrome.idle`, `chrome.storage.local` | **PASS (Fully Verified)** |
| **Automatic Idle Detection** | None | `extension/background.js:208` | None | `chrome.idle.setDetectionInterval(60)` | **PASS (Fully Verified)** |
| **Periodic 60s Delta Sync** | None | `extension/background.js:263`, `extension/manifest.json` | `core/views.py:165`, `core/serializers.py:116`, `core/models.py:214` | `POST /api/usage/`, `UsageLog`, `chrome.alarms` | **PASS (Fully Verified)** |
| **Midnight Dwell Commit & Reset**| None | `extension/background.js:217` | `core/views.py:165` | `POST /api/usage/`, `chrome.alarms`, `declarativeNetRequest` | **PASS (Fully Verified)** |
| **3-Tier Escalation: 80% Nudge** | None | `extension/background.js:93`, `extension/popup.js:133` | None | `chrome.notifications.create`, `chrome.storage.local` | **PASS (Fully Verified)** |
| **3-Tier Escalation: 100% Alert** | None | `extension/background.js:101` | None | `chrome.notifications.create`, `chrome.storage.local` | **PASS (Fully Verified)** |
| **3-Tier Escalation: 5m Grace + DNR Block** | None | `extension/background.js:109`, `extension/blocked.html` | None | `chrome.declarativeNetRequest.updateDynamicRules` | **PASS (Fully Verified)** |
| **Focus Mode Toggling** | `dashboard/core/templates/dashboard.html:1115` | `extension/popup.js:201`, `extension/background.js:352` | `core/views.py:443`, `core/models.py:246` | `PATCH /api/settings/`, `UserSettings.focus_mode_active` | **PASS (Fully Verified)** |
| **Timed Focus Sprints (25/45/60m)**| None | `extension/popup.js:228`, `extension/background.js:416` | `core/views.py:577`, `core/models.py:199` | `POST /api/sessions/`, `FocusSession`, `chrome.alarms` | **PASS (Fully Verified)** |
| **Per-Site Daily Limit Configuration**| `dashboard/core/templates/dashboard.html:1212` | `extension/popup.js:245` | `core/views.py:467`, `core/serializers.py:135`, `core/models.py:174` | `GET/POST/PATCH/DELETE /api/limits/`, `SiteLimit` | **PASS (Fully Verified)** |
| **Dynamic Domain Categorization**| None | `extension/popup.js:141` | `core/models.py:106` (`classify_domain`) | `CATEGORY_MAP`, `UserProfile.persona`, academic domain regex | **PASS (Fully Verified)** |
| **User Category Overrides** | `dashboard/core/templates/dashboard.html:1261` | None | `core/views.py:526`, `core/serializers.py:152`, `core/models.py:153` | `GET/POST/DELETE /api/categories/`, `CategoryOverride` | **PASS (Fully Verified)** |
| **7-Day Analytics & Charting** | `dashboard/core/templates/dashboard.html:913` | None | `core/views.py:213` | `GET /api/summary/`, `UsageLog`, Chart.js 4.4 | **PASS (Fully Verified)** |
| **Strict Streak Calculation** | `dashboard/core/templates/dashboard.html:874` | `extension/popup.js:61` | `core/views.py:294` | `GET /api/summary/`, `UsageLog`, `SiteLimit`, `UserSettings` | **PASS (Fully Verified)** |
| **Focus Goal Ring (3h Default)** | `dashboard/core/templates/dashboard.html:890` | None | `core/views.py:213`, `core/models.py:253` | `UserSettings.focus_goal_minutes`, SVG `stroke-dasharray` | **PASS (Fully Verified)** |
| **Dual-Theme System (Calm Sky / Opal Noir)**| `dashboard/core/templates/*.html`, `core/static/css/theme.css` | `extension/popup.html`, `extension/blocked.html`, `theme.css` | None | CSS custom properties, `localStorage['driftless-theme']` | **PASS (Fully Verified)** |
| **Demo vs. Live Data Switcher**| `dashboard/core/templates/dashboard.html:786` | None | `core/management/commands/seed_demo.py` | Client toggle switching between fallback demo payload and `/api/summary/` | **PASS (Fully Verified)** |
| **1-Click Data Export (JSON)** | `dashboard/core/templates/dashboard.html:1285` | None | `core/views.py:603` | `GET /api/data/export/`, `UsageLog`, `SiteLimit`, `FocusSession` | **PASS (Fully Verified)** |
| **1-Click Browsing History Erasure**| `dashboard/core/templates/dashboard.html:1289` | `extension/popup.js:318` | `core/views.py:632` | `POST /api/data/delete/`, `RESET_ALL_TIMERS` message | **PASS (Fully Verified)** |

---

## 2. Multi-File Component Cooperation Analysis

### 2.1. Cooperating Modules: Per-Site Limits Enforcement
A user configures a 25-minute limit on `reddit.com`. Here is how the files cooperate:
1. **Creation (`dashboard.html` or `popup.js`):** The user enters the domain and limit. An asynchronous `POST /api/limits/` is dispatched to the Django backend.
2. **Persistence (`core/views.py` & `core/models.py`):** The DRF view validates `1 <= daily_limit_minutes <= 1440` and updates the `SiteLimit` record in `db.sqlite3`.
3. **Synchronization (`background.js`):** During the next 60-second pull cycle, `pullBackendConfig()` requests `GET /api/limits/` and caches the limit in `chrome.storage.local.set({ siteLimits })`.
4. **Enforcement (`background.js`):** As the user spends time on `reddit.com`, `evaluateSiteLimits()` tracks accumulated seconds against 25 minutes. At 20 minutes (80%), a desktop nudge is created. At 25 minutes (100%), an alert is shown. At 30 minutes (100% + 5m), a DNR redirect rule is created.
5. **Interception (`blocked.html`):** Future requests to `reddit.com` are caught by Chrome's network engine and redirected to `chrome-extension://.../blocked.html?site=reddit.com`.
6. **Analytics (`views.py` & `dashboard.html`):** The dashboard `/api/summary/` checks `reddit.com` against the `SiteLimit`. If exceeded, it breaks the consecutive daily streak.

---

### 2.2. Cooperating Modules: Persona-Driven Onboarding
1. **Registration UI (`auth.html`):** The user registers, choosing persona `"influencer"`.
2. **Validation & Defaults (`core/serializers.py`):** `RegisterSerializer` calls `apply_persona_defaults()`, seeding initial `SiteLimit` records (e.g. Netflix: 30m, Twitch: 25m, Reddit: 20m).
3. **Classification (`core/models.py`):** `classify_domain()` checks `user.profile.persona`. When the influencer browses `instagram.com` or `youtube.com`, the engine categorizes it as `Productivity` instead of `Social` or `Entertainment`.
4. **Visualization (`dashboard.html`):** Time spent on Instagram is rendered in emerald green on the 7-day chart, increasing the user's Focus Efficiency score.

---

## 3. Implementation State Classifications

- **Verified Live Full-Stack Features:**
  - Multi-identifier authentication, Token auth, persona seeding.
  - Periodic delta ingestion, SQLite persistence, and aggregation.
  - Per-site limits, category overrides, and data export/deletion.
  - Active tab tracking, 3-tier escalation, DNR blocking, and focus sprint timers.
  - Calm Sky & Opal Noir dual-theme styling across dashboard, popup, and blocked screen.
- **Client-Side Isolated Features:**
  - Timer countdown ticker (`popup.js` `setInterval`).
  - Active window focus and 60-second idle detection (`chrome.idle`).
  - FOUC-prevention scripts in HTML `<head>`.
- **Demo Mode Fallback:**
  - The dashboard includes a built-in toggle (`Demo` vs. `Live`). In Demo mode, it renders a 14-day sample payload without requiring an active server connection. In Live mode, it fetches directly from `/api/summary/`.
