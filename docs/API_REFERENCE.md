<h1 id="ch-10">Chapter 10: Complete API Reference</h1>

This chapter details every REST API endpoint exposed by the DRIFTLESS backend. All endpoints are prefixed with `/api/` and return `application/json`.

---

### 1. Register User
* **Endpoint:** `POST /api/auth/register/`
* **Authentication:** None (Public)
* **Handler:** `dashboard/core/views.py:register_view()`
* **Request Body:**
  ```json
  {
    "username": "student_alex",
    "email": "alex@university.edu",
    "password": "SecurePassword123!",
    "phone": "+15551234567",
    "persona": "student"
  }
  ```
* **Success Response (`201 Created`):**
  ```json
  {
    "success": true,
    "token": "4f8a9e2d1c3b5a7e9f0d2c4b6a8e0f1d3c5b7a9e",
    "username": "student_alex",
    "is_verified": true,
    "redirect": "/dashboard/"
  }
  ```
* **Error Response (`400 Bad Request`):**
  ```json
  {
    "error": "Please enter a valid email address.",
    "email": ["Please enter a valid email address."]
  }
  ```

---

### 2. Login User
* **Endpoint:** `POST /api/auth/login/`
* **Authentication:** None (Public)
* **Handler:** `dashboard/core/views.py:login_view()`
* **Request Body:** Accepts `username`, `email`, or `phone` in the identifier field:
  ```json
  {
    "username": "alex@university.edu",
    "password": "SecurePassword123!"
  }
  ```
* **Success Response (`200 OK`):**
  ```json
  {
    "success": true,
    "token": "4f8a9e2d1c3b5a7e9f0d2c4b6a8e0f1d3c5b7a9e",
    "username": "student_alex",
    "is_verified": true,
    "redirect": "/dashboard/"
  }
  ```

---

### 3. Google Sign-In & Demo Auth
* **Endpoint:** `POST /api/auth/google/`
* **Authentication:** None (Public)
* **Handler:** `dashboard/core/views.py:google_auth_view()`
* **Request Body:** Real Google ID token OR Demo payload:
  ```json
  {
    "email": "alex.demo@gmail.com",
    "name": "Alex Demo",
    "demo": true
  }
  ```
* **Success Response (`200 OK` / `201 Created`):**
  ```json
  {
    "success": true,
    "token": "4f8a9e2d1c3b5a7e9f0d2c4b6a8e0f1d3c5b7a9e",
    "username": "alex_demo",
    "email": "alex.demo@gmail.com",
    "name": "Alex Demo",
    "redirect": "/dashboard/"
  }
  ```

---

### 4. Regenerate API Token
* **Endpoint:** `POST /api/auth/regenerate-token/`
* **Authentication:** Session or Token (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:regenerate_token_view()`
* **Success Response (`200 OK`):**
  ```json
  {
    "token": "8a7e9f0d2c4b6a8e0f1d3c5b7a9e4f8a9e2d1c3b"
  }
  ```

---

### 5. Ingest Usage Dwell Logs
* **Endpoint:** `POST /api/usage/`
* **Authentication:** Token (`IsAuthenticated`), Rate Throttled (120/min)
* **Handler:** `dashboard/core/views.py:usage_log_view()`
* **Request Body (Batch Array or Single Object):**
  ```json
  [
    {
      "website_url": "github.com",
      "time_spent_seconds": 360,
      "date": "2026-10-31"
    },
    {
      "website_url": "instagram.com",
      "time_spent_seconds": 120,
      "date": "2026-10-31"
    }
  ]
  ```
* **Success Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "Logged 2 entries successfully"
  }
  ```

---

### 6. Analytics Summary
* **Endpoint:** `GET /api/summary/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:summary_view()`
* **Success Response (`200 OK`):**
  ```json
  {
    "stats": {
      "productive_time": "3h 45m",
      "distracting_time": "25m",
      "focus_efficiency": 90,
      "streak_days": 10,
      "longest_session": "45m"
    },
    "user": {
      "username": "student_alex",
      "persona": "student",
      "level": 5,
      "xp": 80,
      "xp_progress": 80,
      "has_zen_master": true,
      "has_deep_worker": true,
      "has_iron_will": true
    },
    "grove": {
      "days": [
        {
          "date": "2026-10-31",
          "status": "grown",
          "day_name": "Sat",
          "day_num": 31,
          "formatted_date": "Oct 31",
          "total_seconds": 14400
        }
      ],
      "total_grown": 28,
      "current_streak": 10
    },
    "weekly": {
      "labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
      "productive": [120, 150, 180, 200, 210, 190, 225],
      "distracting": [30, 25, 20, 15, 10, 20, 25],
      "others": [10, 15, 10, 5, 10, 15, 10]
    },
    "settings": {
      "focus_mode_active": false,
      "schedule_enabled": true,
      "schedule_start": "20:00",
      "schedule_end": "22:30",
      "blocked_sites": "instagram.com\nfacebook.com\nreddit.com\nyoutube.com",
      "allowed_sites": "github.com\nstackoverflow.com\ndocs.google.com"
    }
  }
  ```

---

### 7. Settings Management
* **Endpoint:** `GET /api/settings/` & `PATCH /api/settings/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:settings_view()`
* **Patch Body (Any subset):**
  ```json
  {
    "focus_mode_active": true,
    "schedule_enabled": true,
    "schedule_start": "21:00",
    "schedule_end": "23:00",
    "persona": "professional"
  }
  ```
* **Success Response (`200 OK`):** Returns updated `UserSettingsSerializer` payload plus `persona`.

---

### 8. Per-Site Limits CRUD
* **List / Create:** `GET/POST /api/limits/`
* **Detail / Patch / Delete:** `GET/PATCH/DELETE /api/limits/<int:pk>/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:limits_list_create_view()`, `limits_detail_view()`
* **Create Body:**
  ```json
  {
    "domain": "reddit.com",
    "daily_limit_minutes": 20,
    "enabled": true
  }
  ```
* **Success Response (`201 Created` / `200 OK`):**
  ```json
  {
    "id": 4,
    "domain": "reddit.com",
    "daily_limit_minutes": 20,
    "enabled": true
  }
  ```

---

### 9. Category Overrides CRUD
* **List / Create:** `GET/POST /api/categories/`
* **Delete:** `DELETE /api/categories/<int:pk>/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:categories_list_create_view()`, `categories_detail_view()`
* **Create Body:**
  ```json
  {
    "domain": "news.ycombinator.com",
    "category": "Productive sites"
  }
  ```

---

### 10. Focus Sessions
* **List / Record:** `GET/POST /api/sessions/`
* **Authentication:** Token or Session (`IsAuthenticated`)
* **Handler:** `dashboard/core/views.py:sessions_view()`
* **Record Body:**
  ```json
  {
    "duration_minutes": 25,
    "completed": true
  }
  ```

---

### 11. Privacy & Data Export / Erasure
* **Export:** `GET /api/data/export/`
  - Returns complete JSON export containing `profile`, `settings`, `usage_logs`, `site_limits`, and `focus_sessions`.
* **Erasure:** `POST /api/data/delete/`
  - Completely purges all `UsageLog`, `SiteLimit`, and `FocusSession` records for the user. Returns `{ "status": "success", "message": "All user data deleted" }`.
