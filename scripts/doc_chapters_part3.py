# -*- coding: utf-8 -*-
"""
DRIFTLESS Documentation - Chapters 12 to 18
"""

CH_12_FRONTEND = """<h1 id="ch-12">Chapter 12: Frontend Architecture &amp; UI Design</h1>

The DRIFTLESS frontend consists of two distinct presentation applications:
1. **The Chrome Extension Popup (`popup.html` &amp; `popup.js`):** A compact, responsive browser action window.
2. **The Web Dashboard Application (`dashboard.html` &amp; `auth.html`):** A full-featured 3D Neumorphic / Glassmorphic single-page web interface.

Both applications share the **DRIFTLESS Design System**, featuring high-contrast typography, tactile depth, and a dual-theme color architecture.

---

## 12.1 Chrome Extension Popup Interface

The extension popup (`popup.html`) is structured with modular views and interactive modal drawers:

```text
┌────────────────────────────────────────────────────────┐
│  🍃 DRIFTLESS            [🔥 10-Day Streak]  [⚙️ Token] │
├────────────────────────────────────────────────────────┤
│  ⚡ FOCUS MODE                       [ Toggle Switch ]  │
│     Block all distracting sites instantly             │
├────────────────────────────────────────────────────────┤
│  🎬 BLOCK SHORTS & REELS (Student)   [ Toggle Switch ]  │
│     YouTube Shorts & Instagram Reels blocked           │
├────────────────────────────────────────────────────────┤
│  ⏰ SCHEDULED FOCUS                  [ Toggle Switch ]  │
│     Active 08:00 PM to 10:30 PM (Next: Today at 8:00)  │
│     ▼ Edit Times                                       │
│     [ Start: 20:00 ]  [ End: 22:30 ]  [ Save Button ]  │
├────────────────────────────────────────────────────────┤
│  🍅 POMODORO SPRINT                                    │
│     25:00 Focus Phase       [ Start Sprint ]  [ Reset ]│
├────────────────────────────────────────────────────────┤
│  ⏳ DISTRACTING SITES (Global Limit: 60m)  [ + Add ]   │
│     • instagram.com     45s / 2m    [ ⚙️ Limit ]  [ 🗑️ ] │
│     • reddit.com        12m / 20m   [ ⚙️ Limit ]  [ 🗑️ ] │
├────────────────────────────────────────────────────────┤
│  🌱 PRODUCTIVE SITES                      [ + Add ]   │
│     • github.com                    [ Whitelisted ]    │
│     • stackoverflow.com             [ Whitelisted ]    │
├────────────────────────────────────────────────────────┤
│  👤 Connected as student_alex        [ 🔗 Dashboard ]  │
│  🔄 Cloud Sync (Last: Just now)      [ Sync Now ]      │
└────────────────────────────────────────────────────────┘
```

### Key Popup UI Modules:
* **Welcome &amp; Persona Onboarding (`onboardingView`):** Displayed when `userPersona` is uninitialized. Steps user through initial brand introduction and persona selection.
* **Scheduled Focus Collapsible Drawer:** Expands when Scheduled Focus is active or tapped. Houses two HTML5 `<input type="time">` pickers, displays human-readable 12-hour formatted labels, and includes an explicit **Save** button.
* **Custom Limit Modal (`customLimitModal`):** Prompts for per-site minutes (1 to 1440) or provides a "Remove Limit" button to fall back to the global limit.
* **Global Limit Modal (`globalLimitModal`):** Modifies default limit for unconfigured distracting sites.

---

## 12.2 Web Dashboard Architecture (`dashboard.html`)

The web dashboard employs a modern **3D Neumorphic / Glassmorphic** aesthetic:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  🍃 DRIFTLESS  [ 👨‍🎓 Student ▼ ]     [ 🌓 Theme ]  [ 🔑 API Token ]  [ Logout ] │
├──────────────────────┬───────────────────────────────────────────────────────┤
│  SIDEBAR             │  MAIN WORKSPACE                                       │
│                      │                                                       │
│  [ Avatar ]          │  ⚡ FOCUS MODE STATUS CARD                             │
│  student_alex        │     [ ON / OFF Switch ]  Status: Focus Mode Active    │
│  LVL 5               │                                                       │
│  [================-] │  4 KPI CARDS (3D Layered Shadows):                    │
│  80 / 100 XP (80%)   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐ │
│                      │  │ 3h 45m    │ │ 25m       │ │ 90%       │ │ 🔥 10  │ │
│  MY BADGES (3D):     │  │ Productive│ │Distracting│ │ Efficiency│ │ Streak │ │
│  ┌────────────────┐  │  └───────────┘ └───────────┘ └───────────┘ └────────┘ │
│  │ 🧘‍♂️ Zen Master  │  │                                                       │
│  └────────────────┘  │  🎯 3-HOUR DAILY FOCUS GOAL RING                       │
│  ┌────────────────┐  │     Circular SVG Progress Ring (125% Goal Achieved)   │
│  │ 🧠 Deep Worker │  │                                                       │
│  └────────────────┘  │  📊 ANALYTICS CHART [ Bar Chart ] [ Line Chart ]       │
│  ┌────────────────┐  │     Weekly category dwell breakdown (Productive vs    │
│  │ 🛡️ Iron Will   │  │     Distracting vs Others)                            │
│  └────────────────┘  │                                                       │
│                      │  🌲 30-DAY GREEN GROVE FOREST                         │
│  PRIORITY TO-DOS:    │     30 tactile tree icons (Pine = Success,            │
│  [ Task input... ]   │     Withered = Exceeded, Empty = No Data)             │
│  [x] Complete paper  │                                                       │
│  [ ] Review PR #42   │  🛑 TOP DISTRACTIONS & SITE LIMITS                    │
│  [ 1 / 2 Done ]      │     Per-domain limit editor with live progress bars   │
└──────────────────────┴───────────────────────────────────────────────────────┘
```

### Neumorphic &amp; 3D CSS Design System:
* **Dual Drop Shadows:** Cards utilize opposing layered shadows:
  ```css
  box-shadow: 8px 8px 16px rgba(0, 0, 0, 0.06), -8px -8px 16px rgba(255, 255, 255, 0.8);
  ```
* **Glassmorphic Navigation:** Top header and sidebar feature:
  ```css
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  ```
* **Animated XP Bar:** Features shimmering light bars and smooth CSS width transitions.
* **3D Metallic Badges:** Features metallic bevel borders, tactile drop shadows, and a 45-degree animated sheen sweep on hover (`.badge-sheen`).
* **Priority To-Do Planner:** Interactive daily checklist widget saving directly to `localStorage['driftless_priority_todos']`.

---

## 12.3 Split-Screen Authentication UI (`auth.html`)
Inspired by modern SaaS interfaces:
* **Left Branding Panel (45%):** Displays the official green leaf "D" brand logo, large typography, and value proposition feature highlights.
* **Right Auth Card (55%):** Form card (max-width: 440px) featuring:
  - Prominent "Continue with Google" button with official Google SVG mark.
  - "or continue with email" horizontal divider.
  - High-contrast inputs (48px height) with emerald focus rings.
  - Strict client-side email format regex validation.
  - Instant direct sign-in and sign-up with demo shortcuts.

---

## 12.4 Dual-Theme Token Architecture (`theme.css`)
DRIFTLESS supports two palettes toggled via `localStorage['driftless-theme']`:
1. **Calm Sky (Light Mode):** Clean slate background (`#f8fafc`), crisp white cards, and ocean blue / emerald accents.
2. **Opal Noir (Dark Mode):** Deep obsidian background (`#090d16`), elevated dark slate cards (`#131b2e`), and luminescent cyan / emerald glows.
"""

CH_13_WORKFLOWS = """<h1 id="ch-13">Chapter 13: End-to-End Workflows as Diagrams</h1>

This chapter details the 8 core operational workflows of the DRIFTLESS platform, illustrating the exact sequence of events, message exchanges, and data state transitions.

---

### Workflow 1: Precision Active Tab Dwell Tracking
Solves service worker idling by using an active tab heartbeat script to emit 1-second ticks.

![Workflow 1: Active Tab Dwell Tracking](diagrams/workflow_1_tracking.svg)

1. User focuses on tracked site (e.g. `reddit.com`).
2. `content.js` detects `!document.hidden && document.hasFocus()`.
3. Starts 1000ms `setInterval` loop emitting `PAGE_HEARTBEAT_TICK`.
4. `background.js` verifies tab is active in the current window and increments `siteTimes[domain]` by 1 second.
5. `background.js` checks accumulated dwell against 80% nudge and 100% block thresholds.
6. When the user switches tabs or minimizes the window, `content.js` detects `blur` / `visibilitychange`, clears the interval, and sends `PAGE_HEARTBEAT_PAUSE`.
7. `background.js` flushes uncommitted time to storage via `commitActiveTime()`.

---

### Workflow 2: 3-Tier Timer Escalation &amp; DNR Enforcement
Graduated enforcement from gentle notification to complete browser network blocking.

![Workflow 2: Escalation & Enforcement](diagrams/workflow_2_escalation_block.svg)

1. User browses a distracting site with a 2-minute (120s) limit.
2. At 96 seconds (80%), `background.js` fires `sendNudgeNotification()`.
3. If the user continues browsing and reaches 120 seconds (100%), `background.js` fires `sendLimitReachedNotification()`.
4. `background.js` immediately calls `blockDomainViaDNR(domain)`, installing a dynamic DNR rule in the `1000..1999` range.
5. Future network requests to `domain` are intercepted at the browser engine level and redirected to `blocked.html`.
6. Daily limits and DNR rules persist until the midnight alarm (`ALARM_MIDNIGHT_RESET`) executes at `00:00:00`.

---

### Workflow 3: Scheduled Focus Mode Lifecycle
Automated daily focus windows with start and end alarms.

![Workflow 3: Scheduled Focus](diagrams/workflow_3_scheduled_focus.svg)

1. User configures schedule times (e.g. 20:00 to 22:30) in the popup time pickers.
2. User taps "Save Schedule", dispatching `UPDATE_SCHEDULE` message.
3. `background.js` saves times to `chrome.storage.local` and patches `/api/settings/`.
4. `background.js` clears existing alarms and creates `driftless_schedule_start` and `driftless_schedule_end`.
5. At 20:00, `driftless_schedule_start` fires, calling `enableFocusMode()` to inject DNR rules 100..899.
6. At 22:30, `driftless_schedule_end` fires, calling `disableFocusMode()` to remove DNR rules.

---

### Workflow 4: Pomodoro Focus Sprint State Machine
25-minute deep focus sprints followed by 5-minute restorative breaks.

![Workflow 4: Pomodoro Focus Sprint](diagrams/workflow_4_pomodoro.svg)

1. User clicks "Start Pomodoro" in the popup.
2. `background.js` enters `work` mode, enables Focus Mode DNR rules (100..899), and sets `driftless_pomodoro` alarm for 25 minutes.
3. At T+25m, the alarm fires: Focus Mode disengages, audio chime plays, +50 XP is awarded, and `POST /api/sessions/` is recorded.
4. `background.js` enters `break` mode, schedules a 5-minute rest alarm, and unblocks distracting sites.
5. At T+30m, the break ends, and the state machine resets to `idle`.

---

### Workflow 5: Authentication &amp; Persona Onboarding
Frictionless direct registration, Google auth, and initial extension setup.

![Workflow 5: Authentication & Onboarding](diagrams/workflow_5_auth_onboarding.svg)

1. User signs up on `auth.html` or chooses "Continue with Google".
2. Client performs strict email regex validation before form submission.
3. Backend `register_view` validates format with Django's `EmailValidator`, sets `is_verified=True`, seeds demo gamification (Level 5, 80 XP, 3 badges), and returns DRF Token.
4. User is redirected straight to `/dashboard/`.
5. When opening the extension, `popup.js` detects uninitialized persona and presents the Welcome screen.
6. User selects their persona (e.g. Student), auto-populating recommended site lists and suggested schedule.

---

### Workflow 6: Periodic Cloud Synchronization
Batch transmission of local dwell time deltas and bidirectional settings synchronization.

![Workflow 6: Periodic Cloud Sync](diagrams/workflow_6_sync.svg)

1. Every 15 minutes, `ALARM_PERIODIC_SYNC` fires in `background.js` (or user clicks "Sync Now").
2. `background.js` reads `unsyncedDeltas` from `chrome.storage.local`.
3. If deltas exist and API token is present, sends `POST /api/usage/`.
4. DRF ingests the logs and updates SQLite `UsageLog` records.
5. `background.js` fetches `GET /api/settings/` to retrieve any updated site lists, schedule times, or persona changes made on the web dashboard.

---

### Workflow 7: 30-Day Green Grove Forest Calculation
Strict daily habit evaluation classifying days into grown, withered, or empty tree plots.

![Workflow 7: Green Grove Calculation](diagrams/workflow_7_green_grove.svg)

1. Dashboard calls `GET /api/summary/`.
2. Backend loops through past 30 days (`[today - 29 .. today]`).
3. For each day, if total dwell is 0, status is set to `'empty'` (soil plot).
4. If dwell exists, compares every domain against custom `SiteLimit` and global distracting limit.
5. If any limit was breached, status is set to `'withered'`.
6. If all limits were respected, status is set to `'grown'` (+1 to total trees grown).

---

### Workflow 8: Gamification &amp; Reward Unlock
Milestone evaluation awarding XP and unlocking 3D shiny badges.

![Workflow 8: Gamification Reward Flow](diagrams/gamification_reward_flow.svg)

1. User achieves behavioral milestone (10-day streak, 2h focus sprint, limit adherence).
2. Backend verifies rule condition during session logging or summary computation.
3. Model fields (`has_zen_master`, `has_deep_worker`, `has_iron_will`, `level`, `xp`) are updated in SQLite `UserProfile`.
4. Left sidebar of `dashboard.html` renders animated XP progress bar and tactile 3D badges with metallic sheen sweep.
"""

CH_14_PRIVACY = """<h1 id="ch-14">Chapter 14: Privacy &amp; Security Architecture</h1>

DRIFTLESS is designed with a **privacy-first, local-first** philosophy. This chapter conducts an honest audit of what data is collected, how it is handled, and what is explicitly excluded.

---

## 14.1 Honest Content Script Audit (`content.js`)
Earlier documentation claimed that DRIFTLESS operated with "no content scripts". That is **no longer true**. A content script (`extension/content.js`) was added in late October to resolve Manifest V3 service worker throttling.

Because content scripts have technical access to page DOMs, the following boundaries are strictly enforced:

| Property | What `content.js` Reads | What `content.js` NEVER Reads |
| :--- | :--- | :--- |
| **Domain** | Reads `window.location.hostname` (e.g. `reddit.com`) | Does NOT read URL search parameters, hash fragments, or query strings |
| **Full URL** | Reads `window.location.href` ONLY to check if URL matches YouTube Shorts (`/shorts/`) or Instagram Reels (`/reels/`) | Does NOT log, transmit, or store search queries, article titles, or path strings |
| **Page DOM** | **Zero inspection.** Does not touch `document.body`, `document.getElementById`, or HTML nodes | Does NOT read page text, comments, articles, videos, or images |
| **User Input** | **Zero inspection.** No event listeners on `input`, `keydown`, `keypress`, or `change` | Does NOT read passwords, credit card numbers, form inputs, or keystrokes |
| **Cookies / Auth** | **Zero inspection.** Does not read `document.cookie`, `localStorage`, or `sessionStorage` | Does NOT read session tokens, cookies, auth headers, or credentials |

`content.js` operates solely as a **precision stopwatch pulse generator**, confirming whether the user is actively viewing and interacting with the browser tab.

---

## 14.2 Data Collection &amp; Storage Audit

### What Data IS Collected:
* **Account Credentials:** Username, email address, optional phone number, and bcrypt-hashed password (handled via Django standard auth).
* **Domain-Level Dwell Time:** Aggregated seconds spent per domain per calendar date (e.g., `github.com`: 3,600s on `2026-10-31`).
* **User Preferences:** Selected persona, custom per-site limits, schedule start/end times, and blocked/allowed site lists.
* **Gamification Progress:** XP points, user level, and 3 badge unlock booleans.

### What Data is NEVER Collected:
* Full browsing history, page titles, or search queries.
* Incognito browsing dwell time (extension disabled in incognito by default).
* Form inputs, passwords, credit card details, or financial data.
* Webpage contents, personal emails, or private messages.

---

## 14.3 Storage &amp; Transit Security
1. **Local-First Storage:** All real-time second counters and active timer states reside exclusively in the user's browser via `chrome.storage.local`.
2. **Token Authentication:** Extension-to-backend communication utilizes DRF Token Authentication (`Authorization: Token <key>`). Tokens can be instantly revoked and regenerated via `POST /api/auth/regenerate-token/`.
3. **Transport Encryption:** In production, all API communication must be enforced over TLS/HTTPS.
4. **Data Ownership:** The user has sovereign control over their data:
   - `GET /api/data/export/`: Complete 1-click JSON export of all stored data.
   - `POST /api/data/delete/`: Complete 1-click permanent erasure of all browsing logs, site limits, and focus sessions.
"""

CH_15_SETUP = r"""<h1 id="ch-15">Chapter 15: Setup &amp; Execution Guide</h1>

This step-by-step setup guide is written so that any team member, regardless of coding background, can run and test DRIFTLESS locally.

---

## 15.1 Prerequisites
Ensure the following tools are installed on your workstation:
* **Python 3.10+** (Python 3.11, 3.12, or 3.13 recommended)
* **Google Chrome** (or Chromium-based browser such as Brave, Edge, or Arc)
* **Git** (for version control cloning)

---

## 15.2 Step 1: Clone Repository &amp; Set Up Virtual Environment

Open your terminal (PowerShell on Windows, or Bash on macOS/Linux):

```bash
# 1. Clone the repository
git clone https://github.com/aadi8200/driftless.git
cd driftless

# 2. Navigate to dashboard backend directory
cd dashboard

# 3. Create a Python virtual environment
python -m venv venv

# 4. Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

# 5. Install Python dependencies
pip install -r ../requirements.txt
```

---

## 15.3 Step 2: Configure Environment Variables

In the `dashboard/` folder, copy the `.env.example` file to create your `.env` file:

```bash
# On Windows:
copy .env.example .env
# On macOS / Linux:
cp .env.example .env
```

Open `.env` in any text editor. The variable **names** required by the system are:
* `SECRET_KEY`: Django cryptographic signing key (a default is provided for local development).
* `DEBUG`: Set to `True` for local development.
* `ALLOWED_HOSTS`: Set to `127.0.0.1,localhost`.
* `GOOGLE_CLIENT_ID`: (Optional) Google OAuth Client ID for live Google Sign-In.
* `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: (Optional) SMTP credentials.

---

## 15.4 Step 3: Run Database Migrations &amp; Start Server

With your virtual environment activated inside `dashboard/`:

```bash
# 1. Apply database migrations (applies 0001 through 0010)
python manage.py migrate

# 2. (Optional) Run backend tests to verify system health
python manage.py test core

# 3. Start the Django development server
python manage.py runserver 127.0.0.1:8000
```

You should see:
```text
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## 15.5 Step 4: Load Chrome Extension in Developer Mode

1. Open **Google Chrome**.
2. In the URL bar, navigate to: `chrome://extensions/`
3. In the top-right corner, toggle **Developer mode** to **ON**.
4. Click the **Load unpacked** button in the top-left corner.
5. In the file picker dialog, select the `extension/` folder inside your cloned `driftless/` repository.
6. The DRIFTLESS extension card will appear with version **1.1** and the green leaf icon.

---

## 15.6 Step 5: Execute First End-to-End Verification Test

1. **Open Web App:** Navigate to `http://127.0.0.1:8000/` in Chrome.
2. **Sign Up:** Click "Sign Up", enter a valid email address (e.g. `test@driftless.local`) and password, and submit. You will be immediately redirected to the 3D dashboard at `/dashboard/`.
3. **Copy API Token:** In the dashboard header, click **Copy Token**.
4. **Open Extension Popup:** Click the DRIFTLESS leaf icon in the Chrome toolbar.
5. **Complete Onboarding:** On the Welcome screen, click **Get Started**, choose **Student**, and click **Finish Setup**.
6. **Connect API Token:** In the extension popup, expand the settings drawer, paste your API token, and click **Save Token**.
7. **Test Timer Accuracy:**
   - In the popup, locate `instagram.com` (or add it to Distracting Sites).
   - Click the gear icon and set a custom limit of **1 minute**.
   - Open a new tab and browse `https://www.instagram.com`.
   - Keep the tab focused. Watch the live counter in the popup.
   - At ~48 seconds (80%), confirm the desktop nudge notification appears.
   - At 60 seconds (100%), confirm the alert appears and the page redirects to `blocked.html`.
"""

CH_16_LIMITATIONS = """<h1 id="ch-16">Chapter 16: Known Limitations &amp; Technical Debt</h1>

In the interest of full technical transparency, this chapter documents the known limitations, architectural trade-offs, and minor technical debt in the current codebase.

---

## 16.1 Service Worker Cold-Start Latency
* **Behavior:** When the service worker in `background.js` is asleep, an incoming message or alarm requires ~150ms to 250ms to wake the V8 execution context.
* **Impact:** Minimal. `content.js` queues initial ticks safely, and the browser handles message awakening asynchronously.

---

## 16.2 Multi-Window Concurrent Dwell Tracking
* **Behavior:** Dwell tracking checks `sender.tab.active` within its browser window.
* **Limitation:** If a user opens two separate Chrome windows side-by-side on dual monitors and both windows are active, Chrome considers only the single window with OS operating system focus as currently focused. Time is accumulated only on the OS-focused window.

---

## 16.3 Manual Token Copy for Extension Linking
* **Behavior:** The extension does not currently utilize an automated OAuth cookie bridge to inherit the session from `http://127.0.0.1:8000/` automatically.
* **Workaround:** Users copy their API token from the dashboard header and paste it once into the extension popup. It persists indefinitely in `chrome.storage.local`.

---

## 16.4 Declarative Net Request Dynamic Rule Ceiling
* **Behavior:** Chrome enforces a hard ceiling of 5,000 dynamic DNR rules per extension.
* **Impact:** Negligible. DRIFTLESS utilizes rule IDs `100..899` (Focus Mode), `1000..1999` (Limit Blocks), and `2000..2009` (Shorts/Reels), which easily accommodates hundreds of configured domains without approaching the limit.

---

## 16.5 Gmail SMTP Fallback
* **Behavior:** In development mode without valid SMTP credentials, attempting to send email raises connection errors.
* **Solution Implemented:** Email OTP was completely removed in Migration 0009. The application now uses direct registration with strict format validation, avoiding external email delivery dependencies entirely.
"""

CH_17_NOT_BUILT = """<h1 id="ch-17">Chapter 17: Planned &amp; Unbuilt Features</h1>

To prevent any confusion regarding current capabilities versus future roadmap concepts, this chapter explicitly lists features that are **NOT BUILT** in the codebase as of October 31, 2026.

---

## 17.1 Real-World Physical or Monetary Rewards
* **Status:** `NOT BUILT`
* **Clarification:** The DRIFTLESS reward system consists entirely of **digital gamification** (user levels, XP points, 3D shiny badges in the web dashboard, and the 30-day Green Grove visual forest). The codebase does NOT contain integrations with tree-planting non-profits, payment processors, gift card APIs, or physical delivery services.

---

## 17.2 Native Mobile Companion Apps (iOS &amp; Android)
* **Status:** `NOT BUILT`
* **Clarification:** DRIFTLESS is implemented exclusively as a desktop Chrome extension and a responsive web dashboard. No Swift, Kotlin, or React Native mobile applications exist in the repository.

---

## 17.3 Social Sharing of Achievements &amp; Badges
* **Status:** `NOT BUILT`
* **Clarification:** Badges (*Zen Master*, *Deep Worker*, *Iron Will*) and streaks are stored in the user's private database profile and rendered on the private dashboard. There are no public user profile URLs or social media share sheet integrations.

---

## 17.4 Team &amp; Enterprise Workspace Dashboards
* **Status:** `NOT BUILT`
* **Clarification:** DRIFTLESS is designed as an individual personal wellbeing platform. There are no multi-tenant organizational hierarchies, team leaderboards, manager oversight views, or enterprise billing modules.

---

## 17.5 Automated Weekly Email Digest
* **Status:** `NOT BUILT`
* **Clarification:** There is no background cron job or scheduled task generating weekly PDF or HTML email summary digests. Analytics are viewed interactively on the web dashboard.
"""

CH_18_GLOSSARY = """<h1 id="ch-18">Chapter 18: Glossary of Technical Terms</h1>

This glossary provides plain English definitions for technical concepts used throughout this documentation.

* **Alarm (`chrome.alarms`):** A browser-managed scheduling mechanism that wakes up background extension scripts at specified times or recurring intervals without draining system memory.
* **Authentication Token:** A unique cryptographic string (e.g. `4f8a9e2d...`) sent in HTTP request headers (`Authorization: Token <key>`) allowing the backend to verify the user's identity without requiring session cookies.
* **Content Script (`content.js`):** A lightweight JavaScript file injected directly into web pages that can interact with the page environment (such as monitoring tab focus) and communicate with the extension background worker.
* **Cross-Site Request Forgery (CSRF):** A security vulnerability where malicious websites trick a user's browser into executing unauthorized actions on a web application where they are currently authenticated.
* **Declarative Net Request (DNR):** A modern browser API that allows extensions to block or redirect network requests by declaring rules in advance, executed directly by the browser's C++ networking core.
* **Django REST Framework (DRF):** A powerful toolkit for building Web APIs in Python, handling data validation, serialization, authentication, and HTTP response formatting.
* **Dwell Time:** The cumulative active time (measured in seconds) that a user spends actively focused on a specific website domain.
* **Glassmorphism:** A user interface design trend characterized by translucent frosted-glass panels, soft borders, and blurred background layers (`backdrop-filter: blur()`).
* **Manifest V3:** The current generation of the Google Chrome Extension platform, emphasizing performance, privacy, and security by replacing persistent background pages with event-driven service workers.
* **Migration (Django):** Python files (such as `0010_userprofile...`) that record changes to data models and automatically update the database schema without manual SQL authoring.
* **Neumorphism (Soft UI):** A visual design style combining light and dark drop-shadows to give flat user interface cards an elevated, tactile 3D appearance.
* **Object-Relational Mapping (ORM):** A programming technique that allows developers to query and manipulate database tables using Python objects rather than raw SQL statements.
* **Pomodoro Technique:** A time-management methodology dividing deep work into 25-minute uninterrupted sprint intervals separated by 5-minute restorative breaks.
* **Service Worker (`background.js`):** An event-driven background script in Manifest V3 that runs independently of web pages, terminating when idle and waking up only to handle specific events.
"""

print("Loaded Chapters 12 to 18 (Enhanced).")
