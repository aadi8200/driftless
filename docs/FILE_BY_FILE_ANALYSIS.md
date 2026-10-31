<h1 id="ch-7">Chapter 7: File-by-File Analysis</h1>

This chapter analyzes every source file in the repository as of **October 31, 2026**, describing its architectural purpose, its primary functions in plain language, and the exact files it interacts with.

---

### 1. `extension/manifest.json`
* **Purpose:** The configuration manifest defining the extension's metadata, permissions, content script injections, background worker, and web-accessible resources under Chrome Manifest V3 rules.
* **Key Properties:**
  - `manifest_version: 3`, `version: "1.1"`
  - `permissions`: `tabs`, `storage`, `alarms`, `notifications`, `idle`, `declarativeNetRequest`, `declarativeNetRequestWithHostAccess`, `declarativeNetRequestFeedback`
  - `host_permissions`: `<all_urls>`
  - `content_scripts`: Injects `content.js` on `<all_urls>` with `run_at: "document_start"`.
  - `background.service_worker`: `background.js`
* **Interacts With:** Chrome runtime, `background.js`, `content.js`, `popup.html`, `blocked.html`.

---

### 2. `extension/content.js`
* **Purpose:** Active tab tracking agent. Solves service worker suspension by executing directly inside active browser tabs and emitting a 1-second heartbeat.
* **Primary Functions:**
  - `isPageActiveAndFocused()`: Returns `true` only when `!document.hidden && document.hasFocus()`.
  - `sendTick()`: Transmits `PAGE_HEARTBEAT_TICK` message to `background.js` with `rawDomain`, `url`, and `timestamp`. If the response contains `blocked: true`, stops heartbeat and executes `window.location.replace(blockedUrl)`.
  - `startHeartbeat()`: Initiates a 1000ms `setInterval` loop calling `sendTick()`.
  - `stopHeartbeat()`: Clears the interval timer when the tab is blurred or hidden.
  - `handleStateChange()`: Listens for `visibilitychange`, `window.focus`, and `window.blur` events. Triggers `startHeartbeat()` or sends `PAGE_HEARTBEAT_PAUSE`.
* **Interacts With:** `background.js` (via `chrome.runtime.sendMessage`), `blocked.html` (via redirection).

---

### 3. `extension/background.js`
* **Purpose:** The central service worker and event orchestrator. Manages storage, DNR rules, system alarms, dwell tracking, limit evaluation, notifications, Pomodoro sprints, and backend synchronization.
* **Primary Functions:**
  - `cleanDomain(url)`: Normalizes URLs into clean lowercase hostnames (e.g. `https://www.reddit.com/r/all` -> `reddit.com`), stripping `www.` and filtering internal browser protocols.
  - `getActiveTabSafe()`: Queries active tabs across focused and current windows with defensive try/catch error handling.
  - `getServerUrl()`: Retrieves the configured backend base URL from storage, defaulting to `http://127.0.0.1:8000`.
  - `buildBlockRule(id, domain)`: Constructs a Declarative Net Request block rule object for the specified domain.
  - `commitActiveTime()`: Flushes uncommitted dwell time deltas into `siteTimes` and `unsyncedDeltas` in `chrome.storage.local`.
  - `evaluateSiteLimits(domain, seconds)`: Compares accumulated seconds against custom site limits and global distracting limits.
  - `sendNudgeNotification(domain)`: Displays an 80% progress desktop notification encouraging the user to wrap up their session.
  - `sendLimitReachedNotification(domain)`: Displays a 100% limit reached alert informing the user that the site is now locked.
  - `blockDomainViaDNR(domain)`: Dynamically installs a DNR block rule in the `1000..1999` range for the domain.
  - `enableFocusMode()`: Injects dynamic DNR rules `100..899` blocking all domains listed in `blockedSites` / `distractingSites`.
  - `disableFocusMode()`: Removes dynamic DNR rules `100..899`, restoring full browsing access.
  - `isShortsOrReelsUrl(url)`: Returns `true` if a URL matches YouTube Shorts or Instagram Reels patterns.
  - `updateShortsReelsRules(enable)`: Dynamically updates DNR rules `2001` and `2002` to intercept Shorts and Reels paths.
  - `parseTimeMinutes(timeStr)`: Converts `"HH:MM"` 24-hour time strings into total minutes from midnight.
  - `isWithinScheduleWindow(startStr, endStr, dateObj)`: Computes whether the current time falls inside the scheduled focus window, correctly handling overnight midnight crossings.
  - `updateScheduleAlarms()`: Clears and creates the `driftless_schedule_start` and `driftless_schedule_end` Chrome alarms.
  - `evaluateScheduleState(trigger)`: Evaluates current time against schedule settings and engages or disengages Focus Mode accordingly.
  - `performMidnightReset()`: Resets `siteTimes` to zero, clears `escalationState`, removes limit DNR rules `1000..1999`, and reschedules the midnight alarm.
  - `syncToBackend()`: Transmits `unsyncedDeltas` to `POST /api/usage/` and fetches updated configuration from `GET /api/settings/`.
* **Interacts With:** `content.js`, `popup.js`, `blocked.html`, `dashboard/core/views.py` (via HTTP fetch), Chrome Extension APIs (`tabs`, `alarms`, `storage`, `declarativeNetRequest`, `notifications`).

---

### 4. `extension/popup.html` & `popup.js`
* **Purpose:** The user interface presented when the extension toolbar icon is clicked.
* **Key Components:**
  - Onboarding Screen (`onboardingView`): Step 1 Welcome message with leaf brand logo; Step 2 Persona selector (Student, Professional, Influencer, Creator, Other).
  - Main View (`mainView`): Streak badge, Focus Mode toggle switch, Shorts & Reels switch (Student only), Scheduled Focus collapsible time editor (start/end pickers, Save button, next focus status text), Pomodoro Sprint controller (Start/Stop buttons, live timer display), Distracting Sites card (with per-site limit gear buttons and global limit modal), Productive Sites card, Connected Account status, and API Token credentials drawer.
  - Modals: `customLimitModal` (per-site minutes), `globalLimitModal` (global minutes), `confirmOverlay` (reset all timers confirmation).
* **Interacts With:** `background.js` (via `chrome.runtime.sendMessage`), `chrome.storage.local`, `theme.css`.

---

### 5. `extension/blocked.html`
* **Purpose:** The friendly interception screen presented when a user attempts to access a blocked site (either via 100% daily limit or active Focus Mode).
* **Key Features:** Reads query parameter `?site=...`, displays the domain name, presents encouraging mindfulness copy ("Time to refocus on what matters"), and displays a countdown timer until the midnight reset.
* **Interacts With:** `theme.css`, `background.js`.

---

### 6. `dashboard/core/models.py`
* **Purpose:** Defines the relational data models and domain classification logic for SQLite persistence via Django ORM.
* **Core Models & Functions:**
  - `UserProfile`: Extends Django's `auth_user` with 1-to-1 relationship. Fields: `phone`, `persona` (Student, Professional, Influencer, Creator, Other), `is_verified` (Boolean), `xp` (Integer, default 0), `level` (Integer, default 1), and badge booleans: `has_zen_master`, `has_deep_worker`, `has_iron_will`. Includes `seed_demo_gamification()` helper.
  - `UserSettings`: User preferences. Fields: `focus_mode_active`, `daily_limit_minutes`, `focus_goal_minutes`, `streak_days`, `require_challenge`, `blocked_sites` (newline-delimited text), `allowed_sites`, `schedule_enabled`, `schedule_start`, `schedule_end`.
  - `UsageLog`: Ingested dwell logs. Fields: `user` (FK), `website_url`, `time_spent_seconds`, `category`, `date`, timestamps.
  - `SiteLimit`: Per-domain limit configurations. Fields: `user` (FK), `domain`, `daily_limit_minutes`, `enabled`.
  - `CategoryOverride`: User-defined category overrides. Fields: `user` (FK), `domain`, `category`.
  - `FocusSession`: Completed focus sprint records. Fields: `user` (FK), `duration_minutes`, `started_at`, `completed`.
  - `clean_domain(url)`: Strips schemes, paths, and `www.` prefixes to isolate standard domain names.
  - `classify_domain(domain, user=None)`: Looks up user `CategoryOverride`, then checks static `CATEGORY_MAP` (45+ domains), falls back to academic TLD heuristic, and defaults to `CATEGORY_OTHERS`.
* **Interacts With:** `views.py`, `serializers.py`, `admin.py`, `tests.py`.

---

### 7. `dashboard/core/serializers.py`
* **Purpose:** Serializes Django model instances to JSON and validates inbound API payloads.
* **Key Components:**
  - `PERSONA_DEFAULTS`: Static dictionary storing default distracting and productive site lists and recommended schedule windows for each of the 5 personas.
  - `apply_persona_defaults(user, persona, keep_user_sites=False)`: Seeds initial site limits and schedule settings for a user. If `keep_user_sites=True`, preserves any custom sites previously added by the user.
  - `RegisterSerializer`: Validates registration input (`username`, `email`, `phone`, `password`, `persona`), enforces uniqueness, hashes passwords securely, and creates `UserProfile` and `UserSettings`.
  - `UsageLogSerializer`: Validates batch usage log payloads for `/api/usage/`.
  - `UserSettingsSerializer`: Handles partial updates to user settings (focus toggle, schedule times, site lists).
  - `SiteLimitSerializer`, `CategoryOverrideSerializer`, `FocusSessionSerializer`: CRUD serialization.
* **Interacts With:** `models.py`, `views.py`.

---

### 8. `dashboard/core/views.py`
* **Purpose:** The backend view controller housing REST API endpoints, analytics calculations, and HTML template renderers.
* **Primary Functions:**
  - `auth_page(request)`: Renders the split-screen `auth.html` page.
  - `dashboard_page(request)`: Authenticated view rendering `dashboard.html` with initial context (user, persona, token, settings).
  - `register_view(request)`: `POST /api/auth/register/`. Validates email with `EmailValidator`, creates user and profile, sets `is_verified=True`, seeds demo gamification, generates DRF token, logs user in, and returns `{ redirect: '/dashboard/' }`.
  - `login_view(request)`: `POST /api/auth/login/`. Resolves identifier across username, email, or normalized phone number, authenticates password, and issues DRF token.
  - `logout_view(request)`: Logs user out and flushes the session.
  - `google_auth_view(request)`: `POST /api/auth/google/`. Handles Google Identity Services ID tokens or Quick Demo sign-in, auto-provisioning verified accounts.
  - `regenerate_token_view(request)`: `POST /api/auth/regenerate-token/`. Deletes existing DRF token and generates a new one.
  - `usage_log_view(request)`: `POST /api/usage/`. Ingests batch usage logs from extension, classifying domains and updating daily logs.
  - `summary_view(request)`: `GET /api/summary/`. Central analytics engine. Computes 7-day category totals, today's stats, focus efficiency score, consecutive streak count, 30-day Green Grove forest statuses (`grown`, `withered`, `empty`), and returns user gamification data (`level`, `xp`, `xp_progress`, badges).
  - `settings_view(request)`: `GET/PATCH /api/settings/`. Retrieves and updates user settings, handling schedule times and persona changes.
  - `limits_list_create_view()` & `limits_detail_view()`: CRUD operations for `SiteLimit`.
  - `categories_list_create_view()` & `categories_detail_view()`: CRUD operations for `CategoryOverride`.
  - `sessions_view(request)`: `GET/POST /api/sessions/`. Lists and records focus sessions.
  - `data_export_view(request)`: `GET /api/data/export/`. Exports all user data as a downloadable JSON file.
  - `data_delete_view(request)`: `POST /api/data/delete/`. Completely deletes all browsing logs, site limits, and focus sessions for the authenticated user.
* **Interacts With:** `models.py`, `serializers.py`, `urls.py`, `auth.html`, `dashboard.html`.

---

### 9. `dashboard/core/templates/auth.html`
* **Purpose:** Split-screen authentication interface.
* **Key Features:** 50/50 desktop split layout; brand header with official leaf logo; "Continue with Google" button; email/password form with strict HTML5 and regex validation; toggle between Sign In and Sign Up tabs; demo login shortcuts.
* **Interacts With:** `/api/auth/login/`, `/api/auth/register/`, `/api/auth/google/`, `theme.css`.

---

### 10. `dashboard/core/templates/dashboard.html`
* **Purpose:** The main 3D Neumorphic web dashboard.
* **Key Features:**
  - Top Glassmorphism Header: Greeting, persona selector dropdown, date display, theme switcher, API token display with copy button.
  - Left Sidebar: User avatar, Level & XP progress bar, 3D shiny badges grid (*Zen Master*, *Deep Worker*, *Iron Will*), Priority To-Do planner checklist widget.
  - Main Grid: Focus Mode hero card, 4 KPI cards (Productive Time, Distracting Time, Focus Efficiency, Daily Streak), Focus Goal ring, Chart.js analytics with Bar/Line toggle, 30-Day Green Grove forest visual, Top Distractions list with per-site limit controls, and Data Management panel (Export / Delete).
* **Interacts With:** `/api/summary/`, `/api/settings/`, `/api/limits/`, `/api/data/`, Chart.js, `theme.css`.

---

### 11. `dashboard/core/tests.py`
* **Purpose:** Automated test suite verifying the integrity of the backend API and data models.
* **Test Classes & Methods (16 Total Tests, All Passing):**
  - `RegisterViewTests`: Verifies valid registration, duplicate email rejection, invalid email rejection.
  - `LoginViewTests`: Verifies login with username, login with email, login with phone number, bad password rejection.
  - `GoogleAuthViewTests`: Verifies demo Google login creates and logs in user with verified status.
  - `RegenerateTokenViewTests`: Verifies token invalidation and new token generation.
  - `UsageLogViewTests`: Verifies posting usage deltas, classification, and rate throttling.
  - `SummaryViewTests`: Verifies summary payload structure, stats, weekly totals, grove days, and gamification fields.
  - `SiteLimitTests`: Verifies creating, listing, updating, and deleting per-site limits.
  - `SettingsViewTests`: Verifies retrieving and patching settings (focus toggle, schedule times, persona).
  - `CategoryOverrideTests`: Verifies creating and deleting category overrides.
  - `FocusSessionTests`: Verifies recording completed focus sprint sessions.
  - `DataManagementTests`: Verifies JSON export and total history deletion.
