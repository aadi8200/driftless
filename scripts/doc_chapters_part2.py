# -*- coding: utf-8 -*-
"""
DRIFTLESS Documentation - Chapters 7 to 11
"""

CH_7_FILE_BY_FILE = """<h1 id="ch-7">Chapter 7: File-by-File Analysis</h1>

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
"""

CH_8_EXTENSION_ARCH = """<h1 id="ch-8">Chapter 8: Chrome Extension Architecture</h1>

The DRIFTLESS browser extension is built on **Google Chrome Manifest V3**. This chapter details the service worker lifecycle, timer mechanics, escalation engine, blocking rules, schedule automation, and inter-process messaging catalog.

## 8.1 Service Worker Lifecycle & Precision Heartbeat
Under Manifest V3, background pages are replaced by **ephemeral service workers**. A service worker is started by browser events (such as alarms, tab focus changes, or runtime messages) and is automatically terminated by Chrome after approximately 30 seconds of inactivity.

### The 1-Second Heartbeat Pipeline
Standard background `setInterval` timers stop firing when the worker terminates, causing timer lag. DRIFTLESS overcomes this via an active tab heartbeat architecture:
1. `extension/content.js` runs in the page execution context on every standard HTTP/HTTPS page.
2. It monitors `visibilitychange`, `window.focus`, and `window.blur`.
3. When `!document.hidden && document.hasFocus()`, it executes a 1000ms interval loop.
4. Each second, it sends `PAGE_HEARTBEAT_TICK` to `background.js`.
5. The message wakes the service worker (if suspended), allowing `background.js` to accumulate active dwell time second-by-second into `siteTimes` in `chrome.storage.local`.
6. When the tab loses focus, `content.js` clears its interval and sends `PAGE_HEARTBEAT_PAUSE`, prompting `background.js` to execute `commitActiveTime()` and prevent phantom dwell accumulation.

![Precision Tracking Workflow](diagrams/workflow_1_tracking.svg)

## 8.2 3-Tier Escalation Engine & DNR Enforcement
DRIFTLESS enforces site limits through a graduated 3-tier escalation pipeline rather than sudden punitive cutoffs:

```text
[ Browsing Distracting Site ]
             │
             ▼ (Accumulated Seconds >= 80% Limit)
  Tier 1: 80% Gentle Nudge
  • state.nudged = true
  • sendNudgeNotification(domain)
  • "Almost at your daily limit! Consider wrapping up."
             │
             ▼ (Accumulated Seconds >= 100% Limit)
  Tier 2: 100% Limit Alert
  • state.blocked = true
  • sendLimitReachedNotification(domain)
  • "Daily limit reached. This site is now locked until midnight."
             │
             ▼ (Immediate DNR Dynamic Rule Injection)
  Tier 3: Declarative Net Request Block & Redirection
  • Injects DNR rule in ID range 1000..1999
  • content.js receives { blocked: true } -> redirects to blocked.html
  • Future network requests intercepted at browser engine level
```

![Escalation and Enforcement Workflow](diagrams/workflow_2_escalation_block.svg)

## 8.3 Declarative Net Request (DNR) Rule ID Catalog
DRIFTLESS segments its dynamic Declarative Net Request rules into distinct, collision-free numeric bands:

| Numeric Range | Rule Purpose | Action | Condition | Triggering Event |
| :--- | :--- | :--- | :--- | :--- |
| **`100` to `899`** | Manual Focus Mode & Scheduled Focus | `block` | `urlFilter: "||domain"`, all resource types | Focus Mode enabled, Scheduled start alarm |
| **`1000` to `1999`** | Per-Site 100% Limit Enforcement | `block` | `urlFilter: "||domain"`, all resource types | Accumulated time breaches 100% daily limit |
| **`2000` to `2009`** | Shorts & Reels Blocker | `block` | Rule 2001: `||youtube.com/shorts*`<br>Rule 2002: `||instagram.com/reels*` | Shorts & Reels toggle (Student persona) |

All rules specify `priority: 1` and target resource types: `main_frame`, `sub_frame`, `xmlhttprequest`, `script`, `image`, `stylesheet`, `font`, `media`, `websocket`, and `other`.

## 8.4 Scheduled Focus Mode Automation
Scheduled Focus allows users to establish daily recurring deep work windows (e.g., 20:00 to 22:30).
* **Alarms:** `background.js` schedules two daily Chrome alarms:
  - `driftless_schedule_start`: Fires at `schedule_start`.
  - `driftless_schedule_end`: Fires at `schedule_end`.
* **State Check:** On startup or schedule update, `evaluateScheduleState()` calls `isWithinScheduleWindow()`. If the current time is currently within the window, Focus Mode is automatically activated.
* **Midnight Crossing:** If `schedule_end < schedule_start` (e.g. 23:00 to 01:00), the window spans across midnight: time is within the window if `current >= start OR current < end`.

![Scheduled Focus Workflow](diagrams/workflow_3_scheduled_focus.svg)

## 8.5 Pomodoro Sprint State Machine
The Pomodoro feature implements structured sprint intervals:
* **Work Phase (25 Minutes):** User clicks "Start Pomodoro". Focus Mode is engaged (DNR rules 100..899 active). Chrome alarm `driftless_pomodoro` is scheduled for 25 minutes.
* **Completion & Transition:** At T+25m, the alarm fires. A desktop chime and notification alert the user. Focus Mode disengages, a `FocusSession` record is synced to `/api/sessions/`, +50 XP is awarded, and a 5-minute break alarm is scheduled.
* **Break Phase (5 Minutes):** Distracting sites are unblocked. Popup displays a relaxing green countdown timer.

![Pomodoro Sprint Workflow](diagrams/workflow_4_pomodoro.svg)

## 8.6 Cloud Synchronization & Midnight Reset
* **Periodic Sync (`ALARM_PERIODIC_SYNC`):** Scheduled with `periodInMinutes: 15`. Gathers `unsyncedDeltas` from `chrome.storage.local`, posts them to `POST /api/usage/`, fetches updated settings from `GET /api/settings/`, and resets `unsyncedDeltas`.
* **Midnight Reset (`ALARM_MIDNIGHT_RESET`):** Calculates exact milliseconds until local midnight (`00:00:00.050`). At midnight, clears `siteTimes`, resets `escalationState`, strips limit DNR rules `1000..1999`, and reschedules the alarm for the next midnight.

## 8.7 Complete Message Catalog
Below is the definitive catalog of all 14 message types handled by `background.js` via `chrome.runtime.onMessage.addListener`:

| Message Type | Direction | Payload Schema | Action Performed | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `PAGE_HEARTBEAT_TICK` | `content.js` -> `background.js` | `{ type, domain, url, timestamp }` | Validates active tab, increments dwell seconds, checks 80%/100% limits | `{ blocked, domain, elapsed, limit, nudgeAt }` |
| `PAGE_HEARTBEAT_PAUSE` | `content.js` -> `background.js` | `{ type, domain, timestamp }` | Flushes active dwell delta, marks tab inactive | `{ success: true }` |
| `SET_FOCUS_MODE` | `popup.js` -> `background.js` | `{ type, enabled: boolean }` | Toggles Focus Mode DNR rules (100..899), syncs to backend | `{ success: true, focusModeActive: boolean }` |
| `UPDATE_SCHEDULE` | `popup.js` -> `background.js` | `{ type, scheduleEnabled, scheduleStart, scheduleEnd }` | Saves schedule times, recreates start/end alarms, re-evaluates window | `{ success: true, scheduleEnabled, ... }` |
| `UPDATE_SITE_LISTS` | `popup.js` -> `background.js` | `{ type, distractingSites, productiveSites }` | Updates storage site lists, re-evaluates active focus rules, syncs to backend | `{ success: true }` |
| `SET_GLOBAL_LIMIT` | `popup.js` -> `background.js` | `{ type, limitMinutes: number }` | Updates `userTimeLimitMinutes`, syncs to `/api/settings/` | `{ success: true }` |
| `SET_CUSTOM_LIMIT` | `popup.js` -> `background.js` | `{ type, domain, limitMinutes }` | Sets per-domain limit, syncs `POST /api/limits/` | `{ success: true }` |
| `REMOVE_CUSTOM_LIMIT` | `popup.js` -> `background.js` | `{ type, domain }` | Removes custom limit, syncs `DELETE /api/limits/<id>/` | `{ success: true }` |
| `TRIGGER_SYNC` | `popup.js` -> `background.js` | `{ type }` | Triggers immediate `syncToBackend()` push and pull | `{ success: true }` |
| `RESET_ALL_TIMERS` | `popup.js` -> `background.js` | `{ type }` | Resets today's `siteTimes` and `escalationState` in storage | `{ success: true }` |
| `TOGGLE_SHORTS_REELS`| `popup.js` -> `background.js` | `{ type, enabled: boolean }` | Toggles DNR dynamic rules 2001 & 2002 for Shorts/Reels | `{ success: true, enabled: boolean }` |
| `START_POMODORO` | `popup.js` -> `background.js` | `{ type }` | Starts 25m work phase, activates focus DNR rules, sets alarm | `{ success: true, state: "running", mode: "work" }` |
| `STOP_POMODORO` | `popup.js` -> `background.js` | `{ type }` | Cancels Pomodoro alarm, deactivates focus rules, resets state | `{ success: true, state: "idle" }` |
| `PAUSE_POMODORO` | `popup.js` -> `background.js` | `{ type }` | Pauses Pomodoro timer and records remaining time | `{ success: true, state: "paused" }` |
"""

CH_9_DJANGO_BACKEND = """<h1 id="ch-9">Chapter 9: Django Backend Architecture</h1>

The DRIFTLESS backend is constructed using **Django 4.2+** and **Django REST Framework (DRF 3.17+)**. This chapter examines configuration settings, data models, serialization logic, analytics computations, streak algorithms, Green Grove calculations, and gamification mechanics.

## 9.1 Settings & Configuration Architecture
Key settings in `dashboard/driftless/settings.py`:
* **CORS & CSRF:** Configured for cross-origin extension communication and local development.
* **REST Framework Configuration:**
  - `DEFAULT_AUTHENTICATION_CLASSES`: `TokenAuthentication` and `SessionAuthentication`.
  - `DEFAULT_PERMISSION_CLASSES`: `IsAuthenticated` (view-level overrides for auth routes).
  - Rate Throttling: `SyncRateThrottle` limits sync ingestion to 120 requests/minute per authenticated user.
* **Security & Secret Hygiene:** Secrets are loaded from environment variables (`.env`). In development, fallback placeholders are provided for local presentation.

## 9.2 Domain Normalization & Classification Engine
All web traffic processed by the backend is routed through normalization and categorization functions in `dashboard/core/models.py`:
* **`clean_domain(url)`:** Strips protocol schemes (`http://`, `https://`), path segments, and leading `www.` subdomains.
* **`classify_domain(domain, user=None)`:** Determines the category:
  1. Checks if the user has an explicit record in `CategoryOverride`.
  2. Checks static `CATEGORY_MAP` (covering 45+ popular websites).
  3. Checks academic TLD regex (`.edu`, `.ac.uk`, `.org`).
  4. Defaults to `CATEGORY_OTHERS` (`'Others'`).

Standardized Categories (Migration 0006):
- `Productive sites`
- `Distracting sites`
- `Others`

## 9.3 Analytics & Streak Calculation Algorithm
In `dashboard/core/views.py:summary_view()`, analytics and streaks are computed strictly:
1. **Focus Efficiency Score:**
   $$\\text{Efficiency} = \\frac{\\text{Productive Seconds}}{\\text{Productive Seconds} + \\text{Distracting Seconds}} \\times 100$$
2. **Strict Consecutive Daily Streak:**
   - Evaluates consecutive days descending from yesterday back to 60 days.
   - For each day, the day is considered **successful** if:
     - Total logged seconds > 0.
     - No custom `SiteLimit` was exceeded.
     - Total unconfigured distracting time did NOT exceed `global_limit_minutes`.
     - Total productive focus time met or exceeded `focus_goal_minutes` (if configured).
   - The first day that breaches any limit terminates the streak count.

## 9.4 Green Grove 30-Day Forest Status Engine
The Green Grove visualizer calculates progress across the preceding 30 days (`views.py:552-649`):
* For each day in `[today - 29 days .. today]`:
  - **`status = 'empty'`:** No browsing dwell logs exist for that date (`total_seconds == 0`). Rendered as an empty soil plot.
  - **`status = 'grown'`:** User logged browsing activity and stayed strictly within all per-site and global distracting limits. Rendered as a healthy green pine tree.
  - **`status = 'withered'`:** User exceeded either a custom site limit or the global distracting limit. Rendered as a withered amber/gray tree.

![Green Grove Calculation Workflow](diagrams/workflow_7_green_grove.svg)

## 9.5 Gamification & Reward Engine
DRIFTLESS implements an ethical digital gamification system designed to reinforce habit formation without misleading financial claims:
* **Database Fields (`UserProfile`):** `level` (Integer), `xp` (Integer), and three badge flags: `has_zen_master`, `has_deep_worker`, `has_iron_will`.
* **Milestone Rules:**
  - 🧘‍♂️ **Zen Master:** Awarded for maintaining a 10-day focus streak without limit violations.
  - 🧠 **Deep Worker:** Awarded for completing 2+ hours (120 minutes) of deep focus sprints.
  - 🛡️ **Iron Will:** Awarded for immediate limit compliance (closing a distracting site upon receiving the 80% nudge).
* **Presentation Demo Helper (`seed_demo_gamification`):** Pre-seeds Level 5, 80 XP progress, and unlocks all 3 badges on initial registration or demo login.
* **API Delivery:** Returned via `GET /api/summary/` inside the `user` dictionary: `{ level, xp, xp_progress, has_zen_master, has_deep_worker, has_iron_will }`.

![Gamification Reward Flow](diagrams/gamification_reward_flow.svg)

## 9.6 Evolution of Authentication: Email OTP Removal
In earlier development (Migration 0008), an `EmailOTP` model was introduced to send 6-digit codes via Gmail SMTP. To ensure frictionless user onboarding during live presentations and avoid third-party email delivery delays, the OTP system was **completely removed in Migration 0009**:
* Removed `EmailOTP` model and its database table.
* Removed OTP generation, email dispatch, and verification endpoints.
* Replaced with streamlined direct registration: strict frontend regex validation, backend `EmailValidator` check, immediate `is_verified=True`, demo gamification seeding, DRF token generation, and instant redirect to `/dashboard/`.
"""

CH_10_API_REF = """<h1 id="ch-10">Chapter 10: Complete API Reference</h1>

This chapter details every REST API endpoint exposed by the DRIFTLESS backend. All endpoints are prefixed with `/api/` and return `application/json`.

---

### 1. Register User
* **Endpoint:** `POST /api/auth/register/`
* **Authentication:** None (Public)
* **Handler:** `dashboard/core/views.py:register_view()`
* **Request Body:**
  ```json
  {
    "username": "student_alex",
    "email": "alex@university.edu",
    "password": "SecurePassword123!",
    "phone": "+15551234567",
    "persona": "student"
  }
  ```
* **Success Response (`201 Created`):**
  ```json
  {
    "success": true,
    "token": "4f8a9e2d1c3b5a7e9f0d2c4b6a8e0f1d3c5b7a9e",
    "username": "student_alex",
    "is_verified": true,
    "redirect": "/dashboard/"
  }
  ```
* **Error Response (`400 Bad Request`):**
  ```json
  {
    "error": "Please enter a valid email address.",
    "email": ["Please enter a valid email address."]
  }
  ```

---

### 2. Login User
* **Endpoint:** `POST /api/auth/login/`
* **Authentication:** None (Public)
* **Handler:** `dashboard/core/views.py:login_view()`
* **Request Body:** Accepts `username`, `email`, or `phone` in the identifier field:
  ```json
  {
    "username": "alex@university.edu",
    "password": "SecurePassword123!"
  }
  ```
* **Success Response (`200 OK`):**
  ```json
  {
    "success": true,
    "token": "4f8a9e2d1c3b5a7e9f0d2c4b6a8e0f1d3c5b7a9e",
    "username": "student_alex",
    "is_verified": true,
    "redirect": "/dashboard/"
  }
  ```

---

### 3. Google Sign-In & Demo Auth
* **Endpoint:** `POST /api/auth/google/`
* **Authentication:** None (Public)
* **Handler:** `dashboard/core/views.py:google_auth_view()`
* **Request Body:** Real Google ID token OR Demo payload:
  ```json
  {
    "email": "alex.demo@gmail.com",
    "name": "Alex Demo",
    "demo": true
  }
  ```
* **Success Response (`200 OK` / `201 Created`):**
  ```json
  {
    "success": true,
    "token": "4f8a9e2d1c3b5a7e9f0d2c4b6a8e0f1d3c5b7a9e",
    "username": "alex_demo",
    "email": "alex.demo@gmail.com",
    "name": "Alex Demo",
    "redirect": "/dashboard/"
  }
  ```

---

### 4. Regenerate API Token
* **Endpoint:** `POST /api/auth/regenerate-token/`
* **Authentication:** Session or Token (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:regenerate_token_view()`
* **Success Response (`200 OK`):**
  ```json
  {
    "token": "8a7e9f0d2c4b6a8e0f1d3c5b7a9e4f8a9e2d1c3b"
  }
  ```

---

### 5. Ingest Usage Dwell Logs
* **Endpoint:** `POST /api/usage/`
* **Authentication:** Token (`IsAuthenticated`), Rate Throttled (120/min)
* **Handler:** `dashboard/core/views.py:usage_log_view()`
* **Request Body (Batch Array or Single Object):**
  ```json
  [
    {
      "website_url": "github.com",
      "time_spent_seconds": 360,
      "date": "2026-10-31"
    },
    {
      "website_url": "instagram.com",
      "time_spent_seconds": 120,
      "date": "2026-10-31"
    }
  ]
  ```
* **Success Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "Logged 2 entries successfully"
  }
  ```

---

### 6. Analytics Summary
* **Endpoint:** `GET /api/summary/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:summary_view()`
* **Success Response (`200 OK`):**
  ```json
  {
    "stats": {
      "productive_time": "3h 45m",
      "distracting_time": "25m",
      "focus_efficiency": 90,
      "streak_days": 10,
      "longest_session": "45m"
    },
    "user": {
      "username": "student_alex",
      "persona": "student",
      "level": 5,
      "xp": 80,
      "xp_progress": 80,
      "has_zen_master": true,
      "has_deep_worker": true,
      "has_iron_will": true
    },
    "grove": {
      "days": [
        {
          "date": "2026-10-31",
          "status": "grown",
          "day_name": "Sat",
          "day_num": 31,
          "formatted_date": "Oct 31",
          "total_seconds": 14400
        }
      ],
      "total_grown": 28,
      "current_streak": 10
    },
    "weekly": {
      "labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
      "productive": [120, 150, 180, 200, 210, 190, 225],
      "distracting": [30, 25, 20, 15, 10, 20, 25],
      "others": [10, 15, 10, 5, 10, 15, 10]
    },
    "settings": {
      "focus_mode_active": false,
      "schedule_enabled": true,
      "schedule_start": "20:00",
      "schedule_end": "22:30",
      "blocked_sites": "instagram.com\\nfacebook.com\\nreddit.com\\nyoutube.com",
      "allowed_sites": "github.com\\nstackoverflow.com\\ndocs.google.com"
    }
  }
  ```

---

### 7. Settings Management
* **Endpoint:** `GET /api/settings/` & `PATCH /api/settings/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:settings_view()`
* **Patch Body (Any subset):**
  ```json
  {
    "focus_mode_active": true,
    "schedule_enabled": true,
    "schedule_start": "21:00",
    "schedule_end": "23:00",
    "persona": "professional"
  }
  ```
* **Success Response (`200 OK`):** Returns updated `UserSettingsSerializer` payload plus `persona`.

---

### 8. Per-Site Limits CRUD
* **List / Create:** `GET/POST /api/limits/`
* **Detail / Patch / Delete:** `GET/PATCH/DELETE /api/limits/<int:pk>/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:limits_list_create_view()`, `limits_detail_view()`
* **Create Body:**
  ```json
  {
    "domain": "reddit.com",
    "daily_limit_minutes": 20,
    "enabled": true
  }
  ```
* **Success Response (`201 Created` / `200 OK`):**
  ```json
  {
    "id": 4,
    "domain": "reddit.com",
    "daily_limit_minutes": 20,
    "enabled": true
  }
  ```

---

### 9. Category Overrides CRUD
* **List / Create:** `GET/POST /api/categories/`
* **Delete:** `DELETE /api/categories/<int:pk>/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:categories_list_create_view()`, `categories_detail_view()`
* **Create Body:**
  ```json
  {
    "domain": "news.ycombinator.com",
    "category": "Productive sites"
  }
  ```

---

### 10. Focus Sessions
* **List / Record:** `GET/POST /api/sessions/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:sessions_view()`
* **Record Body:**
  ```json
  {
    "duration_minutes": 25,
    "completed": true
  }
  ```

---

### 11. Privacy & Data Export / Erasure
* **Export:** `GET /api/data/export/`
  - Returns complete JSON export containing `profile`, `settings`, `usage_logs`, `site_limits`, and `focus_sessions`.
* **Erasure:** `POST /api/data/delete/`
  - Completely purges all `UsageLog`, `SiteLimit`, and `FocusSession` records for the user. Returns `{ "status": "success", "message": "All user data deleted" }`.
"""

CH_11_DATABASE_SCHEMA = """<h1 id="ch-11">Chapter 11: Database Schema &amp; Migration History</h1>

This chapter details the relational database schema implemented in SQLite 3 via the Django ORM, followed by the complete chronological migration history.

## 11.1 Relational Entity-Relationship Diagram

![Database ER Diagram](diagrams/database_er_diagram.svg)

## 11.2 Model & Field Reference

### 1. `auth_user` (Django Built-in)
* `id`: `INTEGER [PK]`
* `username`: `VARCHAR(150) [Unique]`
* `email`: `VARCHAR(254)`
* `password`: `VARCHAR(128)` (PBKDF2 SHA-256 hash)
* `is_active`: `BOOLEAN`
* `date_joined`: `DATETIME`

### 2. `core_userprofile` (One-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK, Unique]`
* `phone`: `VARCHAR(32)` (Blank allowed)
* `persona`: `VARCHAR(20)` (Choices: `student`, `professional`, `influencer`, `creator`, `other`)
* `is_verified`: `BOOLEAN` (Default `True`)
* `xp`: `INTEGER` (Default `0`)
* `level`: `INTEGER` (Default `1`)
* `has_zen_master`: `BOOLEAN` (Default `False`)
* `has_deep_worker`: `BOOLEAN` (Default `False`)
* `has_iron_will`: `BOOLEAN` (Default `False`)

### 3. `core_usersettings` (One-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK, Unique]`
* `focus_mode_active`: `BOOLEAN` (Default `False`)
* `daily_limit_minutes`: `POSITIVE_INTEGER` (Default `60`)
* `focus_goal_minutes`: `POSITIVE_INTEGER` (Default `180` - 3 hours)
* `streak_days`: `POSITIVE_INTEGER` (Default `0`)
* `require_challenge`: `BOOLEAN` (Default `False`)
* `blocked_sites`: `TEXT` (Newline-delimited distracting domains)
* `allowed_sites`: `TEXT` (Newline-delimited productive domains)
* `schedule_enabled`: `BOOLEAN` (Default `False`)
* `schedule_start`: `VARCHAR(5)` (Default `'20:00'`)
* `schedule_end`: `VARCHAR(5)` (Default `'22:00'`)
* `updated_at`: `DATETIME`

### 4. `core_usagelog` (Many-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK]`
* `website_url`: `VARCHAR(255)`
* `time_spent_seconds`: `POSITIVE_INTEGER` (Default `0`)
* `category`: `VARCHAR(20)` (Default `'Others'`)
* `date`: `DATE`
* `created_at`: `DATETIME`
* `updated_at`: `DATETIME`

### 5. `core_sitelimit` (Many-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK]`
* `domain`: `VARCHAR(255)`
* `daily_limit_minutes`: `POSITIVE_INTEGER` (Default `30`)
* `enabled`: `BOOLEAN` (Default `True`)
* `created_at`: `DATETIME`
* `updated_at`: `DATETIME`

### 6. `core_categoryoverride` (Many-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK]`
* `domain`: `VARCHAR(255)`
* `category`: `VARCHAR(30)` (Choices: `Productive sites`, `Distracting sites`, `Others`)
* `created_at`: `DATETIME`
* `updated_at`: `DATETIME`

### 7. `core_focussession` (Many-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK]`
* `duration_minutes`: `POSITIVE_INTEGER` (Default `25`)
* `started_at`: `DATETIME`
* `completed`: `BOOLEAN` (Default `True`)

---

## 11.3 Complete Migration History

| Migration File | Key Operations Performed | Rationale |
| :--- | :--- | :--- |
| `0001_initial.py` | Created `UsageLog`, `SiteLimit`, `CategoryOverride` models. | Baseline data schema for tracking and custom limits. |
| `0002_usagelog_category_usersettings.py` | Added `category` field to `UsageLog`; created `UserSettings` model. | Introduced user configuration and initial category tags. |
| `0003_userprofile.py` | Created `UserProfile` model with `phone` and `persona`. | Introduced multi-identifier login and persona support. |
| `0004_alter_userprofile_persona.py` | Expanded persona choices (`student`, `professional`, `influencer`, `creator`, `other`). | Allowed users to customize onboarding presets. |
| `0005_usersettings_allowed_sites_and_more.py` | Added `allowed_sites` and `focus_goal_minutes` to `UserSettings`. | Supported whitelist configuration and 3-hour daily goal ring. |
| `0006_alter_categoryoverride_category_and_more.py` | Standardized category choices to `Productive sites`, `Distracting sites`, `Others`. | Eliminated confusing 4-category split; aligned with modern UX. |
| `0007_usersettings_schedule_enabled_and_more.py` | Added `schedule_enabled`, `schedule_start`, `schedule_end` to `UserSettings`. | Backed Scheduled Focus Mode time-picker controls. |
| `0008_userprofile_is_verified_emailotp.py` | Added `is_verified` to `UserProfile`; created `EmailOTP` model. | Initial implementation of 6-digit email OTP system. |
| `0009_delete_emailotp.py` | Deleted `EmailOTP` model. | Removed email OTP in favor of streamlined direct signup. |
| `0010_userprofile_has_deep_worker_and_more.py` | Added `xp`, `level`, `has_zen_master`, `has_deep_worker`, `has_iron_will` to `UserProfile`. | Backed 3D gamification, XP progression, and badge unlocks. |
"""

print("Loaded Chapters 7 to 11 (Enhanced).")
