# -*- coding: utf-8 -*-
"""
DRIFTLESS Documentation - Chapters 1 to 6
"""

CH_1_COVER = """<div class="cover-page">
  <div class="cover-badge">DRIFTLESS OFFICIAL ENGINEERING REFERENCE</div>
  <h1 class="cover-title">DRIFTLESS</h1>
  <div class="cover-subtitle">Complete Technical Architecture, Implementation Manual &amp; Source Reference</div>
  <p class="cover-desc">Chrome Extension (Manifest V3) &bull; Django 4.2+ REST API Backend &bull; 3D Neumorphic Web Dashboard</p>

  <div class="cover-meta-grid">
    <div class="meta-item"><strong>Document Version:</strong> 2.0.0 (Post-Oct 26 Refactor)</div>
    <div class="meta-item"><strong>Audit &amp; Release Date:</strong> October 31, 2026</div>
    <div class="meta-item"><strong>Target Audience:</strong> Engineering Team, Designers, QA, DevOps</div>
    <div class="meta-item"><strong>Classification:</strong> Authoritative Technical Reference Manual</div>
  </div>
</div>

<div class="section-divider"></div>

<h2 id="how-to-read">How to Read This Document</h2>

<p>This technical manual serves as the single source of truth for the entire <strong>DRIFTLESS</strong> platform as of <strong>October 31, 2026</strong>. All legacy documentation dated October 26, 2026 is superseded by this document due to comprehensive architectural enhancements, new database models, and timer refactoring.</p>

<p>To ensure high productivity and accessibility for all team members, this document follows five foundational standards:</p>
<ul>
  <li><strong>Plain English First:</strong> Whenever a technical word or architecture concept appears for the first time (e.g. <em>Manifest V3</em>, <em>Service Worker</em>, <em>Declarative Net Request</em>, <em>DRF</em>, <em>ORM</em>, <em>Alarm</em>, <em>Content Script</em>), it is immediately defined in simple, non-academic terms. A full glossary is provided in <a href="#ch-18">Chapter 18</a>.</li>
  <li><strong>Early Code Mapping:</strong> To quickly locate which file, function, or API endpoint implements any feature, consult the <a href="#ch-3">Master Table &ldquo;Feature to Code&rdquo; in Chapter 3</a>.</li>
  <li><strong>Four Honest Status Labels:</strong> Every feature is classified using only one of four strict labels:
    <code>IMPLEMENTED AND TESTED</code> (verified in this audit session), <code>IMPLEMENTED, NOT TESTED</code> (verified in code), <code>PARTIAL</code>, or <code>NOT BUILT</code>.
  </li>
  <li><strong>Exact Code Blocks &amp; Zero Character Drop:</strong> Code snippets, regexes, and selectors retain exact characters (e.g. <code>--pri</code>, <code>www.</code>, <code>icons/*</code>, <code>||youtube.com/shorts*</code>).</li>
  <li><strong>Zero Secret Disclosure:</strong> Environment variables and configurations are referenced by variable name only; no credentials or private keys are printed.</li>
</ul>

<div class="toc-container">
  <h2>Table of Contents</h2>
  <div class="toc-grid">
    <div>
      <ol style="padding-left: 20px; margin-bottom: 0;">
        <li><a href="#how-to-read">Cover Page &amp; How to Read This Document</a></li>
        <li><a href="#ch-2">Project Overview &amp; Architecture</a></li>
        <li><a href="#ch-3">Master Table &ldquo;Feature to Code&rdquo;</a></li>
        <li><a href="#ch-4">What Changed Since Oct 26 (Changelog)</a></li>
        <li><a href="#ch-5">Project Structure &amp; Directory Tree</a></li>
        <li><a href="#ch-6">Technology Stack &amp; Architectural Rationale</a></li>
        <li><a href="#ch-7">File-by-File Analysis</a></li>
        <li><a href="#ch-8">Chrome Extension Architecture (Manifest V3)</a></li>
        <li><a href="#ch-9">Django Backend Architecture</a></li>
      </ol>
    </div>
    <div>
      <ol start="10" style="padding-left: 20px; margin-bottom: 0;">
        <li><a href="#ch-10">Complete REST API Reference (20 Endpoints)</a></li>
        <li><a href="#ch-11">Database Schema &amp; Migration History</a></li>
        <li><a href="#ch-12">Frontend Architecture &amp; UI Design</a></li>
        <li><a href="#ch-13">End-to-End Workflows as Diagrams (8 Flows)</a></li>
        <li><a href="#ch-14">Privacy &amp; Security Architecture (content.js)</a></li>
        <li><a href="#ch-15">Setup &amp; Execution Guide (For Non-Coders)</a></li>
        <li><a href="#ch-16">Known Limitations &amp; Technical Debt</a></li>
        <li><a href="#ch-17">Planned &amp; Unbuilt Features (Scope Limits)</a></li>
        <li><a href="#ch-18">Glossary of Technical Terms</a></li>
      </ol>
    </div>
  </div>
</div>
"""

CH_2_OVERVIEW = """<h1 id="ch-2">Chapter 2: Project Overview</h1>

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
"""

CH_3_MASTER_TABLE = """<h1 id="ch-3">Chapter 3: Master Table &ldquo;Feature to Code&rdquo;</h1>

This master traceability table provides immediate mapping between every user-facing feature, the exact files and functions that implement it, its REST endpoints, its database tables, and its audit status as of **October 31, 2026**.

| Feature | What It Does (Plain English) | Files Implementing It | Functions / Handlers | API Endpoints | Database Tables | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **User Registration** | Validates email format, creates account, seeds demo gamification, logs user in immediately. | `dashboard/core/views.py`<br>`dashboard/core/serializers.py`<br>`dashboard/core/templates/auth.html` | `register_view()`<br>`RegisterSerializer.create()`<br>`handleRegister()` | `POST /api/auth/register/` | `auth_user`<br>`core_userprofile`<br>`core_usersettings` | `IMPLEMENTED AND TESTED` |
| **Multi-Identifier Login** | Authenticates user via username, email address, or phone number. | `dashboard/core/views.py`<br>`dashboard/core/templates/auth.html` | `login_view()`<br>`handleLogin()` | `POST /api/auth/login/` | `auth_user`<br>`core_userprofile`<br>`authtoken_token` | `IMPLEMENTED AND TESTED` |
| **Google Sign-In** | Authorizes user via Google Identity Services token or Quick Demo modal. | `dashboard/core/views.py`<br>`dashboard/core/templates/auth.html` | `google_auth_view()`<br>`handleGoogleCredentialResponse()` | `POST /api/auth/google/` | `auth_user`<br>`core_userprofile`<br>`authtoken_token` | `IMPLEMENTED AND TESTED` |
| **Token Regeneration** | Issues a fresh DRF authentication token, invalidating old sessions. | `dashboard/core/views.py`<br>`dashboard/core/templates/dashboard.html` | `regenerate_token_view()`<br>`regenerateToken()` | `POST /api/auth/regenerate-token/` | `authtoken_token` | `IMPLEMENTED AND TESTED` |
| **1-Second Precision Heartbeat** | Emits active dwell tick every 1000ms while tab is focused; bypasses service worker throttling. | `extension/content.js` | `sendTick()`<br>`startHeartbeat()`<br>`handleStateChange()` | None (Extension internal) | None (Local tab state) | `IMPLEMENTED, NOT TESTED` |
| **Passive Dwell Accumulation** | Aggregates active seconds per domain; ignores inactive background tabs and idle periods. | `extension/background.js` | `onMessage` handler (`PAGE_HEARTBEAT_TICK`)<br>`commitActiveTime()` | None (Extension internal) | `chrome.storage.local` (`siteTimes`) | `IMPLEMENTED, NOT TESTED` |
| **80% Nudge Notification** | Sends a gentle desktop notification when user reaches 80% of their daily site limit. | `extension/background.js` | `sendNudgeNotification()`<br>`evaluateSiteLimits()` | None | `chrome.storage.local` (`escalationState`) | `IMPLEMENTED, NOT TESTED` |
| **100% Limit Hard Block** | Dispatches desktop alert and injects Declarative Net Request block rule when 100% reached. | `extension/background.js`<br>`extension/blocked.html` | `sendLimitReachedNotification()`<br>`blockDomainViaDNR()` | None | `chrome.storage.local`<br>DNR Rules 1000..1999 | `IMPLEMENTED, NOT TESTED` |
| **Midnight Dwell Reset** | Automatically resets daily dwell counters and clears DNR limit blocks at 00:00:00. | `extension/background.js` | `performMidnightReset()`<br>`scheduleMidnightReset()` | None | `chrome.storage.local` (`siteTimes`) | `IMPLEMENTED, NOT TESTED` |
| **Manual Focus Mode** | Instant 1-click toggle blocking all distracting sites via dynamic DNR rules. | `extension/popup.js`<br>`extension/background.js`<br>`dashboard/core/templates/dashboard.html` | `toggleFocusMode()`<br>`enableFocusMode()`<br>`disableFocusMode()` | `PATCH /api/settings/` | `core_usersettings`<br>DNR Rules 100..899 | `IMPLEMENTED AND TESTED` |
| **Scheduled Focus Mode** | Lets user set start & end times; auto-engages focus mode during scheduled hours. | `extension/popup.html`<br>`extension/popup.js`<br>`extension/background.js`<br>`dashboard/core/models.py` | `saveScheduleTimes()`<br>`updateScheduleAlarms()`<br>`evaluateScheduleState()` | `PATCH /api/settings/` | `core_usersettings`<br>(`schedule_start`, `schedule_end`) | `IMPLEMENTED, NOT TESTED` |
| **Pomodoro Focus Sprints** | 25-minute deep focus sprint followed by 5-minute restorative break with notification. | `extension/popup.html`<br>`extension/popup.js`<br>`extension/background.js` | `startPomodoro()`<br>`stopPomodoro()`<br>`alarmListener` (`ALARM_POMODORO`) | `POST /api/sessions/` | `core_focussession`<br>`chrome.storage.local` | `IMPLEMENTED, NOT TESTED` |
| **Shorts & Reels Blocker** | Blocks short-form video paths on YouTube (`/shorts*`) and Instagram (`/reels*`) for Student persona. | `extension/popup.html`<br>`extension/popup.js`<br>`extension/background.js` | `toggleShortsReels()`<br>`updateShortsReelsRules()`<br>`isShortsOrReelsUrl()` | None | DNR Rules 2001..2002<br>`chrome.storage.local` | `IMPLEMENTED, NOT TESTED` |
| **Extension Welcome & Persona** | Displays onboarding screen on initial install; lets user choose persona and seeds site lists. | `extension/popup.html`<br>`extension/popup.js` | `checkOnboarding()`<br>`savePersonaAndProceed()` | `PATCH /api/settings/` | `chrome.storage.local` (`userPersona`) | `IMPLEMENTED, NOT TESTED` |
| **Dashboard Persona Selector** | Dropdown on dashboard to switch persona; dynamically adjusts site presets. | `dashboard/core/templates/dashboard.html`<br>`dashboard/core/views.py`<br>`dashboard/core/serializers.py` | `onPersonaChange()`<br>`settings_view()`<br>`apply_persona_defaults()` | `PATCH /api/settings/` | `core_userprofile`<br>`core_usersettings` | `IMPLEMENTED AND TESTED` |
| **Site Lists Configuration** | Lets user add/delete distracting and productive sites with instant storage and cloud sync. | `extension/popup.js`<br>`extension/background.js`<br>`dashboard/core/templates/dashboard.html` | `addSite()`<br>`deleteSite()`<br>`saveSettings()` | `PATCH /api/settings/` | `core_usersettings`<br>(`blocked_sites`, `allowed_sites`) | `IMPLEMENTED AND TESTED` |
| **Custom Site Limits (CRUD)** | Allows custom per-domain time limits (e.g. reddit.com: 20 mins) via modal. | `extension/popup.js`<br>`dashboard/core/views.py`<br>`dashboard/core/models.py` | `saveCustomLimit()`<br>`limits_list_create_view()`<br>`limits_detail_view()` | `GET/POST /api/limits/`<br>`PATCH/DELETE /api/limits/<id>/` | `core_sitelimit` | `IMPLEMENTED AND TESTED` |
| **Domain Categorization** | Automatically categorizes domains as Productive, Distracting, or Others based on master map. | `dashboard/core/models.py`<br>`dashboard/core/views.py` | `classify_domain()`<br>`clean_domain()` | None | `CATEGORY_MAP`<br>`core_categoryoverride` | `IMPLEMENTED AND TESTED` |
| **Usage Delta Batch Ingestion** | Periodically transmits local browsing time deltas to cloud backend (15m alarm or manual). | `extension/background.js`<br>`dashboard/core/views.py`<br>`dashboard/core/serializers.py` | `syncToBackend()`<br>`usage_log_view()`<br>`UsageLogSerializer` | `POST /api/usage/` | `core_usagelog` | `IMPLEMENTED AND TESTED` |
| **Unified Analytics Summary** | Computes 7-day category totals, focus efficiency, streak count, and daily breakdowns. | `dashboard/core/views.py`<br>`dashboard/core/templates/dashboard.html` | `summary_view()`<br>`renderDashboard()`<br>`updateCharts()` | `GET /api/summary/` | `core_usagelog`<br>`core_sitelimit`<br>`core_usersettings` | `IMPLEMENTED AND TESTED` |
| **Strict Streak Calculation** | Computes consecutive days where user stayed within all limits and achieved focus goals. | `dashboard/core/views.py` | `summary_view()` (streak loop) | `GET /api/summary/` | `core_usagelog`<br>`core_sitelimit` | `IMPLEMENTED AND TESTED` |
| **Green Grove 30-Day Forest** | Forest visual: grown tree (success), withered tree (limit breached), empty spot (no data). | `dashboard/core/views.py`<br>`dashboard/core/templates/dashboard.html` | `summary_view()` (`grove` array builder)<br>`renderGrove()` | `GET /api/summary/` | `core_usagelog`<br>`core_sitelimit` | `IMPLEMENTED AND TESTED` |
| **Gamified Level & Badges** | Tracks XP, levels, and unlocks 3D metallic badges (Zen Master, Deep Worker, Iron Will). | `dashboard/core/models.py`<br>`dashboard/core/views.py`<br>`dashboard/core/templates/dashboard.html` | `seed_demo_gamification()`<br>`summary_view()` | `GET /api/summary/` | `core_userprofile`<br>(`level`, `xp`, badges) | `IMPLEMENTED AND TESTED` |
| **Priority To-Do Planner** | Fast daily task manager in sidebar with completion counter and strike-through styling. | `dashboard/core/templates/dashboard.html` | `renderTodos()`<br>`addPriorityTodo()`<br>`toggleTodo()`<br>`deleteTodo()` | None (Client-side) | `localStorage`<br>(`driftless_priority_todos`) | `IMPLEMENTED, NOT TESTED` |
| **Data Privacy & Erasure** | 1-Click JSON data export and total browsing history deletion. | `dashboard/core/views.py`<br>`dashboard/core/templates/dashboard.html` | `data_export_view()`<br>`data_delete_view()`<br>`exportData()`<br>`deleteData()` | `GET /api/data/export/`<br>`POST /api/data/delete/` | `core_usagelog`<br>`core_focussession`<br>`core_sitelimit` | `IMPLEMENTED AND TESTED` |
| **Email OTP Verification** | Email 6-digit code dispatch for verification and password reset. | None (Removed) | None | None | Dropped in migration 0009 | `NOT BUILT` |
| **Physical / Monetary Prizes** | Real trees planted, cash prizes, gift cards, or physical shipments. | None | None | None | None | `NOT BUILT` |
"""

CH_4_CHANGELOG = """<h1 id="ch-4">Chapter 4: What Changed Since Oct 26</h1>

The DRIFTLESS repository underwent intensive engineering between **October 26, 2026** (commit `e14951e`) and **October 31, 2026** (commit `36ecc24`). During this period, **88 files were modified or added**, with **8,635 lines inserted** and **2,067 lines removed**.

The following changelog catalogs all architectural, backend, database, and extension changes introduced after the October 26 documentation was published.

---

### 1. Precision Timer Architecture & Content Script (`content.js`)
* **Problem Addressed:** In Manifest V3, background service workers are suspended after 30 seconds of inactivity. Chrome also throttles timer alarms on inactive tabs. This caused 2-minute custom limits to trigger 4 to 5 minutes late.
* **New File Added:** `extension/content.js` (92 lines). Injected on `<all_urls>` at `document_start`.
* **Mechanism:** Listens to `visibilitychange`, `window.focus`, and `window.blur`. Ticks every 1,000ms only when `!document.hidden && document.hasFocus()`. Sends `PAGE_HEARTBEAT_TICK` to `background.js` and immediately redirects to `blocked.html` if the response indicates the site is blocked.
* **Privacy Assurance:** Does NOT inspect the DOM, form inputs, cookies, or keystrokes; reads only `window.location.hostname` and `href`.

---

### 2. Scheduled Focus Mode with Interactive Time Pickers
* **Problem Addressed:** Previously, Scheduled Focus had a toggle switch but no interface to define start and end times, and alarms were not synchronized with backend settings.
* **Popup UI Additions (`extension/popup.html`, `popup.js`):** Added collapsible time editor with `<input type="time">` pickers for Start and End, validation rejecting identical start and end times while supporting overnight spans crossing midnight (e.g., 22:00 to 02:00), and an explicit **Save** button.
* **Alarms & Background Handlers (`extension/background.js`):** Added `ALARM_SCHEDULE_START` (`driftless_schedule_start`) and `ALARM_SCHEDULE_END` (`driftless_schedule_end`). `updateScheduleAlarms()` calculates exact millisecond offsets and schedules daily alarms. `isWithinScheduleWindow()` checks if the current time falls inside the window on startup or schedule change.
* **Backend Model & Migration:** Added `schedule_enabled` (BooleanField), `schedule_start` (CharField, default `'20:00'`), and `schedule_end` (CharField, default `'22:00'`) to `UserSettings` in **Migration 0007**.
* **API Synchronization:** Handled via `PATCH /api/settings/` and `GET /api/settings/`.

---

### 3. Pomodoro Focus Sprints (25m Focus / 5m Break)
* **New Capability:** Added Pomodoro sprint engine in `extension/popup.html`, `popup.js`, and `background.js`.
* **State Machine:** Manages three states (`idle`, `running`, `paused`) across two modes: `work` (25 minutes, Focus Mode DNR rules active) and `break` (5 minutes, sites unblocked).
* **Alarms & Persistence:** Driven by `ALARM_POMODORO` (`driftless_pomodoro`). Completed sprints dispatch `POST /api/sessions/` to persist `FocusSession` records in SQLite and award +50 XP.

---

### 4. Shorts & Reels Blocker (Student Persona Only)
* **Targeted Intervention:** Distraction study showed short-form algorithmic video feeds are uniquely harmful to students.
* **Popup Switch:** Added "Block Shorts & Reels" switch to `extension/popup.html` (rendered only if persona is `Student`).
* **Declarative Net Request Blocking:** `background.js` reserves Dynamic Rule IDs 2001 and 2002 blocking regex filters `||youtube.com/shorts*` and `||instagram.com/reels*`.

---

### 5. Extension Welcome Screen & Persona Onboarding
* **Problem Addressed:** The extension previously defaulted to Student presets without consulting the user or reading the persona selected at web registration.
* **Onboarding Flow (`extension/popup.html`, `popup.js`):** If no persona is saved in `chrome.storage.local`, the popup displays a 2-step onboarding screen:
  1. *Welcome to Driftless* with official leaf logo.
  2. *Who are you?* with choices: Student, Professional, Influencer, Creator, Other.
* **Auto-Seeding:** Choice persists to `chrome.storage.local`, syncs to `/api/settings/`, and seeds recommended distracting/productive site lists from `PERSONA_DEFAULTS`.

---

### 6. Dashboard Persona Selector & Site Preservation
* **Dashboard Dropdown:** Added `dashPersonaSelect` in `dashboard.html` header.
* **Smart Preset Application:** `apply_persona_defaults(user, persona, keep_user_sites=True)` in `serializers.py` replaces default recommendations with the new persona's defaults while **preserving custom user-added sites**.

---

### 7. Complete Removal of Email OTP System
* **Evolutionary Context:** In commit `7ac4d90`, an Email OTP verification model was created (**Migration 0008: `0008_userprofile_is_verified_emailotp.py`**) requiring 6-digit codes sent via Gmail SMTP.
* **Removal in Migration 0009:** Due to presentation friction and potential SMTP rate limits, `EmailOTP` was deleted in **Migration 0009: `0009_delete_emailotp.py`**.
* **Streamlined Direct Registration:** Registration now performs strict frontend regex validation and backend `EmailValidator` checks, sets `is_verified=True` immediately, seeds presentation gamification, logs the user in, and returns an instant redirect to `/dashboard/`.

---

### 8. Gamified Level, XP System, and 3D Shiny Badges
* **Database Upgrades (Migration 0010: `0010_userprofile_has_deep_worker_and_more.py`):** Added fields to `UserProfile`:
  - `xp` (Integer, default 0)
  - `level` (Integer, default 1)
  - `has_zen_master` (Boolean, default False)
  - `has_deep_worker` (Boolean, default False)
  - `has_iron_will` (Boolean, default False)
* **Presentation Demo Seeder (`seed_demo_gamification`):** Pre-seeds Level 5, 80 XP progress, and unlocks all 3 badges on signup or demo login.
* **3D Visual Styling:** Rendered in left sidebar of `dashboard.html` with metallic gradients, dynamic drop shadows, animated XP progress bars, and a 45-degree hovering sheen sweep (`badge-sheen`).

---

### 9. Priority To-Do Planner Widget
* **Sidebar Integration:** Built a daily priority checklist in `dashboard.html` sidebar below user badges.
* **Client-Side Persistence:** Tasks persist to browser `localStorage` (`driftless_priority_todos`) with active/done status, strikethrough styling, and a dynamic progress pill (e.g. `2/3`).

---

### 10. 3D Neumorphic & Glassmorphic Dashboard Design
* **Design System Overhaul:** Dashboard upgraded to tactile 3D styling featuring layered dual drop-shadows, soft beveled borders, and glassmorphic translucent panels with `backdrop-filter: blur(12px)`.

---

### 11. Standardization to 3 Category Model
* **Database Clean-up (Migration 0006):** Replaced legacy 4-category split (`Productivity`, `Social`, `Entertainment`, `Other`) with 3 standardized categories:
  - `Productive sites`
  - `Distracting sites`
  - `Others`
* Static `CATEGORY_MAP` in `models.py` updated with 45+ popular domains.

---

### 12. Official Brand Logo Refresh
* **Asset Creation:** Replaced generic placeholders with official green leaf "D" brand symbol across all required resolutions: `icon-16.png`, `icon-32.png`, `icon-48.png`, `icon-128.png`, and `icon-512.png`.
"""

CH_5_STRUCTURE = """<h1 id="ch-5">Chapter 5: Project Structure</h1>

Below is the complete repository directory layout as of **October 31, 2026**, with a single-line plain English purpose for every file and folder:

```text
driftless/
│
├── README.md                              # High-level project summary, quick-start guide, and core features
├── requirements.txt                       # Python dependencies (Django, DRF, Pillow, Pygments, Markdown)
├── db.sqlite3                             # SQLite database storing users, logs, settings, and gamification
│
├── assets/                                # Master brand assets and image files
│   └── logo/                              # Official DRIFTLESS leaf logo in all export resolutions
│       ├── driftless_logo_16.png          # 16x16 icon for browser tabs and extension favicon
│       ├── driftless_logo_32.png          # 32x32 icon for Windows taskbar and Retina extension menus
│       ├── driftless_logo_48.png          # 48x48 icon for Chrome Extension Management screen
│       ├── driftless_logo_128.png         # 128x128 icon for Chrome Web Store and installer dialogs
│       ├── driftless_logo_512.png         # 512x512 high-resolution master brand logo
│       ├── driftless_logo_symbol.png      # Transparent symbol mark without wordmark text
│       └── old/                           # Archived legacy logo assets from early development
│
├── docs/                                  # Project documentation library
│   ├── diagrams/                          # Vector SVG system architecture, ER, and workflow diagrams
│   │   ├── system_architecture.svg        # 3-Tier cross-system architecture diagram
│   │   ├── gamification_reward_flow.svg   # Gamification milestone-to-badge lifecycle diagram
│   │   ├── database_er_diagram.svg        # Relational database entity-relationship schema diagram
│   │   ├── workflow_1_tracking.svg        # 1-second precision heartbeat tracking workflow
│   │   ├── workflow_2_escalation_block.svg# 3-tier escalation and DNR enforcement workflow
│   │   ├── workflow_3_scheduled_focus.svg # Scheduled focus start/end alarm lifecycle workflow
│   │   ├── workflow_4_pomodoro.svg        # Pomodoro 25m work / 5m break state machine workflow
│   │   ├── workflow_5_auth_onboarding.svg # Direct registration and persona onboarding workflow
│   │   ├── workflow_6_sync.svg            # Periodic cloud synchronization workflow
│   │   └── workflow_7_green_grove.svg     # 30-day Green Grove tree calculation workflow
│   ├── API_REFERENCE.md                   # Complete REST API reference documentation
│   ├── CHROME_EXTENSION_ARCHITECTURE.md   # Extension service worker, alarms, and DNR documentation
│   ├── CONFIGURATION_AND_DEPENDENCIES.md  # Configuration parameters and environment variables
│   ├── DATABASE_AND_DATA_FLOW.md          # Database models, relationships, and data flow pipelines
│   ├── DJANGO_BACKEND.md                  # Django views, serializers, and business logic
│   ├── DRIFTLESS_COMPLETE_DOCUMENTATION.md# Master 18-chapter monolithic documentation file
│   ├── FEATURE_CODE_MAPPING.md            # Traceability matrix mapping features to exact code files
│   ├── FILE_BY_FILE_ANALYSIS.md           # Granular file-by-file function and interaction breakdown
│   ├── FRONTEND_ARCHITECTURE.md           # Dashboard, auth UI, and extension popup architecture
│   ├── PROJECT_OVERVIEW.md                # Problem statement, objectives, and personas overview
│   ├── PROJECT_STRUCTURE.md               # Current directory layout and file purpose catalog
│   ├── SECURITY_AND_LIMITATIONS.md        # Privacy audit, security boundaries, and known limitations
│   ├── SYSTEM_ARCHITECTURE.md             # System architecture design and component interactions
│   ├── TECH_STACK.md                      # Technology choices and rationales
│   └── VERIFICATION_REPORT.md             # Audit findings, test suite results, and verification notes
│
├── extension/                             # Chrome Extension Client (Manifest V3)
│   ├── manifest.json                      # Extension manifest declaring permissions, DNR, and scripts
│   ├── background.js                      # Background service worker (alarms, DNR rules, storage, sync)
│   ├── content.js                         # Precision heartbeat content script (1-second active tab ticks)
│   ├── popup.html                         # Popup UI markup (welcome, main controls, modals, pickers)
│   ├── popup.js                           # Popup controller (DOM events, storage bindings, messaging)
│   ├── blocked.html                       # Interception screen displayed when a site limit is reached
│   ├── theme.css                          # Shared stylesheet providing Calm Sky and Opal Noir themes
│   └── icons/                             # Extension runtime icons (16px, 32px, 48px, 128px)
│
├── dashboard/                             # Django Web Application Project
│   ├── manage.py                          # Django command-line execution utility
│   ├── build.sh                           # Deployment build script for automated migrations and static collection
│   ├── .env.example                       # Template documenting required environment variable names
│   │
│   ├── driftless/                         # Django Project Configuration Package
│   │   ├── __init__.py                    # Python package initializer
│   │   ├── settings.py                    # Django configuration (INSTALLED_APPS, DRF, Database, Auth)
│   │   ├── urls.py                        # Root URL router mapping / and /dashboard/ to core app
│   │   ├── wsgi.py                        # WSGI entry-point for synchronous web servers
│   │   └── asgi.py                        # ASGI entry-point for asynchronous web servers
│   │
│   └── core/                              # Primary Django Application
│       ├── __init__.py                    # Application package initializer
│       ├── admin.py                       # Django Admin configuration for model inspection
│       ├── apps.py                        # Application registry configuration
│       ├── models.py                      # Data models (UserProfile, UserSettings, UsageLog, SiteLimit)
│       ├── serializers.py                 # DRF serializers and persona preset definitions
│       ├── views.py                       # REST API views, analytics engines, and template handlers
│       ├── urls.py                        # Application URL router (auth, analytics, settings, data)
│       ├── tests.py                       # Automated test suite (16 tests verifying auth, logs, CRUD)
│       │
│       ├── migrations/                    # Database migration history
│       │   ├── 0001_initial.py            # Initial models (UsageLog, SiteLimit, CategoryOverride)
│       │   ├── 0002_usagelog_category...  # Added category field to UsageLog and UserSettings
│       │   ├── 0003_userprofile.py        # Added UserProfile model with phone and persona
│       │   ├── 0004_alter_userprofile...  # Updated persona choices on UserProfile
│       │   ├── 0005_usersettings_allo...  # Added allowed_sites and focus_goal_minutes to UserSettings
│       │   ├── 0006_alter_categoryove...  # Standardized 3 categories (Productive, Distracting, Others)
│       │   ├── 0007_usersettings_sche...  # Added schedule_enabled, schedule_start, schedule_end
│       │   ├── 0008_userprofile_is_ve...  # Introduced EmailOTP model and is_verified field
│       │   ├── 0009_delete_emailotp.py    # Removed EmailOTP model for direct registration flow
│       │   └── 0010_userprofile_has_d...  # Added level, xp, and 3 badge booleans to UserProfile
│       │
│       ├── static/                        # Static assets (stylesheets, JavaScript, brand images)
│       │   ├── css/
│       │   │   └── theme.css              # Dashboard theme tokens and neumorphism utility classes
│       │   └── img/                       # Dashboard logo images
│       │
│       └── templates/                     # Server-rendered HTML templates
│           ├── auth.html                  # Split-screen authentication page (Signup, Login, Google Auth)
│           └── dashboard.html             # Main 3D Neumorphic dashboard (Analytics, Grove, To-Dos, Badges)
│
└── scripts/                               # Automation, utility, and documentation build scripts
    ├── generate_diagrams.py               # Generates all 10 vector SVG architecture and workflow diagrams
    ├── build_extension.py                 # Extension packaging and zip compilation utility
    └── build_extension.sh                 # Shell script equivalent for extension packaging
```
"""

CH_6_TECH_STACK = """<h1 id="ch-6">Chapter 6: Technology Stack &amp; Architectural Rationale</h1>

Every technology chosen in DRIFTLESS was selected to satisfy stringent performance, privacy, and architectural requirements. Below is the technical justification for each component:

## 6.1 Frontend & Extension Architecture

### 1. Google Chrome Manifest V3
* **What it is:** The modern browser extension platform standard enforced by Google Chrome and Chromium browsers.
* **Why it is used:** Manifest V3 is mandatory for Chrome Web Store deployment. It replaces persistent background pages with ephemeral service workers, significantly reducing browser RAM consumption and battery drain.
* **Architectural Challenge & DRIFTLESS Solution:** Because service workers terminate after 30 seconds of inactivity, standard JavaScript `setInterval` timers stop firing. DRIFTLESS resolves this by deploying a lightweight content script (`content.js`) on the active tab that emits 1-second heartbeat pulses, keeping tracking perfectly accurate.

### 2. Chrome Declarative Net Request (DNR) API
* **What it is:** A high-performance browser engine API that blocks or redirects network requests based on declarative rules without letting the extension execute arbitrary code on web traffic.
* **Why it is used:** Replaces the deprecated `webRequestBlocking` API. By delegating request interception directly to the browser's C++ networking core, DNR eliminates latency and guarantees that blocked distracting sites (and Shorts/Reels paths) cannot load even before the DOM begins parsing.
* **Rule ID Allocation:** DRIFTLESS isolates dynamic rule sets into distinct numerical bands:
  - Rules `100` to `899`: Reserved for active Focus Mode blocks.
  - Rules `1000` to `1999`: Reserved for 100% daily limit enforcement blocks.
  - Rules `2000` to `2009`: Reserved for targeted Shorts and Reels blocks.

### 3. Chrome Storage Local (`chrome.storage.local`)
* **What it is:** An asynchronous, persistent key-value storage engine isolated to the extension.
* **Why it is used:** Survives service worker restarts, browser restarts, and computer reboots. Fast, asynchronous reads prevent UI thread blocking in the popup.

### 4. Chrome Alarms API (`chrome.alarms`)
* **What it is:** An operating-system-level scheduled wake-up mechanism for service workers.
* **Why it is used:** Replaces `setTimeout` for long durations. Alarms wake up the suspended background service worker reliably to execute periodic cloud syncs (every 15 minutes), trigger scheduled focus start/end windows, handle Pomodoro sprints, and execute the midnight reset.

## 6.2 Backend & Data Architecture

### 1. Python 3.13 & Django 4.2+ (LTS)
* **What it is:** A mature, high-level Python web framework enforcing clean architectural patterns and rapid development.
* **Why it is used:** Django provides battle-tested Object-Relational Mapping (ORM), robust session management, database migration tooling, and built-in protection against SQL injection, Cross-Site Scripting (XSS), and Cross-Site Request Forgery (CSRF).

### 2. Django REST Framework (DRF 3.17+)
* **What it is:** A flexible toolkit for building robust, scalable Web APIs.
* **Why it is used:** Provides serialization between Python model instances and JSON, class-based view abstractions, rate throttling (120 requests/minute for sync), and standard token authentication.

### 3. Token-Based Authentication (`rest_framework.authtoken`)
* **What it is:** Stateless cryptographic token authentication where requests carry an `Authorization: Token <key>` header.
* **Why it is used:** Extensions cannot easily maintain cookie-based session state across domains without third-party cookie permissions. Tokens allow the extension to communicate securely with the backend across different origins.

### 4. SQLite 3 Database
* **What it is:** A self-contained, serverless, zero-configuration transactional SQL database engine.
* **Why it is used:** Ideal for local development, zero-friction demonstration, and embedded environments. Handled through Django's ORM, making migration to PostgreSQL or MySQL seamless for high-scale cloud deployments.

## 6.3 UI & Presentation Architecture

### 1. 3D Neumorphism & Soft Shadows
* **What it is:** A visual design trend utilizing paired light and dark drop-shadows to simulate tactile, physically elevated physical objects.
* **Why it is used:** Creates a soothing, organic, and premium aesthetic that distinguishes DRIFTLESS from sterile corporate analytics tools.

### 2. Glassmorphism & Backdrop Blur
* **What it is:** Frosted-glass UI styling achieved via translucent CSS backgrounds and `backdrop-filter: blur(12px)`.
* **Why it is used:** Keeps navigation headers and sidebars readable while providing spatial depth.

### 3. Chart.js 4.4
* **What it is:** A responsive HTML5 canvas charting library.
* **Why it is used:** Delivers smooth animations, interactive hover tooltips, and dynamic dataset toggling between Bar and Line chart visualizations.
"""

print("Loaded Chapters 1 to 6 (Enhanced).")
