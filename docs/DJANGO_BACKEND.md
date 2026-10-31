<h1 id="ch-9">Chapter 9: Django Backend Architecture</h1>

The DRIFTLESS backend is constructed using **Django 4.2+** and **Django REST Framework (DRF 3.17+)**. This chapter examines configuration settings, data models, serialization logic, analytics computations, streak algorithms, Green Grove calculations, and gamification mechanics.

## 9.1 Settings & Configuration Architecture
Key settings in `dashboard/driftless/settings.py`:
* **CORS & CSRF:** Configured for cross-origin extension communication and local development.
* **REST Framework Configuration:**
  - `DEFAULT_AUTHENTICATION_CLASSES`: `TokenAuthentication` and `SessionAuthentication`.
  - `DEFAULT_PERMISSION_CLASSES`: `IsAuthenticated` (view-level overrides for auth routes).
  - Rate Throttling: `SyncRateThrottle` limits sync ingestion to 120 requests/minute per authenticated user.
* **Security & Secret Hygiene:** Secrets are loaded from environment variables (`.env`). In development, fallback placeholders are provided for local presentation.

## 9.2 Domain Normalization & Classification Engine
All web traffic processed by the backend is routed through normalization and categorization functions in `dashboard/core/models.py`:
* **`clean_domain(url)`:** Strips protocol schemes (`http://`, `https://`), path segments, and leading `www.` subdomains.
* **`classify_domain(domain, user=None)`:** Determines the category:
  1. Checks if the user has an explicit record in `CategoryOverride`.
  2. Checks static `CATEGORY_MAP` (covering 45+ popular websites).
  3. Checks academic TLD regex (`.edu`, `.ac.uk`, `.org`).
  4. Defaults to `CATEGORY_OTHERS` (`'Others'`).

Standardized Categories (Migration 0006):
- `Productive sites`
- `Distracting sites`
- `Others`

## 9.3 Analytics & Streak Calculation Algorithm
In `dashboard/core/views.py:summary_view()`, analytics and streaks are computed strictly:
1. **Focus Efficiency Score:**
   $$\text{Efficiency} = \frac{\text{Productive Seconds}}{\text{Productive Seconds} + \text{Distracting Seconds}} \times 100$$
2. **Strict Consecutive Daily Streak:**
   - Evaluates consecutive days descending from yesterday back to 60 days.
   - For each day, the day is considered **successful** if:
     - Total logged seconds > 0.
     - No custom `SiteLimit` was exceeded.
     - Total unconfigured distracting time did NOT exceed `global_limit_minutes`.
     - Total productive focus time met or exceeded `focus_goal_minutes` (if configured).
   - The first day that breaches any limit terminates the streak count.

## 9.4 Green Grove 30-Day Forest Status Engine
The Green Grove visualizer calculates progress across the preceding 30 days (`views.py:552-649`):
* For each day in `[today - 29 days .. today]`:
  - **`status = 'empty'`:** No browsing dwell logs exist for that date (`total_seconds == 0`). Rendered as an empty soil plot.
  - **`status = 'grown'`:** User logged browsing activity and stayed strictly within all per-site and global distracting limits. Rendered as a healthy green pine tree.
  - **`status = 'withered'`:** User exceeded either a custom site limit or the global distracting limit. Rendered as a withered amber/gray tree.

![Green Grove Calculation Workflow](diagrams/workflow_7_green_grove.svg)

## 9.5 Gamification & Reward Engine
DRIFTLESS implements an ethical digital gamification system designed to reinforce habit formation without misleading financial claims:
* **Database Fields (`UserProfile`):** `level` (Integer), `xp` (Integer), and three badge flags: `has_zen_master`, `has_deep_worker`, `has_iron_will`.
* **Milestone Rules:**
  - 🧘‍♂️ **Zen Master:** Awarded for maintaining a 10-day focus streak without limit violations.
  - 🧠 **Deep Worker:** Awarded for completing 2+ hours (120 minutes) of deep focus sprints.
  - 🛡️ **Iron Will:** Awarded for immediate limit compliance (closing a distracting site upon receiving the 80% nudge).
* **Presentation Demo Helper (`seed_demo_gamification`):** Pre-seeds Level 5, 80 XP progress, and unlocks all 3 badges on initial registration or demo login.
* **API Delivery:** Returned via `GET /api/summary/` inside the `user` dictionary: `{ level, xp, xp_progress, has_zen_master, has_deep_worker, has_iron_will }`.

![Gamification Reward Flow](diagrams/gamification_reward_flow.svg)

## 9.6 Evolution of Authentication: Email OTP Removal
In earlier development (Migration 0008), an `EmailOTP` model was introduced to send 6-digit codes via Gmail SMTP. To ensure frictionless user onboarding during live presentations and avoid third-party email delivery delays, the OTP system was **completely removed in Migration 0009**:
* Removed `EmailOTP` model and its database table.
* Removed OTP generation, email dispatch, and verification endpoints.
* Replaced with streamlined direct registration: strict frontend regex validation, backend `EmailValidator` check, immediate `is_verified=True`, demo gamification seeding, DRF token generation, and instant redirect to `/dashboard/`.
