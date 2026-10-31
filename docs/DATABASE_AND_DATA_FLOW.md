<h1 id="ch-11">Chapter 11: Database Schema &amp; Migration History</h1>

This chapter details the relational database schema implemented in SQLite 3 via the Django ORM, followed by the complete chronological migration history.

## 11.1 Relational Entity-Relationship Diagram

![Database ER Diagram](diagrams/database_er_diagram.svg)

## 11.2 Model & Field Reference

### 1. `auth_user` (Django Built-in)
* `id`: `INTEGER [PK]`
* `username`: `VARCHAR(150) [Unique]`
* `email`: `VARCHAR(254)`
* `password`: `VARCHAR(128)` (PBKDF2 SHA-256 hash)
* `is_active`: `BOOLEAN`
* `date_joined`: `DATETIME`

### 2. `core_userprofile` (One-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK, Unique]`
* `phone`: `VARCHAR(32)` (Blank allowed)
* `persona`: `VARCHAR(20)` (Choices: `student`, `professional`, `influencer`, `creator`, `other`)
* `is_verified`: `BOOLEAN` (Default `True`)
* `xp`: `INTEGER` (Default `0`)
* `level`: `INTEGER` (Default `1`)
* `has_zen_master`: `BOOLEAN` (Default `False`)
* `has_deep_worker`: `BOOLEAN` (Default `False`)
* `has_iron_will`: `BOOLEAN` (Default `False`)

### 3. `core_usersettings` (One-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK, Unique]`
* `focus_mode_active`: `BOOLEAN` (Default `False`)
* `daily_limit_minutes`: `POSITIVE_INTEGER` (Default `60`)
* `focus_goal_minutes`: `POSITIVE_INTEGER` (Default `180` - 3 hours)
* `streak_days`: `POSITIVE_INTEGER` (Default `0`)
* `require_challenge`: `BOOLEAN` (Default `False`)
* `blocked_sites`: `TEXT` (Newline-delimited distracting domains)
* `allowed_sites`: `TEXT` (Newline-delimited productive domains)
* `schedule_enabled`: `BOOLEAN` (Default `False`)
* `schedule_start`: `VARCHAR(5)` (Default `'20:00'`)
* `schedule_end`: `VARCHAR(5)` (Default `'22:00'`)
* `updated_at`: `DATETIME`

### 4. `core_usagelog` (Many-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK]`
* `website_url`: `VARCHAR(255)`
* `time_spent_seconds`: `POSITIVE_INTEGER` (Default `0`)
* `category`: `VARCHAR(20)` (Default `'Others'`)
* `date`: `DATE`
* `created_at`: `DATETIME`
* `updated_at`: `DATETIME`

### 5. `core_sitelimit` (Many-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK]`
* `domain`: `VARCHAR(255)`
* `daily_limit_minutes`: `POSITIVE_INTEGER` (Default `30`)
* `enabled`: `BOOLEAN` (Default `True`)
* `created_at`: `DATETIME`
* `updated_at`: `DATETIME`

### 6. `core_categoryoverride` (Many-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK]`
* `domain`: `VARCHAR(255)`
* `category`: `VARCHAR(30)` (Choices: `Productive sites`, `Distracting sites`, `Others`)
* `created_at`: `DATETIME`
* `updated_at`: `DATETIME`

### 7. `core_focussession` (Many-to-One with `auth_user`)
* `id`: `INTEGER [PK]`
* `user_id`: `INTEGER [FK]`
* `duration_minutes`: `POSITIVE_INTEGER` (Default `25`)
* `started_at`: `DATETIME`
* `completed`: `BOOLEAN` (Default `True`)

---

## 11.3 Complete Migration History

| Migration File | Key Operations Performed | Rationale |
| :--- | :--- | :--- |
| `0001_initial.py` | Created `UsageLog`, `SiteLimit`, `CategoryOverride` models. | Baseline data schema for tracking and custom limits. |
| `0002_usagelog_category_usersettings.py` | Added `category` field to `UsageLog`; created `UserSettings` model. | Introduced user configuration and initial category tags. |
| `0003_userprofile.py` | Created `UserProfile` model with `phone` and `persona`. | Introduced multi-identifier login and persona support. |
| `0004_alter_userprofile_persona.py` | Expanded persona choices (`student`, `professional`, `influencer`, `creator`, `other`). | Allowed users to customize onboarding presets. |
| `0005_usersettings_allowed_sites_and_more.py` | Added `allowed_sites` and `focus_goal_minutes` to `UserSettings`. | Supported whitelist configuration and 3-hour daily goal ring. |
| `0006_alter_categoryoverride_category_and_more.py` | Standardized category choices to `Productive sites`, `Distracting sites`, `Others`. | Eliminated confusing 4-category split; aligned with modern UX. |
| `0007_usersettings_schedule_enabled_and_more.py` | Added `schedule_enabled`, `schedule_start`, `schedule_end` to `UserSettings`. | Backed Scheduled Focus Mode time-picker controls. |
| `0008_userprofile_is_verified_emailotp.py` | Added `is_verified` to `UserProfile`; created `EmailOTP` model. | Initial implementation of 6-digit email OTP system. |
| `0009_delete_emailotp.py` | Deleted `EmailOTP` model. | Removed email OTP in favor of streamlined direct signup. |
| `0010_userprofile_has_deep_worker_and_more.py` | Added `xp`, `level`, `has_zen_master`, `has_deep_worker`, `has_iron_will` to `UserProfile`. | Backed 3D gamification, XP progression, and badge unlocks. |
