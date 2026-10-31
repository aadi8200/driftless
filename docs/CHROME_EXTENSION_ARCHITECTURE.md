<h1 id="ch-8">Chapter 8: Chrome Extension Architecture</h1>

The DRIFTLESS browser extension is built on **Google Chrome Manifest V3**. This chapter details the service worker lifecycle, timer mechanics, escalation engine, blocking rules, schedule automation, and inter-process messaging catalog.

## 8.1 Service Worker Lifecycle & Precision Heartbeat
Under Manifest V3, background pages are replaced by **ephemeral service workers**. A service worker is started by browser events (such as alarms, tab focus changes, or runtime messages) and is automatically terminated by Chrome after approximately 30 seconds of inactivity.

### The 1-Second Heartbeat Pipeline
Standard background `setInterval` timers stop firing when the worker terminates, causing timer lag. DRIFTLESS overcomes this via an active tab heartbeat architecture:
1. `extension/content.js` runs in the page execution context on every standard HTTP/HTTPS page.
2. It monitors `visibilitychange`, `window.focus`, and `window.blur`.
3. When `!document.hidden && document.hasFocus()`, it executes a 1000ms interval loop.
4. Each second, it sends `PAGE_HEARTBEAT_TICK` to `background.js`.
5. The message wakes the service worker (if suspended), allowing `background.js` to accumulate active dwell time second-by-second into `siteTimes` in `chrome.storage.local`.
6. When the tab loses focus, `content.js` clears its interval and sends `PAGE_HEARTBEAT_PAUSE`, prompting `background.js` to execute `commitActiveTime()` and prevent phantom dwell accumulation.

![Precision Tracking Workflow](diagrams/workflow_1_tracking.svg)

## 8.2 3-Tier Escalation Engine & DNR Enforcement
DRIFTLESS enforces site limits through a graduated 3-tier escalation pipeline rather than sudden punitive cutoffs:

```text
[ Browsing Distracting Site ]
             │
             ▼ (Accumulated Seconds >= 80% Limit)
  Tier 1: 80% Gentle Nudge
  • state.nudged = true
  • sendNudgeNotification(domain)
  • "Almost at your daily limit! Consider wrapping up."
             │
             ▼ (Accumulated Seconds >= 100% Limit)
  Tier 2: 100% Limit Alert
  • state.blocked = true
  • sendLimitReachedNotification(domain)
  • "Daily limit reached. This site is now locked until midnight."
             │
             ▼ (Immediate DNR Dynamic Rule Injection)
  Tier 3: Declarative Net Request Block & Redirection
  • Injects DNR rule in ID range 1000..1999
  • content.js receives { blocked: true } -> redirects to blocked.html
  • Future network requests intercepted at browser engine level
```

![Escalation and Enforcement Workflow](diagrams/workflow_2_escalation_block.svg)

## 8.3 Declarative Net Request (DNR) Rule ID Catalog
DRIFTLESS segments its dynamic Declarative Net Request rules into distinct, collision-free numeric bands:

| Numeric Range | Rule Purpose | Action | Condition | Triggering Event |
| :--- | :--- | :--- | :--- | :--- |
| **`100` to `899`** | Manual Focus Mode & Scheduled Focus | `block` | `urlFilter: "||domain"`, all resource types | Focus Mode enabled, Scheduled start alarm |
| **`1000` to `1999`** | Per-Site 100% Limit Enforcement | `block` | `urlFilter: "||domain"`, all resource types | Accumulated time breaches 100% daily limit |
| **`2000` to `2009`** | Shorts & Reels Blocker | `block` | Rule 2001: `||youtube.com/shorts*`<br>Rule 2002: `||instagram.com/reels*` | Shorts & Reels toggle (Student persona) |

All rules specify `priority: 1` and target resource types: `main_frame`, `sub_frame`, `xmlhttprequest`, `script`, `image`, `stylesheet`, `font`, `media`, `websocket`, and `other`.

## 8.4 Scheduled Focus Mode Automation
Scheduled Focus allows users to establish daily recurring deep work windows (e.g., 20:00 to 22:30).
* **Alarms:** `background.js` schedules two daily Chrome alarms:
  - `driftless_schedule_start`: Fires at `schedule_start`.
  - `driftless_schedule_end`: Fires at `schedule_end`.
* **State Check:** On startup or schedule update, `evaluateScheduleState()` calls `isWithinScheduleWindow()`. If the current time is currently within the window, Focus Mode is automatically activated.
* **Midnight Crossing:** If `schedule_end < schedule_start` (e.g. 23:00 to 01:00), the window spans across midnight: time is within the window if `current >= start OR current < end`.

![Scheduled Focus Workflow](diagrams/workflow_3_scheduled_focus.svg)

## 8.5 Pomodoro Sprint State Machine
The Pomodoro feature implements structured sprint intervals:
* **Work Phase (25 Minutes):** User clicks "Start Pomodoro". Focus Mode is engaged (DNR rules 100..899 active). Chrome alarm `driftless_pomodoro` is scheduled for 25 minutes.
* **Completion & Transition:** At T+25m, the alarm fires. A desktop chime and notification alert the user. Focus Mode disengages, a `FocusSession` record is synced to `/api/sessions/`, +50 XP is awarded, and a 5-minute break alarm is scheduled.
* **Break Phase (5 Minutes):** Distracting sites are unblocked. Popup displays a relaxing green countdown timer.

![Pomodoro Sprint Workflow](diagrams/workflow_4_pomodoro.svg)

## 8.6 Cloud Synchronization & Midnight Reset
* **Periodic Sync (`ALARM_PERIODIC_SYNC`):** Scheduled with `periodInMinutes: 15`. Gathers `unsyncedDeltas` from `chrome.storage.local`, posts them to `POST /api/usage/`, fetches updated settings from `GET /api/settings/`, and resets `unsyncedDeltas`.
* **Midnight Reset (`ALARM_MIDNIGHT_RESET`):** Calculates exact milliseconds until local midnight (`00:00:00.050`). At midnight, clears `siteTimes`, resets `escalationState`, strips limit DNR rules `1000..1999`, and reschedules the alarm for the next midnight.

## 8.7 Complete Message Catalog
Below is the definitive catalog of all 14 message types handled by `background.js` via `chrome.runtime.onMessage.addListener`:

| Message Type | Direction | Payload Schema | Action Performed | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `PAGE_HEARTBEAT_TICK` | `content.js` -> `background.js` | `{ type, domain, url, timestamp }` | Validates active tab, increments dwell seconds, checks 80%/100% limits | `{ blocked, domain, elapsed, limit, nudgeAt }` |
| `PAGE_HEARTBEAT_PAUSE` | `content.js` -> `background.js` | `{ type, domain, timestamp }` | Flushes active dwell delta, marks tab inactive | `{ success: true }` |
| `SET_FOCUS_MODE` | `popup.js` -> `background.js` | `{ type, enabled: boolean }` | Toggles Focus Mode DNR rules (100..899), syncs to backend | `{ success: true, focusModeActive: boolean }` |
| `UPDATE_SCHEDULE` | `popup.js` -> `background.js` | `{ type, scheduleEnabled, scheduleStart, scheduleEnd }` | Saves schedule times, recreates start/end alarms, re-evaluates window | `{ success: true, scheduleEnabled, ... }` |
| `UPDATE_SITE_LISTS` | `popup.js` -> `background.js` | `{ type, distractingSites, productiveSites }` | Updates storage site lists, re-evaluates active focus rules, syncs to backend | `{ success: true }` |
| `SET_GLOBAL_LIMIT` | `popup.js` -> `background.js` | `{ type, limitMinutes: number }` | Updates `userTimeLimitMinutes`, syncs to `/api/settings/` | `{ success: true }` |
| `SET_CUSTOM_LIMIT` | `popup.js` -> `background.js` | `{ type, domain, limitMinutes }` | Sets per-domain limit, syncs `POST /api/limits/` | `{ success: true }` |
| `REMOVE_CUSTOM_LIMIT` | `popup.js` -> `background.js` | `{ type, domain }` | Removes custom limit, syncs `DELETE /api/limits/<id>/` | `{ success: true }` |
| `TRIGGER_SYNC` | `popup.js` -> `background.js` | `{ type }` | Triggers immediate `syncToBackend()` push and pull | `{ success: true }` |
| `RESET_ALL_TIMERS` | `popup.js` -> `background.js` | `{ type }` | Resets today's `siteTimes` and `escalationState` in storage | `{ success: true }` |
| `TOGGLE_SHORTS_REELS`| `popup.js` -> `background.js` | `{ type, enabled: boolean }` | Toggles DNR dynamic rules 2001 & 2002 for Shorts/Reels | `{ success: true, enabled: boolean }` |
| `START_POMODORO` | `popup.js` -> `background.js` | `{ type }` | Starts 25m work phase, activates focus DNR rules, sets alarm | `{ success: true, state: "running", mode: "work" }` |
| `STOP_POMODORO` | `popup.js` -> `background.js` | `{ type }` | Cancels Pomodoro alarm, deactivates focus rules, resets state | `{ success: true, state: "idle" }` |
| `PAUSE_POMODORO` | `popup.js` -> `background.js` | `{ type }` | Pauses Pomodoro timer and records remaining time | `{ success: true, state: "paused" }` |
