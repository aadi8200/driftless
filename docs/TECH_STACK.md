# DRIFTLESS — Technology Stack & Dependencies Analysis

## 1. Complete Technology Inventory

| Technology | Category | Actual Usage | File / Module | Purpose | Related Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Python 3.10+** | Programming Language | Core Backend Execution | `dashboard/**/*.py`, `scripts/*.py` | Primary language executing web server, models, serializers, and tooling | All backend APIs, migrations, seeding, extension packaging |
| **JavaScript (ES2022)**| Programming Language | Client & Extension Execution | `extension/*.js`, `<script>` in HTML | Client-side reactive logic, timer tickers, event dispatching, REST fetches | Active tab tracking, chart rendering, theme switching, sync |
| **HTML5** | Markup Language | UI Document Structure | `dashboard/core/templates/*.html`, `extension/*.html` | Semantic layout, forms, accessible widgets, dialog overlays | Analytics views, login forms, extension popup, blocked landing |
| **CSS3 & CSS Custom Props**| Styling System | Visual Tokens & Layout | `dashboard/.../theme.css`, `extension/theme.css` | Design system variables (`--pri`, `--bg`, `--ink`, etc.), micro-transitions | Calm Sky (Light) and Opal Noir (Dark) dual-theme system |
| **Django 4.2 LTS** | Web Framework | Server Architecture | `dashboard/driftless/*`, `dashboard/core/*` | MVC architecture, routing, ORM, authentication backend, template engine | User management, session auth, admin console, static collection |
| **Django REST Framework (DRF 3.15)**| REST API Toolkit | Web API Layer | `dashboard/core/serializers.py`, `dashboard/core/views.py` | Serializer validation, token authentication, rate limiting, JSON responses | `/api/usage/`, `/api/summary/`, `/api/limits/`, `/api/settings/` |
| **Chrome Manifest V3** | Extension Platform Spec| Browser Extension Runtime | `extension/manifest.json`, `extension/background.js` | Defines permissions, service worker lifecycle, alarms, host matches | Browser integration, tab tracking, background execution |
| **declarativeNetRequest API**| Chrome Browser API | Network Interception | `extension/background.js` | Dynamic URL redirect rules executed at network layer without content scripts | 3-tier escalation blocking, Focus Mode distraction suppression |
| **chrome.storage.local** | Browser Storage API | Local Extension State | `extension/background.js`, `extension/popup.js` | High-speed local persistence for accumulated seconds and sync queues | Offline dwell tracking, uncommitted delta queue, cached settings |
| **chrome.alarms API** | Chrome Browser API | Scheduled Background Execution | `extension/background.js` | Periodic timer triggers (`ALARM_PERIODIC_SYNC`, `ALARM_MIDNIGHT_RESET`)| 60-second delta sync, daily midnight usage resets |
| **chrome.idle API** | Chrome Browser API | State Detection | `extension/background.js` | Detects when user becomes inactive for > 60 seconds | Suppresses false positive time accumulation while user is away |
| **chrome.notifications API**| Chrome Browser API | System Desktop Notifications | `extension/background.js` | Displays OS-level desktop notification cards | Tier 1 (80% Nudge), Tier 2 (100% Alert), Focus complete alert |
| **SQLite 3** | Relational Database | Data Persistence | `dashboard/db.sqlite3` | Zero-configuration file-based SQL database storage | Storage of users, profiles, usage logs, limits, and settings |
| **Chart.js 4.4.3 (UMD)** | Data Visualization | Client Charting Engine | `dashboard/core/templates/dashboard.html` | Canvas-based rendering of 7-day multi-dataset stacked bar & line charts | 7-day category breakdowns, hover tooltips, mode switching |
| **Tailwind CSS 3.x (CDN)**| Utility CSS Engine | Rapid UI Component Layout | `dashboard/core/templates/*.html` | Utility classes for flex, grid, spacing, responsive visibility | Dashboard sidebar, grid cards, modal dialogs, status badges |
| **WhiteNoise 6.6** | Static Asset Serving | Middleware File Server | `dashboard/driftless/settings.py` | Serves static assets directly from Gunicorn/WSGI with compression | Production serving of CSS, images, and brand logo |
| **django-cors-headers 4.3**| Security Middleware | CORS Policy Enforcement | `dashboard/driftless/settings.py` | Grants cross-origin request permissions to `chrome-extension://*` | Extension communication with Django REST endpoints |
| **python-dotenv 1.0** | Configuration Utility | Environment Variable Loader | `dashboard/driftless/settings.py` | Parses `.env` configuration file into `os.environ` | Environment secrets, debug flags, allowed hosts, CORS flags |
| **Gunicorn 21.2** | WSGI HTTP Server | Production Web Server | `dashboard/Procfile` | Production-grade multi-worker WSGI HTTP server | Production PaaS deployment (Render / Heroku) |
| **Google Fonts (Inter)** | Web Typography | Font Delivery | `dashboard/core/templates/*.html` | Modern geometric sans-serif typeface for clean UI legibility | Typography across dashboard and authentication pages |

---

## 2. In-Depth Component Analysis

### 2.1. Python & Django 4.2 LTS
- **What It Is:** High-level Python web framework providing an ORM, request router, authentication middleware, and administrative interface.
- **Why It Is Used:** Enables rapid development of secure, maintainable backend applications with robust schema migration tools and native SQL injection protection.
- **Usage Location:** All files in `dashboard/driftless/` and `dashboard/core/`.
- **Key Features Depending On It:** User registration, session login, relational database transactions, static file orchestration, template rendering.
- **Interactions:** Serves as the foundation hosting Django REST Framework and executing all database queries against SQLite.
- **Role:** Directly used core framework.

### 2.2. Django REST Framework (DRF)
- **What It Is:** Powerful, flexible toolkit for building Web APIs in Django.
- **Why It Is Used:** Standardizes token-based authentication (`TokenAuthentication`), incoming payload validation, rate-limiting (`UserRateThrottle`), and structured JSON serialization.
- **Usage Location:** `dashboard/core/serializers.py`, `dashboard/core/views.py`.
- **Key Features Depending On It:** All endpoints under `/api/`, including `/api/usage/`, `/api/summary/`, `/api/limits/`, `/api/settings/`, and `/api/sessions/`.
- **Interactions:** Bridges the client-side JavaScript `fetch()` calls from both the dashboard and the Chrome extension to the Django ORM.
- **Role:** Directly used core library.

### 2.3. Chrome Extension Manifest V3 Runtime
- **What It Is:** The modern standard for Google Chrome extensions requiring service workers instead of persistent background pages.
- **Why It Is Used:** Mandatory requirement for modern Chrome extensions; ensures memory efficiency and enhanced browser security.
- **Usage Location:** `extension/manifest.json`, `extension/background.js`, `extension/popup.js`.
- **Key Features Depending On It:** Dynamic tab listening (`tabs.onActivated`, `tabs.onUpdated`), window focus detection (`windows.onFocusChanged`), idle monitoring, and dynamic declarative network requests.
- **Interactions:** Communicates with the Django REST API over HTTP using the native browser `fetch` API.
- **Role:** Directly used execution platform.

### 2.4. Chart.js 4.4.3
- **What It Is:** Open-source HTML5 Canvas charting library.
- **Why It Is Used:** Renders high-performance, fluid, responsive bar and line charts with custom tooltip styling and smooth theme transitions.
- **Usage Location:** `dashboard/core/templates/dashboard.html` (`renderChart()` function).
- **Key Features Depending On It:** 7-Day category breakdown chart displaying Productivity, Social, Entertainment, and Other categories.
- **Interactions:** Dynamically reads CSS theme variables (`--prod`, `--soc`, `--ent`, `--tooltip-bg`) directly from `window.getComputedStyle()` so chart colors update instantaneously when toggling between Calm Sky and Opal Noir.
- **Role:** Directly used frontend library loaded via CDN.

### 2.5. Tailwind CSS & theme.css Dual-Theme Bridge
- **What It Is:** A hybrid styling approach pairing utility classes with structured CSS custom properties.
- **Why It Is Used:** Tailwind handles responsive layouts, flexboxes, and padding, while `theme.css` manages design tokens (colors, radii, shadows, borders) for Calm Sky (Light) and Opal Noir (Dark).
- **Usage Location:** `dashboard/core/templates/*.html`, `dashboard/core/static/css/theme.css`, `extension/theme.css`.
- **Key Features Depending On It:** Zero-FOUC theme rendering, high-contrast dark mode, and responsive layout scaling across desktop and mobile.
- **Role:** Directly used styling system.
