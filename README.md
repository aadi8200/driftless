# Driftless — Digital Wellbeing & Distraction Tracker

Driftless is an intelligent, gamified digital wellbeing system designed to protect focus, eliminate endless scrolling, and build lasting productivity habits. It pairs a **Manifest V3 Chrome Extension** with a **Django/DRF Web Dashboard**.

- **Live Cloud Dashboard**: [https://driftless-g5cb.onrender.com](https://driftless-g5cb.onrender.com)
- **Technical Documentation PDF**: Included in repository as [`DRIFTLESS_Technical_Documentation.pdf`](DRIFTLESS_Technical_Documentation.pdf) (complete 40-page technical reference with architectural diagrams, API specs, and data flows).

---

## 🌟 Key Features

1. **Intelligent Persona Onboarding**: First-run setup tailors distraction limits and productive site lists to your workflow (Student, Professional, Creator, Influencer, Other).
2. **Shorts & Reels Blocker**: Automatically detects and redirects short-form video feeds (`/shorts`, `/reel/`, TikTok) to a mindful block page.
3. **Pomodoro Focus Timer**: Integrated 25m work / 5m break timer directly inside the extension popup and dashboard.
4. **Incognito Focus Guard (Anti-Cheat)**: Automatically detects and closes incognito/private windows if opened during an active Focus Mode session.
5. **Gamification & Green Grove**: Earn XP, level up (e.g., Level 5 Zen Master), unlock badges (Deep Worker, Iron Will), and grow a 3D virtual bonsai as you maintain your streaks.
6. **Priority To-Do Planner**: Inline daily priority task planner embedded directly into the dashboard sidebar.
7. **Bidirectional Cloud Sync**: Seamless synchronization between the browser extension and Django REST Framework API with token-based authentication.

---

## 📁 Final Project Structure

```
driftless/
├── dashboard/                              # Django + DRF backend & analytics web dashboard
│   ├── core/                               # Core app (models, views, serializers, tests, templates)
│   ├── driftless/                          # Project configuration (settings, urls, wsgi)
│   ├── staticfiles/                        # Production static assets served by WhiteNoise
│   ├── manage.py                           # Django CLI
│   ├── Procfile / render.yaml / build.sh   # Cloud deployment configs (Render / Gunicorn)
│   └── requirements.txt                    # Python dependencies
├── extension/                              # Chrome Extension (Manifest V3)
│   ├── background.js                       # Service worker (tab tracking, DNR rules, incognito blocker)
│   ├── popup.html / popup.js               # Extension popup interface & controller
│   ├── blocked.html / blocked.js           # CSP-compliant block page & theme loader
│   ├── content.js                          # Content script for client-side injection
│   ├── manifest.json                       # Extension Manifest V3 configuration
│   ├── theme.css                           # Unified design tokens & styling
│   └── icons/                              # Production extension icons & logos
├── scripts/                                # Utility scripts
│   ├── build_extension.py                  # Extension ZIP packager for distribution
│   └── build_extension.sh                  # Shell packaging script
├── assets/logo/                            # Official Driftless brand assets & masters
├── DRIFTLESS_Technical_Documentation.pdf   # Complete 40-page technical architecture PDF
├── DEPLOY.md                               # Deployment guide (Render & PythonAnywhere)
├── CHANGELOG.md                            # Comprehensive project changelog
├── .gitignore                              # Production git ignore configuration
└── README.md                               # Project overview and quickstart
```

---

## 🚀 How to Run the Backend (Local Dev)

1. **Navigate to the dashboard directory**:
   ```bash
   cd dashboard
   ```

2. **Activate the virtual environment**:
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Linux / macOS:
     ```bash
     source venv/bin/activate
     ```

3. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Run Backend Tests (16 passing tests)**:
   ```bash
   python manage.py test core
   ```

5. **Start the development server**:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```
   The dashboard is live at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 🧩 How to Load the Chrome Extension

1. Open Google Chrome and navigate to:
   ```
   chrome://extensions
   ```
2. Enable **Developer mode** using the toggle in the top-right corner.
3. Click the **Load unpacked** button in the top-left corner.
4. Select the `extension/` folder located inside the `driftless` repository.
5. The **Driftless** icon will now appear in your browser toolbar.

---

## 🔗 How to Connect the Extension to Your Account

1. Open the Driftless dashboard (locally at [http://127.0.0.1:8000/](http://127.0.0.1:8000/) or live at [https://driftless-g5cb.onrender.com](https://driftless-g5cb.onrender.com)).
2. Log in or create an account.
3. In the top-right header or Settings panel, copy your **API Token**.
4. Click the **Driftless extension icon** in your browser toolbar.
5. In the **Sync & Account** card, paste your API token and click **Save**.
6. The status indicator will switch to green (**Connected**) and all your site limits, daily timers, and focus sessions will synchronize automatically.
