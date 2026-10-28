# Driftless — Digital Wellbeing & Distraction Tracker

Driftless is a digital wellbeing tool consisting of a Chrome extension (Manifest V3) and a Django web dashboard. It helps users understand their browsing habits, maintain deep focus, and build daily productivity streaks by automatically categorizing browsing time into **Productive sites**, **Distracting sites**, and **Others**, providing per-site timers, Focus Mode blocking, and bidirectional synchronization.

---

## 📁 Project Structure

```
driftless/
├── dashboard/               # Django + DRF backend & analytics web dashboard
│   ├── core/                # Core Django app (models, views, serializers, tests)
│   ├── driftless/           # Django project configuration (settings, urls, wsgi)
│   ├── staticfiles/         # Production static assets served by WhiteNoise
│   ├── manage.py            # Django management CLI
│   └── requirements.txt     # Python dependencies
├── docs/                    # Technical & architectural documentation (Markdown)
├── extension/               # Chrome Extension (Manifest V3)
│   ├── background.js        # Background service worker (DNR blocking, tracking, sync)
│   ├── popup.html           # Extension popup interface
│   ├── popup.js             # Popup controller & state management
│   ├── manifest.json        # Extension Manifest V3 configuration
│   ├── theme.css            # Extension styling & theme tokens
│   └── icons/               # Extension icons (16px, 48px, 128px)
├── scripts/                 # Developer utility scripts (build_extension.py, build_extension.sh)
├── .gitignore               # Git ignore patterns
└── README.md                # Project documentation
```

---

## 🚀 How to Run the Backend

1. **Navigate to the dashboard directory**:
   ```bash
   cd dashboard
   ```

2. **Activate the virtual environment**:
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - Linux / macOS:
     ```bash
     source venv/bin/activate
     ```

3. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start the development server**:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```
   The dashboard is now live at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 🧩 How to Load the Chrome Extension

1. Open Google Chrome and navigate to:
   ```
   chrome://extensions
   ```
2. Enable **Developer mode** using the toggle switch in the top-right corner.
3. Click the **Load unpacked** button in the top-left corner.
4. Select the `extension/` folder located inside the `driftless` repository.
5. The **Driftless** icon will now appear in your browser toolbar and extensions menu.

---

## 🔗 How to Link the Token

1. Open the Driftless web dashboard at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
2. Log in to your account (or create a new account).
3. In the dashboard top-right header or Settings, copy your **API Token** (e.g. `9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`).
4. Click the **Driftless extension icon** in your browser toolbar to open the popup.
5. In the **Sync & Account** card, paste your API token into the **API Token** input field.
6. Click **Save**. The status dot will turn green (**Connected**) and your lists, daily timers, limits, and streaks will automatically synchronize with the server.
