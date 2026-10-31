<h1 id="ch-14">Chapter 14: Privacy &amp; Security Architecture</h1>

DRIFTLESS is designed with a **privacy-first, local-first** philosophy. This chapter conducts an honest audit of what data is collected, how it is handled, and what is explicitly excluded.

---

## 14.1 Honest Content Script Audit (`content.js`)
Earlier documentation claimed that DRIFTLESS operated with "no content scripts". That is **no longer true**. A content script (`extension/content.js`) was added in late October to resolve Manifest V3 service worker throttling.

Because content scripts have technical access to page DOMs, the following boundaries are strictly enforced:

| Property | What `content.js` Reads | What `content.js` NEVER Reads |
| :--- | :--- | :--- |
| **Domain** | Reads `window.location.hostname` (e.g. `reddit.com`) | Does NOT read URL search parameters, hash fragments, or query strings |
| **Full URL** | Reads `window.location.href` ONLY to check if URL matches YouTube Shorts (`/shorts/`) or Instagram Reels (`/reels/`) | Does NOT log, transmit, or store search queries, article titles, or path strings |
| **Page DOM** | **Zero inspection.** Does not touch `document.body`, `document.getElementById`, or HTML nodes | Does NOT read page text, comments, articles, videos, or images |
| **User Input** | **Zero inspection.** No event listeners on `input`, `keydown`, `keypress`, or `change` | Does NOT read passwords, credit card numbers, form inputs, or keystrokes |
| **Cookies / Auth** | **Zero inspection.** Does not read `document.cookie`, `localStorage`, or `sessionStorage` | Does NOT read session tokens, cookies, auth headers, or credentials |

`content.js` operates solely as a **precision stopwatch pulse generator**, confirming whether the user is actively viewing and interacting with the browser tab.

---

## 14.2 Data Collection &amp; Storage Audit

### What Data IS Collected:
* **Account Credentials:** Username, email address, optional phone number, and bcrypt-hashed password (handled via Django standard auth).
* **Domain-Level Dwell Time:** Aggregated seconds spent per domain per calendar date (e.g., `github.com`: 3,600s on `2026-10-31`).
* **User Preferences:** Selected persona, custom per-site limits, schedule start/end times, and blocked/allowed site lists.
* **Gamification Progress:** XP points, user level, and 3 badge unlock booleans.

### What Data is NEVER Collected:
* Full browsing history, page titles, or search queries.
* Incognito browsing dwell time (extension disabled in incognito by default).
* Form inputs, passwords, credit card details, or financial data.
* Webpage contents, personal emails, or private messages.

---

## 14.3 Storage &amp; Transit Security
1. **Local-First Storage:** All real-time second counters and active timer states reside exclusively in the user's browser via `chrome.storage.local`.
2. **Token Authentication:** Extension-to-backend communication utilizes DRF Token Authentication (`Authorization: Token <key>`). Tokens can be instantly revoked and regenerated via `POST /api/auth/regenerate-token/`.
3. **Transport Encryption:** In production, all API communication must be enforced over TLS/HTTPS.
4. **Data Ownership:** The user has sovereign control over their data:
   - `GET /api/data/export/`: Complete 1-click JSON export of all stored data.
   - `POST /api/data/delete/`: Complete 1-click permanent erasure of all browsing logs, site limits, and focus sessions.


---

<h1 id="ch-16">Chapter 16: Known Limitations &amp; Technical Debt</h1>

In the interest of full technical transparency, this chapter documents the known limitations, architectural trade-offs, and minor technical debt in the current codebase.

---

## 16.1 Service Worker Cold-Start Latency
* **Behavior:** When the service worker in `background.js` is asleep, an incoming message or alarm requires ~150ms to 250ms to wake the V8 execution context.
* **Impact:** Minimal. `content.js` queues initial ticks safely, and the browser handles message awakening asynchronously.

---

## 16.2 Multi-Window Concurrent Dwell Tracking
* **Behavior:** Dwell tracking checks `sender.tab.active` within its browser window.
* **Limitation:** If a user opens two separate Chrome windows side-by-side on dual monitors and both windows are active, Chrome considers only the single window with OS operating system focus as currently focused. Time is accumulated only on the OS-focused window.

---

## 16.3 Manual Token Copy for Extension Linking
* **Behavior:** The extension does not currently utilize an automated OAuth cookie bridge to inherit the session from `http://127.0.0.1:8000/` automatically.
* **Workaround:** Users copy their API token from the dashboard header and paste it once into the extension popup. It persists indefinitely in `chrome.storage.local`.

---

## 16.4 Declarative Net Request Dynamic Rule Ceiling
* **Behavior:** Chrome enforces a hard ceiling of 5,000 dynamic DNR rules per extension.
* **Impact:** Negligible. DRIFTLESS utilizes rule IDs `100..899` (Focus Mode), `1000..1999` (Limit Blocks), and `2000..2009` (Shorts/Reels), which easily accommodates hundreds of configured domains without approaching the limit.

---

## 16.5 Gmail SMTP Fallback
* **Behavior:** In development mode without valid SMTP credentials, attempting to send email raises connection errors.
* **Solution Implemented:** Email OTP was completely removed in Migration 0009. The application now uses direct registration with strict format validation, avoiding external email delivery dependencies entirely.


---

<h1 id="ch-17">Chapter 17: Planned &amp; Unbuilt Features</h1>

To prevent any confusion regarding current capabilities versus future roadmap concepts, this chapter explicitly lists features that are **NOT BUILT** in the codebase as of October 31, 2026.

---

## 17.1 Real-World Physical or Monetary Rewards
* **Status:** `NOT BUILT`
* **Clarification:** The DRIFTLESS reward system consists entirely of **digital gamification** (user levels, XP points, 3D shiny badges in the web dashboard, and the 30-day Green Grove visual forest). The codebase does NOT contain integrations with tree-planting non-profits, payment processors, gift card APIs, or physical delivery services.

---

## 17.2 Native Mobile Companion Apps (iOS &amp; Android)
* **Status:** `NOT BUILT`
* **Clarification:** DRIFTLESS is implemented exclusively as a desktop Chrome extension and a responsive web dashboard. No Swift, Kotlin, or React Native mobile applications exist in the repository.

---

## 17.3 Social Sharing of Achievements &amp; Badges
* **Status:** `NOT BUILT`
* **Clarification:** Badges (*Zen Master*, *Deep Worker*, *Iron Will*) and streaks are stored in the user's private database profile and rendered on the private dashboard. There are no public user profile URLs or social media share sheet integrations.

---

## 17.4 Team &amp; Enterprise Workspace Dashboards
* **Status:** `NOT BUILT`
* **Clarification:** DRIFTLESS is designed as an individual personal wellbeing platform. There are no multi-tenant organizational hierarchies, team leaderboards, manager oversight views, or enterprise billing modules.

---

## 17.5 Automated Weekly Email Digest
* **Status:** `NOT BUILT`
* **Clarification:** There is no background cron job or scheduled task generating weekly PDF or HTML email summary digests. Analytics are viewed interactively on the web dashboard.
