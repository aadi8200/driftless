<h1 id="ch-12">Chapter 12: Frontend Architecture &amp; UI Design</h1>

The DRIFTLESS frontend consists of two distinct presentation applications:
1. **The Chrome Extension Popup (`popup.html` &amp; `popup.js`):** A compact, responsive browser action window.
2. **The Web Dashboard Application (`dashboard.html` &amp; `auth.html`):** A full-featured 3D Neumorphic / Glassmorphic single-page web interface.

Both applications share the **DRIFTLESS Design System**, featuring high-contrast typography, tactile depth, and a dual-theme color architecture.

---

## 12.1 Chrome Extension Popup Interface

The extension popup (`popup.html`) is structured with modular views and interactive modal drawers:

```text
┌────────────────────────────────────────────────────────┐
│  🍃 DRIFTLESS            [🔥 10-Day Streak]  [⚙️ Token] │
├────────────────────────────────────────────────────────┤
│  ⚡ FOCUS MODE                       [ Toggle Switch ]  │
│     Block all distracting sites instantly             │
├────────────────────────────────────────────────────────┤
│  🎬 BLOCK SHORTS & REELS (Student)   [ Toggle Switch ]  │
│     YouTube Shorts & Instagram Reels blocked           │
├────────────────────────────────────────────────────────┤
│  ⏰ SCHEDULED FOCUS                  [ Toggle Switch ]  │
│     Active 08:00 PM to 10:30 PM (Next: Today at 8:00)  │
│     ▼ Edit Times                                       │
│     [ Start: 20:00 ]  [ End: 22:30 ]  [ Save Button ]  │
├────────────────────────────────────────────────────────┤
│  🍅 POMODORO SPRINT                                    │
│     25:00 Focus Phase       [ Start Sprint ]  [ Reset ]│
├────────────────────────────────────────────────────────┤
│  ⏳ DISTRACTING SITES (Global Limit: 60m)  [ + Add ]   │
│     • instagram.com     45s / 2m    [ ⚙️ Limit ]  [ 🗑️ ] │
│     • reddit.com        12m / 20m   [ ⚙️ Limit ]  [ 🗑️ ] │
├────────────────────────────────────────────────────────┤
│  🌱 PRODUCTIVE SITES                      [ + Add ]   │
│     • github.com                    [ Whitelisted ]    │
│     • stackoverflow.com             [ Whitelisted ]    │
├────────────────────────────────────────────────────────┤
│  👤 Connected as student_alex        [ 🔗 Dashboard ]  │
│  🔄 Cloud Sync (Last: Just now)      [ Sync Now ]      │
└────────────────────────────────────────────────────────┘
```

### Key Popup UI Modules:
* **Welcome &amp; Persona Onboarding (`onboardingView`):** Displayed when `userPersona` is uninitialized. Steps user through initial brand introduction and persona selection.
* **Scheduled Focus Collapsible Drawer:** Expands when Scheduled Focus is active or tapped. Houses two HTML5 `<input type="time">` pickers, displays human-readable 12-hour formatted labels, and includes an explicit **Save** button.
* **Custom Limit Modal (`customLimitModal`):** Prompts for per-site minutes (1 to 1440) or provides a "Remove Limit" button to fall back to the global limit.
* **Global Limit Modal (`globalLimitModal`):** Modifies default limit for unconfigured distracting sites.

---

## 12.2 Web Dashboard Architecture (`dashboard.html`)

The web dashboard employs a modern **3D Neumorphic / Glassmorphic** aesthetic:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  🍃 DRIFTLESS  [ 👨‍🎓 Student ▼ ]     [ 🌓 Theme ]  [ 🔑 API Token ]  [ Logout ] │
├──────────────────────┬───────────────────────────────────────────────────────┤
│  SIDEBAR             │  MAIN WORKSPACE                                       │
│                      │                                                       │
│  [ Avatar ]          │  ⚡ FOCUS MODE STATUS CARD                             │
│  student_alex        │     [ ON / OFF Switch ]  Status: Focus Mode Active    │
│  LVL 5               │                                                       │
│  [================-] │  4 KPI CARDS (3D Layered Shadows):                    │
│  80 / 100 XP (80%)   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐ │
│                      │  │ 3h 45m    │ │ 25m       │ │ 90%       │ │ 🔥 10  │ │
│  MY BADGES (3D):     │  │ Productive│ │Distracting│ │ Efficiency│ │ Streak │ │
│  ┌────────────────┐  │  └───────────┘ └───────────┘ └───────────┘ └────────┘ │
│  │ 🧘‍♂️ Zen Master  │  │                                                       │
│  └────────────────┘  │  🎯 3-HOUR DAILY FOCUS GOAL RING                       │
│  ┌────────────────┐  │     Circular SVG Progress Ring (125% Goal Achieved)   │
│  │ 🧠 Deep Worker │  │                                                       │
│  └────────────────┘  │  📊 ANALYTICS CHART [ Bar Chart ] [ Line Chart ]       │
│  ┌────────────────┐  │     Weekly category dwell breakdown (Productive vs    │
│  │ 🛡️ Iron Will   │  │     Distracting vs Others)                            │
│  └────────────────┘  │                                                       │
│                      │  🌲 30-DAY GREEN GROVE FOREST                         │
│  PRIORITY TO-DOS:    │     30 tactile tree icons (Pine = Success,            │
│  [ Task input... ]   │     Withered = Exceeded, Empty = No Data)             │
│  [x] Complete paper  │                                                       │
│  [ ] Review PR #42   │  🛑 TOP DISTRACTIONS & SITE LIMITS                    │
│  [ 1 / 2 Done ]      │     Per-domain limit editor with live progress bars   │
└──────────────────────┴───────────────────────────────────────────────────────┘
```

### Neumorphic &amp; 3D CSS Design System:
* **Dual Drop Shadows:** Cards utilize opposing layered shadows:
  ```css
  box-shadow: 8px 8px 16px rgba(0, 0, 0, 0.06), -8px -8px 16px rgba(255, 255, 255, 0.8);
  ```
* **Glassmorphic Navigation:** Top header and sidebar feature:
  ```css
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  ```
* **Animated XP Bar:** Features shimmering light bars and smooth CSS width transitions.
* **3D Metallic Badges:** Features metallic bevel borders, tactile drop shadows, and a 45-degree animated sheen sweep on hover (`.badge-sheen`).
* **Priority To-Do Planner:** Interactive daily checklist widget saving directly to `localStorage['driftless_priority_todos']`.

---

## 12.3 Split-Screen Authentication UI (`auth.html`)
Inspired by modern SaaS interfaces:
* **Left Branding Panel (45%):** Displays the official green leaf "D" brand logo, large typography, and value proposition feature highlights.
* **Right Auth Card (55%):** Form card (max-width: 440px) featuring:
  - Prominent "Continue with Google" button with official Google SVG mark.
  - "or continue with email" horizontal divider.
  - High-contrast inputs (48px height) with emerald focus rings.
  - Strict client-side email format regex validation.
  - Instant direct sign-in and sign-up with demo shortcuts.

---

## 12.4 Dual-Theme Token Architecture (`theme.css`)
DRIFTLESS supports two palettes toggled via `localStorage['driftless-theme']`:
1. **Calm Sky (Light Mode):** Clean slate background (`#f8fafc`), crisp white cards, and ocean blue / emerald accents.
2. **Opal Noir (Dark Mode):** Deep obsidian background (`#090d16`), elevated dark slate cards (`#131b2e`), and luminescent cyan / emerald glows.
