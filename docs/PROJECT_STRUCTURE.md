<h1 id="ch-4">Chapter 4: What Changed Since Oct 26</h1>

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


---

<h1 id="ch-5">Chapter 5: Project Structure</h1>

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
