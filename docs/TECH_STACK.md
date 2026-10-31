<h1 id="ch-6">Chapter 6: Technology Stack &amp; Architectural Rationale</h1>

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
