# Driftless — Deployment Guide

This guide explains how to deploy Driftless to **PythonAnywhere** (recommended for SQLite projects) and **Render** (alternative container platform), plus how any new user gets started.

---

## 🚀 How a New User Starts (5-Line Quickstart)

1. **Open the Live Link**: Navigate to the Driftless web URL in your browser.
2. **Create Your Account**: Click **Create Account**, enter a username, choose your persona (Student, Professional, etc.), and sign up.
3. **Install Extension**: Open `chrome://extensions`, enable **Developer mode**, and click **Load unpacked** on the unzipped `/extension` folder (or download `driftless-extension.zip`).
4. **Link Your Token**: Copy your personal API Token from the dashboard and paste it into the extension popup.
5. **Browse Normally**: Browse the web — productive and distracting sites track automatically, streaks calculate daily, and focus limits protect your attention!

> **Privacy & Isolation:** Each user has their own private account. A friend or family member uses their own account credentials and personal API token on their machine. Users never see each other's data.

---

## 1. Deploying to PythonAnywhere (Primary / Recommended)

PythonAnywhere keeps your SQLite database persistent on disk and is 100% free for educational/mini-project use.

### Step 1: Push Code to GitHub
Ensure your repository is pushed to GitHub with the `.env.example` file.

### Step 2: Open a Bash Console on PythonAnywhere
Clone your repository:
```bash
git clone https://github.com/<your-username>/driftless.git
cd driftless/dashboard
```

### Step 3: Create Virtual Environment & Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create your `.env` file in `dashboard/`:
```bash
cp .env.example .env
nano .env
```
Set:
- `DEBUG=False`
- `ALLOWED_HOSTS=<your-username>.pythonanywhere.com`
- `SECRET_KEY=<a-secure-random-string>`
- `CSRF_TRUSTED_ORIGINS=https://<your-username>.pythonanywhere.com`

### Step 5: Database Migrations & Static Files
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_demo    # Seeds evaluator demo@driftless.app account
```

### Step 6: Configure the Web App Tab
1. In the PythonAnywhere dashboard, go to the **Web** tab.
2. Add a new web app selecting **Manual configuration** -> **Python 3.10+**.
3. Set **Source code directory**: `/home/<your-username>/driftless/dashboard`
4. Set **Virtualenv directory**: `/home/<your-username>/driftless/dashboard/venv`
5. Edit the **WSGI configuration file**:
   ```python
   import os
   import sys
   from pathlib import Path

   path = '/home/<your-username>/driftless/dashboard'
   if path not in sys.path:
       sys.path.append(path)

   os.environ['DJANGO_SETTINGS_MODULE'] = 'driftless.settings'

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
6. Click **Reload <your-username>.pythonanywhere.com**.

---

## 2. Deploying to Render (Alternative Cloud Platform)

Render provides automatic Git-based deploys. The project includes `Procfile` and `render.yaml`.

> **Note on Render SQLite:** Render free instances spin down when inactive and have ephemeral disks (data resets upon restarts). For production usage on Render, add a free PostgreSQL database and provide the `DATABASE_URL` in the environment variables.

### Steps:
1. Connect your repository on [Render](https://render.com).
2. Choose **Web Service** with the root directory set to `dashboard`.
3. Build Command:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py seed_demo
   ```
4. Start Command:
   ```bash
   gunicorn driftless.wsgi:application
   ```
5. Environment Variables:
   - `DEBUG`: `False`
   - `SECRET_KEY`: (generate in dashboard)
   - `ALLOWED_HOSTS`: `.onrender.com`
   - `CORS_ALLOW_ALL_ORIGINS`: `True`

---

## 3. Chrome Extension Distribution

To share the extension with friends or evaluators:
1. Run the packager script:
   ```bash
   python scripts/build_extension.py
   ```
2. Distribute `driftless-extension.zip`.
3. Users extract the folder and load it into Google Chrome via `chrome://extensions` (**Load unpacked**).
4. Users configure their server URL in the popup (defaulting to your production URL or `http://127.0.0.1:8000`).
