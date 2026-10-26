# DRIFTLESS — Complete REST API Reference

All endpoints are registered in `dashboard/core/urls.py` and implemented in `dashboard/core/views.py`. Default base URL during local development is `http://127.0.0.1:8000`.

---

## 1. Master API Endpoints Directory

| HTTP Method | Actual Endpoint | Authentication | Input Format | Processing Summary | Output Format | Implementation File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | AllowAny | JSON Body | Creates User, UserProfile, UserSettings, applies persona limits, logs in session | JSON `{ token, username }` | `core/views.py:73` |
| `POST` | `/api/auth/login/` | AllowAny | JSON Body | Authenticates by username, email, or normalized phone; issues token | JSON `{ token, username }` | `core/views.py:92` |
| `POST` | `/api/auth/logout/` | IsAuthenticated | None | Deletes auth token and terminates Django user session | JSON `{ detail }` | `core/views.py:140` |
| `POST` | `/api/auth/regenerate-token/` | IsAuthenticated | None | Deletes existing auth token and creates a new Token instance | JSON `{ token }` | `core/views.py:150` |
| `POST` | `/api/usage/` | IsAuthenticated (Token/Session) | JSON Object or Array | Validates domain and seconds; creates or increments `UsageLog` records | JSON `{ created, updated }` | `core/views.py:165` |
| `GET` | `/api/summary/` | IsAuthenticated (Token/Session) | None | Aggregates 7-day stats, daily logs, strict streaks, and distractions | JSON `{ weekly, daily, stats, ... }`| `core/views.py:213` |
| `GET` | `/api/settings/` | IsAuthenticated (Token/Session) | None | Retrieves user settings object | JSON `{ focus_mode_active, ... }` | `core/views.py:443` |
| `PATCH` | `/api/settings/` | IsAuthenticated (Token/Session) | JSON Partial Body | Partially updates user settings fields | JSON `{ focus_mode_active, ... }` | `core/views.py:443` |
| `GET` | `/api/limits/` | IsAuthenticated (Token/Session) | None | Lists all configured per-site limits for the authenticated user | JSON Array `[{ id, domain, ... }]` | `core/views.py:467` |
| `POST` | `/api/limits/` | IsAuthenticated (Token/Session) | JSON Body | Creates or updates a `SiteLimit` record for domain | JSON `{ id, domain, daily_limit... }`| `core/views.py:467` |
| `PATCH` | `/api/limits/<id>/` | IsAuthenticated (Token/Session) | JSON Partial Body | Partially updates an existing `SiteLimit` by primary key | JSON `{ id, domain, ... }` | `core/views.py:499` |
| `DELETE`| `/api/limits/<id>/` | IsAuthenticated (Token/Session) | None | Deletes an existing `SiteLimit` record | HTTP 204 No Content | `core/views.py:499` |
| `GET` | `/api/categories/` | IsAuthenticated (Token/Session) | None | Lists all user category overrides | JSON Array `[{ id, domain, ... }]` | `core/views.py:526` |
| `POST` | `/api/categories/` | IsAuthenticated (Token/Session) | JSON Body | Creates category override and retroactively updates past `UsageLog`s | JSON `{ id, domain, category }` | `core/views.py:526` |
| `DELETE`| `/api/categories/<id>/` | IsAuthenticated (Token/Session) | None | Deletes category override and recalculates past `UsageLog` categories | HTTP 204 No Content | `core/views.py:556` |
| `GET` | `/api/sessions/` | IsAuthenticated (Token/Session) | None | Returns the 10 most recent focus sessions for the user | JSON Array `[{ id, duration... }]` | `core/views.py:577` |
| `POST` | `/api/sessions/` | IsAuthenticated (Token/Session) | JSON Body | Logs a completed focus session block | JSON `{ id, duration_minutes, ... }` | `core/views.py:577` |
| `GET` | `/api/data/export/` | IsAuthenticated (Token/Session) | None | Streams full JSON data archive of user's logs, limits, and sessions | Downloadable JSON payload | `core/views.py:603` |
| `POST` | `/api/data/delete/` | IsAuthenticated (Token/Session) | None | Purges all `UsageLog` and `FocusSession` records for user | JSON `{ detail }` | `core/views.py:632` |

---

## 2. Endpoint Specifications

### 2.1. Ingestion: `POST /api/usage/`
- **Purpose:** Ingests uncommitted browsing dwell time from the Chrome extension.
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Token <api_token>`
- **Throttling:** Custom `SyncRateThrottle` at `120 requests/minute`.
- **Request Body (Batch or Single):**
  ```json
  [
    {
      "website_url": "github.com",
      "time_spent_seconds": 60,
      "date": "2026-10-26"
    },
    {
      "website_url": "instagram.com",
      "time_spent_seconds": 45,
      "date": "2026-10-26"
    }
  ]
  ```
- **Validation:**
  - `website_url` is normalized through `clean_domain()`.
  - `time_spent_seconds` must be `>= 0` and `<= 86400` (24-hour sanity clamp).
- **Database Operation:** Finds or creates a `UsageLog` for `(request.user, website_url, date)`. Increments `time_spent_seconds` atomically and recalculates category via `classify_domain()`.
- **Response `200 OK`:**
  ```json
  {
    "created": 1,
    "updated": 1
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Payload validation error (e.g. invalid domain or negative seconds).
  - `401 Unauthorized`: Missing or invalid token.

---

### 2.2. Analytics: `GET /api/summary/`
- **Purpose:** Primary analytics aggregation endpoint powering the Web Dashboard and Extension Popup.
- **Headers:** `Authorization: Token <api_token>` or Session Cookie.
- **Response `200 OK` Schema:**
  ```json
  {
    "weekly": [
      {
        "date": "2026-10-20",
        "total_seconds": 14400,
        "productivity_seconds": 10800,
        "social_seconds": 1800,
        "entertainment_seconds": 1800,
        "other_seconds": 0
      }
    ],
    "daily": [
      {
        "website_url": "github.com",
        "total_seconds": 7200,
        "category": "Productivity"
      }
    ],
    "stats": {
      "today_total_seconds": 14400,
      "productive_seconds": 10800,
      "social_seconds": 1800,
      "entertainment_seconds": 1800,
      "focus_efficiency": 75,
      "top_site": "github.com",
      "streak": 14,
      "today_sessions_count": 2,
      "longest_session_minutes": 45,
      "data_days_count": 14
    },
    "distractions": [
      {
        "website_url": "instagram.com",
        "category": "Social",
        "used_minutes": 25,
        "limit_minutes": 30,
        "percentage": 83,
        "enabled": true,
        "limit_id": 4
      }
    ],
    "settings": {
      "focus_mode_active": false,
      "daily_limit_minutes": 60,
      "focus_goal_minutes": 180,
      "streak_days": 14,
      "require_challenge": false,
      "blocked_sites": "",
      "allowed_sites": ""
    },
    "user": {
      "username": "demo",
      "persona": "student"
    }
  }
  ```

---

### 2.3. Per-Site Limits: `/api/limits/`
- **`GET /api/limits/`**: Returns all limits created by the authenticated user.
- **`POST /api/limits/`**:
  - **Request Body:**
    ```json
    {
      "domain": "reddit.com",
      "daily_limit_minutes": 25,
      "enabled": true
    }
    ```
  - **Validation:** `daily_limit_minutes` must be between `1` and `1440`.
  - **Response `201 Created` / `200 OK`:**
    ```json
    {
      "id": 12,
      "domain": "reddit.com",
      "daily_limit_minutes": 25,
      "enabled": true,
      "updated_at": "2026-10-26T07:15:00Z"
    }
    ```
- **`DELETE /api/limits/<id>/`**: Deletes limit if owned by user. Returns `204 No Content`. Returns `404 Not Found` if the limit belongs to another user (ensuring data isolation).

---

### 2.4. Category Overrides: `/api/categories/`
- **`POST /api/categories/`**:
  - **Request Body:**
    ```json
    {
      "domain": "youtube.com",
      "category": "Productivity"
    }
    ```
  - **Validation:** Category must be one of `Productivity`, `Social`, `Entertainment`, `Other`.
  - **Side Effect:** Automatically executes `UsageLog.objects.filter(user=request.user, website_url=domain).update(category=category)` to reclassify all past records.
- **`DELETE /api/categories/<id>/`**:
  - Deletes override and recalculates default category for all historical logs of that domain.

---

### 2.5. Data Sovereignty: `/api/data/export/` & `/api/data/delete/`
- **`GET /api/data/export/`**:
  - Returns `application/json` payload containing username, export timestamp, user settings, all usage logs, site limits, category overrides, and completed focus sessions.
- **`POST /api/data/delete/`**:
  - Deletes all usage logs and focus sessions for the authenticated user.
  - Response `200 OK`: `{"detail": "All browsing records and focus sessions have been erased."}`
