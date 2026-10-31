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


---

<h1 id="ch-15">Chapter 15: Setup &amp; Execution Guide</h1>

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
