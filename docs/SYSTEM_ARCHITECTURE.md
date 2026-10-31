<h1 id="ch-2">Chapter 2: Project Overview</h1>

## 2.1 Problem Statement
In modern computing, personal computers and web browsers are the primary tools for productivity, research, and communication. However, the open nature of the web exposes users to relentless attention-extractive algorithms:
- **Algorithmic Micro-Distractions:** Platforms such as YouTube Shorts, Instagram Reels, Reddit, and Twitter (X) exploit variable reward mechanics to induce infinite scroll sessions, severely disrupting deep focus.
- **Flawed Awareness:** Users rarely perceive how quickly 2-minute visits escalate into 45-minute rabbit holes.
- **Service Worker Throttling Inaccuracies:** Existing browser extensions often fail to track time accurately due to background service worker throttling in modern browsers (such as Chrome Manifest V3), resulting in delayed nudges and enforcement failures.
- **Punitive Rather than Habit-Forming UX:** Standard blockers simply display abrasive error screens without positive reinforcement, streak rewards, or structured sprint frameworks.

## 2.2 Project Objectives
DRIFTLESS is designed as an intelligent, compassionate, and robust digital wellbeing companion built on four pillars:
1. **Second-Level Tracking Precision:** A dedicated content script heartbeat (`extension/content.js`) coupled with service worker dwell commits (`extension/background.js`) guarantees second-accurate time tracking without reading DOM contents or violating user privacy.
2. **3-Tier Graduated Escalation:** Rather than harsh immediate cut-offs, DRIFTLESS gently nudges users at 80% of their site limit, issues a firm alert at 100%, and enforces full network blocking via Chrome's native Declarative Net Request engine.
3. **Structured Focus Regimes:** Built-in **Scheduled Focus Mode** (with compact inline time pickers) and **Pomodoro Sprints** (25-minute work intervals and 5-minute restorative breaks) create disciplined work windows.
4. **Positive Gamification & Visual Habit Reinforcement:** Users earn XP, level up, unlock tactile 3D metallic badges (*Zen Master*, *Deep Worker*, *Iron Will*), cultivate a 30-day **Green Grove** forest, and maintain consecutive daily streaks.

## 2.3 User Personas & Default Configuration
DRIFTLESS recognizes that productivity is highly subjective. What is distracting for a software engineer (e.g., social media feeds) may be essential research for a social media creator. DRIFTLESS supports five customizable personas:

| Persona | Core Objective | Recommended Distracting Sites | Recommended Productive Sites | Suggested Focus Schedule |
| :--- | :--- | :--- | :--- | :--- |
| **Student** | Academic study, coding, course completion, exam prep | `instagram.com`, `facebook.com`, `reddit.com`, `youtube.com` | `github.com`, `stackoverflow.com`, `docs.google.com`, `geeksforgeeks.org` | 20:00 to 22:30 |
| **Professional** | Deep work, asynchronous communication, engineering | `instagram.com`, `facebook.com`, `youtube.com`, `x.com` | `github.com`, `docs.google.com`, `notion.so`, `stackoverflow.com` | 09:00 to 12:00 |
| **Influencer** | Content curation, client outreach, asset management | `facebook.com`, `reddit.com`, `netflix.com`, `x.com` | `canva.com`, `docs.google.com`, `drive.google.com`, `notion.so` | 14:00 to 17:00 |
| **Creator** | Visual design, video editing, portfolio building | `facebook.com`, `reddit.com`, `netflix.com`, `x.com` | `canva.com`, `figma.com`, `behance.net`, `docs.google.com` | 10:00 to 13:00 |
| **Other** | General self-improvement and balanced browsing | `instagram.com`, `youtube.com`, `facebook.com`, `reddit.com` | `github.com`, `docs.google.com`, `stackoverflow.com`, `coursera.org` | 19:00 to 21:00 |

*Note on Student Persona Privilege:* To combat the epidemic of short-form video consumption during study hours, the **Shorts & Reels Blocker** switch is exclusively illuminated and accessible when the active persona is set to **Student**.

## 2.4 System Architecture Overview
The DRIFTLESS platform operates as a cohesive distributed system consisting of three primary tiers:
1. **Client Browser Tier (Chrome Extension Manifest V3):** Executes passive tracking via `content.js`, manages background alarms and Declarative Net Request rules in `background.js`, and exposes user controls in `popup.html`/`popup.js`.
2. **Backend Services Tier (Django 4.2+ / DRF):** Ingests batch usage deltas, provides analytics summaries, evaluates streak and grove algorithms, exposes REST endpoints, and manages user accounts.
3. **Presentation & Dashboard Tier (Web Application):** Features a modern 3D Neumorphic / Glassmorphic dashboard with dual-theme capability (Calm Sky / Opal Noir), animated XP bars, 3D shiny badges, a Priority To-Do planner, and Chart.js analytics.

![DRIFTLESS System Architecture](diagrams/system_architecture.svg)

## 2.5 Implementation Status Summary Table
Below is the executive summary of implementation health as determined during the October 31, 2026 codebase audit:

| System Subsystem | Component / Feature | Audit Status | Verification Method |
| :--- | :--- | :--- | :--- |
| **Authentication** | Direct Registration with `EmailValidator` | `IMPLEMENTED AND TESTED` | Django test suite: `RegisterViewTests` passed |
| **Authentication** | Multi-Identifier Login (User/Email/Phone) | `IMPLEMENTED AND TESTED` | Django test suite: `LoginViewTests` (3 tests passed) |
| **Authentication** | Google Sign-In & One-Tap Integration | `IMPLEMENTED AND TESTED` | Django test suite: `GoogleAuthViewTests` passed |
| **Authentication** | DRF Token Generation & Regeneration | `IMPLEMENTED AND TESTED` | Django test suite: `RegenerateTokenViewTests` passed |
| **Authentication** | Email OTP System | `NOT BUILT` | Removed in migration 0009; replaced by direct registration |
| **Tracking Engine** | Active Tab Content Script Heartbeat (1s) | `IMPLEMENTED, NOT TESTED` | Verified in code (`content.js`); stopwatch test not run |
| **Tracking Engine** | Service Worker Dwell Delta Accumulation | `IMPLEMENTED, NOT TESTED` | Verified in code (`background.js:1008-1154`) |
| **Enforcement** | 3-Tier Escalation (80% Nudge, 100% DNR Block) | `IMPLEMENTED, NOT TESTED` | Verified in code (`background.js:1120-1139`) |
| **Enforcement** | Shorts & Reels Blocker (Student Persona) | `IMPLEMENTED, NOT TESTED` | Verified in code (`background.js:388-428`, DNR rules 2001-2002) |
| **Focus Regimes** | Scheduled Focus Mode (Time Pickers & Alarms) | `IMPLEMENTED, NOT TESTED` | Verified in code (`popup.js:170`, `background.js:534`) |
| **Focus Regimes** | Pomodoro Focus Sprint (25m Focus / 5m Break) | `IMPLEMENTED, NOT TESTED` | Verified in code (`popup.js:770`, `background.js:1400`) |
| **Cloud Sync** | Periodic Delta Ingestion (`/api/usage/`) | `IMPLEMENTED AND TESTED` | Django test suite: `UsageLogViewTests` passed |
| **Cloud Sync** | Settings Synchronization (`/api/settings/`) | `IMPLEMENTED AND TESTED` | Django test suite: `SettingsViewTests` passed |
| **Analytics** | Unified Analytics Summary (`/api/summary/`) | `IMPLEMENTED AND TESTED` | Django test suite: `SummaryViewTests` passed |
| **Analytics** | Strict Consecutive Streak Algorithm | `IMPLEMENTED AND TESTED` | Code verified in `views.py:380-450`, tests passed |
| **Habit Grove** | 30-Day Green Grove Forest Status Engine | `IMPLEMENTED AND TESTED` | Code verified in `views.py:552-649`, test suite passed |
| **Gamification** | Leveling, XP Progression & 3D Badges | `IMPLEMENTED AND TESTED` | Code verified in `models.py:50`, test suite passed |
| **Dashboard UI** | 3D Neumorphism & Glassmorphism Design | `IMPLEMENTED, NOT TESTED` | Visually styled in `dashboard.html` and `theme.css` |
| **Dashboard UI** | Priority To-Do Planner Widget | `IMPLEMENTED, NOT TESTED` | Client-side `localStorage` logic in `dashboard.html` |
| **Data Privacy** | 1-Click JSON Data Export & History Deletion | `IMPLEMENTED AND TESTED` | Django test suite: `DataManagementTests` passed |
| **Rewards** | Real-World Monetary / Physical Rewards | `NOT BUILT` | Verified in code: purely digital badges and trees |


---

<h1 id="ch-13">Chapter 13: End-to-End Workflows as Diagrams</h1>

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
