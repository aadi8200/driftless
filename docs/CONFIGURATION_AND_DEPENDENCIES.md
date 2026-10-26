# DRIFTLESS — Configuration & Dependency Specifications

## 1. Python Dependencies (`dashboard/requirements.txt`)

```
Django>=4.2,<5.0
djangorestframework>=3.15
django-cors-headers>=4.3
whitenoise>=6.6
python-dotenv>=1.0
gunicorn>=21.2
sqlparse>=0.5
```

### Detailed Dependency Explanations:
1. **`Django>=4.2,<5.0`:** Long-Term Support (LTS) release of the Django web framework. Provides the core ORM, database migrations, model definitions, session management, template rendering, and administrative back office.
2. **`djangorestframework>=3.15`:** The standard toolkit for REST APIs in Django. Powers serializer validation, token-based authentication (`rest_framework.authtoken`), view decorators (`@api_view`), permission classes, and throttling engines.
3. **`django-cors-headers>=4.3`:** Middleware that attaches Cross-Origin Resource Sharing (CORS) headers to HTTP responses. Essential for enabling the Chrome extension runtime (`chrome-extension://...`) to make fetch calls to the Django backend.
4. **`whitenoise>=6.6`:** Static file serving engine. Binds directly to the WSGI pipeline, enabling Gunicorn to serve production static assets (CSS, logos, themes) with Brotli/Gzip compression and permanent caching headers without requiring Nginx.
5. **`python-dotenv>=1.0`:** Automatically discovers and parses key-value pairs from `.env` files into Python's `os.environ`, decoupling sensitive secrets and deployment flags from code.
6. **`gunicorn>=21.2`:** Production-grade WSGI HTTP server designed for Unix/Linux container environments (Render, Heroku, Docker).
7. **`sqlparse>=0.5`:** Non-validating SQL parser required internally by Django's database management engine to format and execute migration scripts.

---

## 2. Environment Variables Specification (`dashboard/.env` & `.env.example`)

| Variable Name | Default in Code | Purpose | Production Requirement |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | `'driftless-dev-secret-change-in-production-pleaseee'` | Cryptographic signing key for sessions, CSRF tokens, and passwords | **MANDATORY:** Must be set to a secure 50+ character random string in production |
| `DEBUG` | `True` | Toggles Django debug traceback pages and query logging | **MANDATORY:** Must be set to `False` in production |
| `ALLOWED_HOSTS` | `*` | Comma-delimited list of host/domain names that this Django site can serve | Set to production domain (e.g. `driftless.onrender.com,localhost`) |
| `CORS_ALLOW_ALL_ORIGINS`| `True` | Enables open CORS access | Can remain `True` or restrict to specific origins and Chrome extension regex |
| `CSRF_TRUSTED_ORIGINS`| Ngrok, Cloudflare, Localhost list | Comma-delimited origins trusted for POST requests | Include production domain (e.g. `https://driftless.onrender.com`) |
| `SECURE_SSL_REDIRECT` | `False` | Forces all HTTP requests to be redirected to HTTPS | Set to `True` when running behind SSL-terminating reverse proxies |

---

## 3. Extension Manifest Specification (`extension/manifest.json`)

```json
{
  "manifest_version": 3,
  "name": "Driftless - Focus & Wellbeing Companion",
  "version": "1.1",
  "description": "Digital wellbeing & distraction tracker with per-site limits, focus mode, and cloud sync.",
  "icons": {
    "16": "icons/icon-16.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon-16.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    }
  },
  "permissions": [
    "tabs",
    "storage",
    "alarms",
    "notifications",
    "idle",
    "declarativeNetRequest",
    "declarativeNetRequestWithHostAccess",
    "declarativeNetRequestFeedback"
  ],
  "host_permissions": ["<all_urls>"],
  "web_accessible_resources": [
    {
      "resources": ["blocked.html", "theme.css", "icons/*"],
      "matches": ["<all_urls>"]
    }
  ],
  "background": {
    "service_worker": "background.js"
  }
}
```

---

## 4. Build & Development Scripts

### 4.1. Extension Packager: `scripts/build_extension.py`
- **Execution:** `python scripts/build_extension.py`
- **Behavior:**
  1. Resolves `ROOT_DIR / 'extension'`.
  2. Unlinks any pre-existing `driftless-extension.zip`.
  3. Recursively gathers all files in `extension/`, excluding hidden OS/Git files.
  4. Generates a clean, deflated zip file (`driftless-extension.zip`) ready for direct distribution or uploading to `chrome://extensions`.

### 4.2. Shell Alternative: `scripts/build_extension.sh`
- A Bash equivalent for Unix/macOS environments using standard `zip -r`.

---

## 5. Deployment Configurations

### 5.1. `dashboard/Procfile`
```procfile
web: gunicorn driftless.wsgi:application --bind 0.0.0.0:$PORT
```
Declares the process command for PaaS platforms like Render or Heroku to launch Gunicorn bound to the dynamically assigned `$PORT`.

### 5.2. `dashboard/render.yaml`
```yaml
services:
  - type: web
    name: driftless-dashboard
    env: python
    buildCommand: "pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput && python manage.py seed_demo"
    startCommand: "gunicorn driftless.wsgi:application"
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.12
      - key: DEBUG
        value: "False"
      - key: SECRET_KEY
        generateValue: true
```
Infrastructure-as-code specification for Render.com that automates dependency installation, database migration, static collection via WhiteNoise, demo account seeding, and Gunicorn startup.

---

## 6. Git Ignore Directives (`.gitignore`)
The repository includes `.gitignore` rules that protect the codebase against accidental leakage of:
- Virtual environments (`venv/`, `env/`, `.venv/`)
- Compiled Python bytecode (`__pycache__/`, `*.py[cod]`)
- SQLite database binaries (`*.sqlite3`)
- Environment secret files (`.env`)
- Static collection dumps (`staticfiles/`)
- Operating system cache files (`Thumbs.db`, `.DS_Store`)
