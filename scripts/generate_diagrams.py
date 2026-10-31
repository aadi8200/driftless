import os

os.makedirs('docs/diagrams', exist_ok=True)

# 1. System Architecture Diagram
svg_system_architecture = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 680" width="1000" height="680" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <linearGradient id="gradExt" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#eff6ff" />
      <stop offset="100%" stop-color="#dbeafe" />
    </linearGradient>
    <linearGradient id="gradBack" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f0fdf4" />
      <stop offset="100%" stop-color="#dcfce7" />
    </linearGradient>
    <linearGradient id="gradDash" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fdf4ff" />
      <stop offset="100%" stop-color="#fae8ff" />
    </linearGradient>
    <linearGradient id="gradDb" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fff7ed" />
      <stop offset="100%" stop-color="#ffedd5" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.08" />
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569" />
    </marker>
    <marker id="arrowBlue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb" />
    </marker>
    <marker id="arrowGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a" />
    </marker>
  </defs>

  <!-- Title -->
  <text x="500" y="40" text-anchor="middle" font-size="22" font-weight="bold" fill="#0f172a">DRIFTLESS — System Architecture (Manifest V3 &amp; Django/DRF)</text>
  <text x="500" y="65" text-anchor="middle" font-size="13" fill="#64748b">Cross-Tier Interaction: Client-Side Extension, REST API Backend, and Modern Web Dashboard</text>

  <!-- Box 1: Browser Extension Client -->
  <rect x="40" y="95" width="440" height="545" rx="16" fill="url(#gradExt)" stroke="#bfdbfe" stroke-width="2" filter="url(#shadow)" />
  <rect x="55" y="110" width="410" height="34" rx="8" fill="#2563eb" />
  <text x="260" y="132" text-anchor="middle" font-size="14" font-weight="bold" fill="#ffffff">CHROME EXTENSION CLIENT (Manifest V3)</text>

  <!-- Content Script Node -->
  <rect x="65" y="160" width="390" height="95" rx="10" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5" />
  <text x="80" y="185" font-size="13" font-weight="bold" fill="#1e3a8a">Active Tab Content Script (content.js)</text>
  <text x="80" y="205" font-size="11" fill="#475569">• Ticks every 1,000ms while tab is visible and focused</text>
  <text x="80" y="223" font-size="11" fill="#475569">• Only reads window.location.hostname &amp; href (Zero DOM inspection)</text>
  <text x="80" y="241" font-size="11" fill="#475569">• Sends PAGE_HEARTBEAT_TICK and PAGE_HEARTBEAT_PAUSE</text>

  <!-- Service Worker Node -->
  <rect x="65" y="270" width="390" height="185" rx="10" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5" />
  <text x="80" y="295" font-size="13" font-weight="bold" fill="#1e3a8a">Background Service Worker (background.js)</text>
  <text x="80" y="315" font-size="11" fill="#475569">• Alarms: Periodic Sync (15m), Midnight Reset, Tick, Schedule, Pomodoro</text>
  <text x="80" y="333" font-size="11" fill="#475569">• Second-precision timer accumulation &amp; 3-tier limit evaluation</text>
  <text x="80" y="351" font-size="11" fill="#475569">• DNR Engine: Focus rules (100..899), Limit blocks (1000..1999), Shorts (2000..2009)</text>
  <text x="80" y="369" font-size="11" fill="#475569">• Scheduled Focus: start &amp; end alarms toggle DNR blocking automatically</text>
  <text x="80" y="387" font-size="11" fill="#475569">• Pomodoro State Machine: 25m focus sprint / 5m break alarm cycle</text>
  <text x="80" y="405" font-size="11" fill="#475569">• Chrome Storage Local: siteTimes, siteLimits, escalationState, tokens</text>
  <text x="80" y="423" font-size="11" fill="#475569">• Redirection Engine: sends blocked sites to blocked.html</text>

  <!-- Popup UI Node -->
  <rect x="65" y="470" width="390" height="150" rx="10" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5" />
  <text x="80" y="495" font-size="13" font-weight="bold" fill="#1e3a8a">Extension Popup UI (popup.html &amp; popup.js)</text>
  <text x="80" y="515" font-size="11" fill="#475569">• Welcome Screen &amp; Persona Selector (Student, Professional, etc.)</text>
  <text x="80" y="533" font-size="11" fill="#475569">• Focus Mode Toggle &amp; Shorts/Reels Blocker (Student only)</text>
  <text x="80" y="551" font-size="11" fill="#475569">• Scheduled Focus inline time pickers (Start &amp; End) + Save Button</text>
  <text x="80" y="569" font-size="11" fill="#475569">• Pomodoro sprint controls (Start / Stop) with live countdown</text>
  <text x="80" y="587" font-size="11" fill="#475569">• Distracting &amp; Productive lists, per-site modal limits &amp; global defaults</text>
  <text x="80" y="605" font-size="11" fill="#475569">• Connected account status, API Token configuration, Reset Timers</text>

  <!-- Box 2: Django Backend & DRF API -->
  <rect x="520" y="95" width="440" height="315" rx="16" fill="url(#gradBack)" stroke="#bbf7d0" stroke-width="2" filter="url(#shadow)" />
  <rect x="535" y="110" width="410" height="34" rx="8" fill="#16a34a" />
  <text x="740" y="132" text-anchor="middle" font-size="14" font-weight="bold" fill="#ffffff">DJANGO 4.2+ &amp; DJANGO REST FRAMEWORK</text>

  <!-- REST API Endpoints -->
  <rect x="545" y="160" width="390" height="230" rx="10" fill="#ffffff" stroke="#86efac" stroke-width="1.5" />
  <text x="560" y="185" font-size="13" font-weight="bold" fill="#14532d">Core REST API Views &amp; Serialization (views.py)</text>
  <text x="560" y="205" font-size="11" fill="#475569">• Auth: /api/auth/register/, login/, logout/, google/, regenerate-token/</text>
  <text x="560" y="223" font-size="11" fill="#475569">• Sync &amp; Usage: /api/usage/ (Ingests dwell deltas from extension)</text>
  <text x="560" y="241" font-size="11" fill="#475569">• Analytics: /api/summary/ (Daily/Weekly totals, streaks, efficiency, grove)</text>
  <text x="560" y="259" font-size="11" fill="#475569">• Settings &amp; Persona: /api/settings/ (Schedule times, site lists, persona)</text>
  <text x="560" y="277" font-size="11" fill="#475569">• Site Limits &amp; Overrides: /api/limits/, /api/categories/</text>
  <text x="560" y="295" font-size="11" fill="#475569">• Focus Sessions: /api/sessions/ (Records completed focus sprints)</text>
  <text x="560" y="313" font-size="11" fill="#475569">• Data Privacy: /api/data/export/ (JSON), /api/data/delete/</text>
  <text x="560" y="331" font-size="11" fill="#475569">• Gamification Seeding: seeds Level 5, 80 XP, and 3 presentation badges</text>
  <text x="560" y="349" font-size="11" fill="#475569">• Domain Classifier: clean_domain(), classify_domain() master map</text>
  <text x="560" y="367" font-size="11" fill="#475569">• Green Grove Engine: 30-day strict tree evaluation (grown vs withered)</text>

  <!-- Box 3: Database Storage -->
  <rect x="520" y="425" width="440" height="100" rx="14" fill="url(#gradDb)" stroke="#fed7aa" stroke-width="2" filter="url(#shadow)" />
  <rect x="535" y="435" width="410" height="26" rx="6" fill="#ea580c" />
  <text x="740" y="452" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">SQLITE PERSISTENCE LAYER (models.py)</text>
  <text x="545" y="480" font-size="11" fill="#7c2d12">• UserProfile (persona, is_verified, xp, level, has_zen_master, deep_worker, iron_will)</text>
  <text x="545" y="498" font-size="11" fill="#7c2d12">• UserSettings (focus_mode_active, schedule_enabled, schedule_start, schedule_end)</text>
  <text x="545" y="516" font-size="11" fill="#7c2d12">• UsageLog, SiteLimit, CategoryOverride, FocusSession, DRF AuthToken</text>

  <!-- Box 4: Web Dashboard Frontend -->
  <rect x="520" y="540" width="440" height="100" rx="14" fill="url(#gradDash)" stroke="#f5d0fe" stroke-width="2" filter="url(#shadow)" />
  <rect x="535" y="550" width="410" height="26" rx="6" fill="#9333ea" />
  <text x="740" y="567" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">WEB DASHBOARD &amp; AUTH UI (dashboard.html &amp; auth.html)</text>
  <text x="545" y="592" font-size="11" fill="#581c87">• 3D Neumorphic / Glassmorphism UI cards with soft dual shadows</text>
  <text x="545" y="610" font-size="11" fill="#581c87">• Left Sidebar: XP Bar, 3D Shiny Badges, Priority To-Do Planner, Persona selector</text>
  <text x="545" y="628" font-size="11" fill="#581c87">• Green Grove 30-day visual forest, Chart.js analytics (Bar &amp; Line), Live/Demo mode</text>

  <!-- Connecting Lines -->
  <!-- Content script to background -->
  <line x1="260" y1="255" x2="260" y2="270" stroke="#2563eb" stroke-width="2" marker-end="url(#arrowBlue)" />
  <!-- Popup to background -->
  <line x1="260" y1="470" x2="260" y2="455" stroke="#2563eb" stroke-width="2" marker-end="url(#arrowBlue)" />

  <!-- Extension to Backend HTTP -->
  <path d="M 455 350 L 520 270" fill="none" stroke="#16a34a" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrowGreen)" />
  <rect x="445" y="295" width="85" height="24" rx="4" fill="#ffffff" stroke="#16a34a" stroke-width="1" />
  <text x="487" y="311" text-anchor="middle" font-size="10" font-weight="bold" fill="#16a34a">REST API Sync</text>

  <!-- Backend to Database -->
  <line x1="740" y1="410" x2="740" y2="425" stroke="#ea580c" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Dashboard to Backend HTTP -->
  <line x1="740" y1="540" x2="740" y2="525" stroke="#9333ea" stroke-width="2" marker-end="url(#arrow)" />
</svg>'''

with open('docs/diagrams/system_architecture.svg', 'w', encoding='utf-8') as f:
    f.write(svg_system_architecture)

print('Generated system_architecture.svg')

# 2. Gamification & Reward System Flow Diagram
svg_reward_flow = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 950 520" width="950" height="520" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="3" stdDeviation="5" flood-opacity="0.08" />
    </filter>
    <marker id="flowArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#0284c7" />
    </marker>
  </defs>

  <!-- Title -->
  <text x="475" y="38" text-anchor="middle" font-size="20" font-weight="bold" fill="#0f172a">DRIFTLESS — Gamification &amp; Reward System Flow</text>
  <text x="475" y="62" text-anchor="middle" font-size="12" fill="#64748b">Complete Lifecycle: User Behavioral Milestones → Rule Evaluation → Database State → 3D Visual Badges</text>

  <!-- Step 1: User Actions -->
  <rect x="40" y="90" width="190" height="380" rx="12" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="50" y="100" width="170" height="30" rx="6" fill="#475569" />
  <text x="135" y="120" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">1. USER ACTIONS</text>
  
  <rect x="50" y="145" width="170" height="85" rx="8" fill="#ffffff" stroke="#e2e8f0" />
  <text x="60" y="167" font-size="11" font-weight="bold" fill="#0f172a">Daily Focus Streak</text>
  <text x="60" y="185" font-size="10" fill="#64748b">• Stays within all daily limits</text>
  <text x="60" y="200" font-size="10" fill="#64748b">• Achieves daily focus goal</text>
  <text x="60" y="215" font-size="10" fill="#16a34a">→ 10 Consecutive Days</text>

  <rect x="50" y="245" width="170" height="85" rx="8" fill="#ffffff" stroke="#e2e8f0" />
  <text x="60" y="267" font-size="11" font-weight="bold" fill="#0f172a">Deep Work Sprint</text>
  <text x="60" y="285" font-size="10" fill="#64748b">• Enables Focus Mode</text>
  <text x="60" y="300" font-size="10" fill="#64748b">• Completes Pomodoro sprints</text>
  <text x="60" y="315" font-size="10" fill="#2563eb">→ 2+ Hours Focus</text>

  <rect x="50" y="345" width="170" height="110" rx="8" fill="#ffffff" stroke="#e2e8f0" />
  <text x="60" y="367" font-size="11" font-weight="bold" fill="#0f172a">Immediate Compliance</text>
  <text x="60" y="385" font-size="10" fill="#64748b">• Receives 80% Nudge</text>
  <text x="60" y="400" font-size="10" fill="#64748b">• Immediately closes tab</text>
  <text x="60" y="415" font-size="10" fill="#64748b">• Never breaches 100%</text>
  <text x="60" y="430" font-size="10" fill="#059669">→ Demonstrates Iron Will</text>

  <!-- Step 2: Rule Verification Engine -->
  <rect x="270" y="90" width="200" height="380" rx="12" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="280" y="100" width="180" height="30" rx="6" fill="#0284c7" />
  <text x="370" y="120" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">2. RULE CHECK</text>

  <rect x="280" y="145" width="180" height="95" rx="8" fill="#ffffff" stroke="#bfdbfe" />
  <text x="290" y="167" font-size="11" font-weight="bold" fill="#0369a1">Streak Rule Verification</text>
  <text x="290" y="185" font-size="10" fill="#475569">File: core/views.py</text>
  <text x="290" y="200" font-size="10" fill="#475569">Func: summary_view()</text>
  <text x="290" y="215" font-size="10" fill="#64748b">Check: streak_days >= 10</text>
  <text x="290" y="230" font-size="10" fill="#0284c7">Awards: Zen Master Badge</text>

  <rect x="280" y="250" width="180" height="95" rx="8" fill="#ffffff" stroke="#bfdbfe" />
  <text x="290" y="272" font-size="11" font-weight="bold" fill="#0369a1">Deep Worker Verification</text>
  <text x="290" y="290" font-size="10" fill="#475569">File: core/views.py &amp; models.py</text>
  <text x="290" y="305" font-size="10" fill="#475569">Check: FocusSession >= 120m</text>
  <text x="290" y="320" font-size="10" fill="#64748b">XP Gain: +100 XP per 60m</text>
  <text x="290" y="335" font-size="10" fill="#0284c7">Awards: Deep Worker Badge</text>

  <rect x="280" y="355" width="180" height="100" rx="8" fill="#ffffff" stroke="#bfdbfe" />
  <text x="290" y="377" font-size="11" font-weight="bold" fill="#0369a1">Iron Will &amp; Demo Seed</text>
  <text x="290" y="395" font-size="10" fill="#475569">File: core/models.py</text>
  <text x="290" y="410" font-size="10" fill="#475569">Func: seed_demo_gamification()</text>
  <text x="290" y="425" font-size="10" fill="#64748b">Pre-seeds: Lvl 5, 80 XP</text>
  <text x="290" y="440" font-size="10" fill="#0284c7">Awards: Iron Will Badge</text>

  <!-- Step 3: Database Persistence -->
  <rect x="510" y="90" width="190" height="380" rx="12" fill="#fff7ed" stroke="#fed7aa" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="520" y="100" width="170" height="30" rx="6" fill="#ea580c" />
  <text x="605" y="120" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">3. DATA STORED</text>

  <rect x="520" y="145" width="170" height="180" rx="8" fill="#ffffff" stroke="#fed7aa" />
  <text x="530" y="167" font-size="11" font-weight="bold" fill="#9a3412">UserProfile Model</text>
  <text x="530" y="185" font-size="10" fill="#475569">Migration: 0010_userprofile...</text>
  <text x="530" y="205" font-size="10" fill="#c2410c">• level = 5 (Integer)</text>
  <text x="530" y="222" font-size="10" fill="#c2410c">• xp = 80 (Integer)</text>
  <text x="530" y="239" font-size="10" fill="#c2410c">• has_zen_master = True</text>
  <text x="530" y="256" font-size="10" fill="#c2410c">• has_deep_worker = True</text>
  <text x="530" y="273" font-size="10" fill="#c2410c">• has_iron_will = True</text>
  <text x="530" y="295" font-size="10" fill="#475569">API Expose: /api/summary/</text>
  <text x="530" y="312" font-size="10" fill="#64748b">Returns: user.xp, level, badges</text>

  <rect x="520" y="335" width="170" height="120" rx="8" fill="#ffffff" stroke="#fed7aa" />
  <text x="530" y="357" font-size="11" font-weight="bold" fill="#9a3412">API Response Payload</text>
  <text x="530" y="375" font-size="9" font-family="monospace" fill="#475569">"user": {</text>
  <text x="540" y="390" font-size="9" font-family="monospace" fill="#475569">"level": 5,</text>
  <text x="540" y="405" font-size="9" font-family="monospace" fill="#475569">"xp": 80,</text>
  <text x="540" y="420" font-size="9" font-family="monospace" fill="#475569">"has_zen_master": true,</text>
  <text x="540" y="435" font-size="9" font-family="monospace" fill="#475569">"has_deep_worker": true</text>
  <text x="530" y="448" font-size="9" font-family="monospace" fill="#475569">}</text>

  <!-- Step 4: UI Representation -->
  <rect x="740" y="90" width="170" height="380" rx="12" fill="#f0fdf4" stroke="#bbf7d0" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="750" y="100" width="150" height="30" rx="6" fill="#16a34a" />
  <text x="825" y="120" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">4. REWARD SHOWN</text>

  <rect x="750" y="145" width="150" height="65" rx="8" fill="#ffffff" stroke="#bbf7d0" />
  <text x="760" y="167" font-size="10" font-weight="bold" fill="#14532d">Animated XP Bar</text>
  <text x="760" y="183" font-size="9" fill="#475569">• Gradient fill (green/cyan)</text>
  <text x="760" y="198" font-size="9" fill="#475569">• "LVL 5" &amp; "80/100 XP (80%)"</text>

  <rect x="750" y="218" width="150" height="70" rx="8" fill="#ffffff" stroke="#eab308" />
  <text x="760" y="238" font-size="10" font-weight="bold" fill="#854d0e">🧘‍♂️ Zen Master (Gold)</text>
  <text x="760" y="254" font-size="9" fill="#475569">• 3D metallic shadow</text>
  <text x="760" y="269" font-size="9" fill="#475569">• Hover sheen sweep animation</text>

  <rect x="750" y="296" width="150" height="70" rx="8" fill="#ffffff" stroke="#3b82f6" />
  <text x="760" y="316" font-size="10" font-weight="bold" fill="#1e40af">🧠 Deep Worker (Blue)</text>
  <text x="760" y="332" font-size="9" fill="#475569">• Sapphire 3D badge styling</text>
  <text x="760" y="347" font-size="9" fill="#475569">• Unlocked for 2h deep focus</text>

  <rect x="750" y="374" width="150" height="80" rx="8" fill="#ffffff" stroke="#10b981" />
  <text x="760" y="394" font-size="10" font-weight="bold" fill="#065f46">🛡️ Iron Will (Emerald)</text>
  <text x="760" y="410" font-size="9" fill="#475569">• Emerald 3D bevel &amp; sheen</text>
  <text x="760" y="425" font-size="9" fill="#475569">• Unlocked by limit discipline</text>
  <text x="760" y="440" font-size="9" fill="#16a34a">Digital-only: No cash/prizes</text>

  <!-- Connectors -->
  <line x1="230" y1="280" x2="270" y2="280" stroke="#0284c7" stroke-width="2" marker-end="url(#flowArrow)" />
  <line x1="470" y1="280" x2="510" y2="280" stroke="#0284c7" stroke-width="2" marker-end="url(#flowArrow)" />
  <line x1="700" y1="280" x2="740" y2="280" stroke="#0284c7" stroke-width="2" marker-end="url(#flowArrow)" />
</svg>'''

with open('docs/diagrams/gamification_reward_flow.svg', 'w', encoding='utf-8') as f:
    f.write(svg_reward_flow)

print('Generated gamification_reward_flow.svg')

# 3. Database ER Diagram
svg_database_er = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 620" width="980" height="620" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <filter id="tableShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-opacity="0.1" />
    </filter>
  </defs>

  <!-- Title -->
  <text x="490" y="35" text-anchor="middle" font-size="20" font-weight="bold" fill="#0f172a">DRIFTLESS — Relational Database Schema (SQLite / Django ORM)</text>
  <text x="490" y="58" text-anchor="middle" font-size="12" fill="#64748b">Current Schema as of Migrations 0001 through 0010 (EmailOTP deleted in 0009)</text>

  <!-- Table 1: auth_user (Django Built-in) -->
  <g transform="translate(40, 80)">
    <rect width="250" height="160" rx="8" fill="#ffffff" stroke="#94a3b8" stroke-width="1.5" filter="url(#tableShadow)" />
    <path d="M 0 0 L 250 0 L 250 28 L 0 28 Z" fill="#475569" />
    <text x="125" y="19" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">auth_user (Django Core)</text>
    <text x="12" y="48" font-size="11" font-weight="bold" fill="#0f172a">id</text><text x="130" y="48" font-size="11" fill="#64748b">INTEGER [PK]</text>
    <text x="12" y="68" font-size="11" font-weight="bold" fill="#0f172a">username</text><text x="130" y="68" font-size="11" fill="#64748b">VARCHAR(150) [UQ]</text>
    <text x="12" y="88" font-size="11" fill="#0f172a">email</text><text x="130" y="88" font-size="11" fill="#64748b">VARCHAR(254)</text>
    <text x="12" y="108" font-size="11" fill="#0f172a">password</text><text x="130" y="108" font-size="11" fill="#64748b">VARCHAR(128)</text>
    <text x="12" y="128" font-size="11" fill="#0f172a">is_active</text><text x="130" y="128" font-size="11" fill="#64748b">BOOLEAN</text>
    <text x="12" y="148" font-size="11" fill="#0f172a">date_joined</text><text x="130" y="148" font-size="11" fill="#64748b">DATETIME</text>
  </g>

  <!-- Table 2: UserProfile (OneToOne) -->
  <g transform="translate(360, 80)">
    <rect width="270" height="235" rx="8" fill="#ffffff" stroke="#0284c7" stroke-width="1.5" filter="url(#tableShadow)" />
    <path d="M 0 0 L 270 0 L 270 28 L 0 28 Z" fill="#0284c7" />
    <text x="135" y="19" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">core_userprofile (1-to-1 User)</text>
    <text x="12" y="48" font-size="11" font-weight="bold" fill="#0f172a">id</text><text x="140" y="48" font-size="11" fill="#64748b">INTEGER [PK]</text>
    <text x="12" y="68" font-size="11" font-weight="bold" fill="#0f172a">user_id</text><text x="140" y="68" font-size="11" fill="#64748b">INTEGER [FK, UQ]</text>
    <text x="12" y="88" font-size="11" fill="#0f172a">phone</text><text x="140" y="88" font-size="11" fill="#64748b">VARCHAR(32)</text>
    <text x="12" y="108" font-size="11" fill="#0f172a">persona</text><text x="140" y="108" font-size="11" fill="#64748b">VARCHAR(20)</text>
    <text x="12" y="128" font-size="11" fill="#0f172a">is_verified</text><text x="140" y="128" font-size="11" fill="#64748b">BOOLEAN (default True)</text>
    <text x="12" y="148" font-size="11" font-weight="bold" fill="#0284c7">xp</text><text x="140" y="148" font-size="11" fill="#0284c7">INTEGER (default 0)</text>
    <text x="12" y="168" font-size="11" font-weight="bold" fill="#0284c7">level</text><text x="140" y="168" font-size="11" fill="#0284c7">INTEGER (default 1)</text>
    <text x="12" y="188" font-size="11" fill="#0f172a">has_zen_master</text><text x="140" y="188" font-size="11" fill="#64748b">BOOLEAN (default False)</text>
    <text x="12" y="208" font-size="11" fill="#0f172a">has_deep_worker</text><text x="140" y="208" font-size="11" fill="#64748b">BOOLEAN (default False)</text>
    <text x="12" y="228" font-size="11" fill="#0f172a">has_iron_will</text><text x="140" y="228" font-size="11" fill="#64748b">BOOLEAN (default False)</text>
  </g>

  <!-- Table 3: UserSettings (OneToOne) -->
  <g transform="translate(680, 80)">
    <rect width="260" height="255" rx="8" fill="#ffffff" stroke="#16a34a" stroke-width="1.5" filter="url(#tableShadow)" />
    <path d="M 0 0 L 260 0 L 260 28 L 0 28 Z" fill="#16a34a" />
    <text x="130" y="19" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">core_usersettings (1-to-1 User)</text>
    <text x="12" y="48" font-size="11" font-weight="bold" fill="#0f172a">id</text><text x="140" y="48" font-size="11" fill="#64748b">INTEGER [PK]</text>
    <text x="12" y="68" font-size="11" font-weight="bold" fill="#0f172a">user_id</text><text x="140" y="68" font-size="11" fill="#64748b">INTEGER [FK, UQ]</text>
    <text x="12" y="88" font-size="11" fill="#0f172a">focus_mode_active</text><text x="140" y="88" font-size="11" fill="#64748b">BOOLEAN</text>
    <text x="12" y="108" font-size="11" fill="#0f172a">daily_limit_minutes</text><text x="140" y="108" font-size="11" fill="#64748b">INTEGER</text>
    <text x="12" y="128" font-size="11" fill="#0f172a">focus_goal_minutes</text><text x="140" y="128" font-size="11" fill="#64748b">INTEGER</text>
    <text x="12" y="148" font-size="11" fill="#0f172a">streak_days</text><text x="140" y="148" font-size="11" fill="#64748b">INTEGER</text>
    <text x="12" y="168" font-size="11" fill="#0f172a">blocked_sites</text><text x="140" y="168" font-size="11" fill="#64748b">TEXT</text>
    <text x="12" y="188" font-size="11" fill="#0f172a">allowed_sites</text><text x="140" y="188" font-size="11" fill="#64748b">TEXT</text>
    <text x="12" y="208" font-size="11" font-weight="bold" fill="#16a34a">schedule_enabled</text><text x="140" y="208" font-size="11" fill="#16a34a">BOOLEAN</text>
    <text x="12" y="228" font-size="11" font-weight="bold" fill="#16a34a">schedule_start</text><text x="140" y="228" font-size="11" fill="#16a34a">VARCHAR(5)</text>
    <text x="12" y="248" font-size="11" font-weight="bold" fill="#16a34a">schedule_end</text><text x="140" y="248" font-size="11" fill="#16a34a">VARCHAR(5)</text>
  </g>

  <!-- Table 4: UsageLog (FK to User) -->
  <g transform="translate(40, 360)">
    <rect width="250" height="175" rx="8" fill="#ffffff" stroke="#d97706" stroke-width="1.5" filter="url(#tableShadow)" />
    <path d="M 0 0 L 250 0 L 250 28 L 0 28 Z" fill="#d97706" />
    <text x="125" y="19" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">core_usagelog (1-to-Many)</text>
    <text x="12" y="48" font-size="11" font-weight="bold" fill="#0f172a">id</text><text x="130" y="48" font-size="11" fill="#64748b">INTEGER [PK]</text>
    <text x="12" y="68" font-size="11" font-weight="bold" fill="#0f172a">user_id</text><text x="130" y="68" font-size="11" fill="#64748b">INTEGER [FK]</text>
    <text x="12" y="88" font-size="11" fill="#0f172a">website_url</text><text x="130" y="88" font-size="11" fill="#64748b">VARCHAR(255)</text>
    <text x="12" y="108" font-size="11" fill="#0f172a">time_spent_seconds</text><text x="130" y="108" font-size="11" fill="#64748b">INTEGER</text>
    <text x="12" y="128" font-size="11" fill="#0f172a">category</text><text x="130" y="128" font-size="11" fill="#64748b">VARCHAR(20)</text>
    <text x="12" y="148" font-size="11" fill="#0f172a">date</text><text x="130" y="148" font-size="11" fill="#64748b">DATE</text>
    <text x="12" y="168" font-size="11" fill="#0f172a">created_at</text><text x="130" y="168" font-size="11" fill="#64748b">DATETIME</text>
  </g>

  <!-- Table 5: SiteLimit (FK to User) -->
  <g transform="translate(360, 360)">
    <rect width="270" height="155" rx="8" fill="#ffffff" stroke="#9333ea" stroke-width="1.5" filter="url(#tableShadow)" />
    <path d="M 0 0 L 270 0 L 270 28 L 0 28 Z" fill="#9333ea" />
    <text x="135" y="19" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">core_sitelimit (1-to-Many)</text>
    <text x="12" y="48" font-size="11" font-weight="bold" fill="#0f172a">id</text><text x="140" y="48" font-size="11" fill="#64748b">INTEGER [PK]</text>
    <text x="12" y="68" font-size="11" font-weight="bold" fill="#0f172a">user_id</text><text x="140" y="68" font-size="11" fill="#64748b">INTEGER [FK]</text>
    <text x="12" y="88" font-size="11" fill="#0f172a">domain</text><text x="140" y="88" font-size="11" fill="#64748b">VARCHAR(255)</text>
    <text x="12" y="108" font-size="11" fill="#0f172a">daily_limit_minutes</text><text x="140" y="108" font-size="11" fill="#64748b">INTEGER</text>
    <text x="12" y="128" font-size="11" fill="#0f172a">enabled</text><text x="140" y="128" font-size="11" fill="#64748b">BOOLEAN</text>
    <text x="12" y="148" font-size="11" fill="#0f172a">updated_at</text><text x="140" y="148" font-size="11" fill="#64748b">DATETIME</text>
  </g>

  <!-- Table 6: FocusSession & CategoryOverride (Split box) -->
  <g transform="translate(680, 360)">
    <rect width="260" height="115" rx="8" fill="#ffffff" stroke="#e11d48" stroke-width="1.5" filter="url(#tableShadow)" />
    <path d="M 0 0 L 260 0 L 260 26 L 0 26 Z" fill="#e11d48" />
    <text x="130" y="18" text-anchor="middle" font-size="11" font-weight="bold" fill="#ffffff">core_focussession (1-to-Many)</text>
    <text x="12" y="44" font-size="10" font-weight="bold" fill="#0f172a">id</text><text x="130" y="44" font-size="10" fill="#64748b">INTEGER [PK]</text>
    <text x="12" y="62" font-size="10" font-weight="bold" fill="#0f172a">user_id</text><text x="130" y="62" font-size="10" fill="#64748b">INTEGER [FK]</text>
    <text x="12" y="80" font-size="10" fill="#0f172a">duration_minutes</text><text x="130" y="80" font-size="10" fill="#64748b">INTEGER</text>
    <text x="12" y="98" font-size="10" fill="#0f172a">completed</text><text x="130" y="98" font-size="10" fill="#64748b">BOOLEAN</text>
  </g>

  <g transform="translate(680, 490)">
    <rect width="260" height="115" rx="8" fill="#ffffff" stroke="#0d9488" stroke-width="1.5" filter="url(#tableShadow)" />
    <path d="M 0 0 L 260 0 L 260 26 L 0 26 Z" fill="#0d9488" />
    <text x="130" y="18" text-anchor="middle" font-size="11" font-weight="bold" fill="#ffffff">core_categoryoverride (1-to-Many)</text>
    <text x="12" y="44" font-size="10" font-weight="bold" fill="#0f172a">id</text><text x="130" y="44" font-size="10" fill="#64748b">INTEGER [PK]</text>
    <text x="12" y="62" font-size="10" font-weight="bold" fill="#0f172a">user_id</text><text x="130" y="62" font-size="10" fill="#64748b">INTEGER [FK]</text>
    <text x="12" y="80" font-size="10" fill="#0f172a">domain</text><text x="130" y="80" font-size="10" fill="#64748b">VARCHAR(255)</text>
    <text x="12" y="98" font-size="10" fill="#0f172a">category</text><text x="130" y="98" font-size="10" fill="#64748b">VARCHAR(30)</text>
  </g>

  <!-- Note on removed EmailOTP -->
  <rect x="40" y="555" width="590" height="45" rx="6" fill="#fef2f2" stroke="#fecaca" />
  <text x="50" y="573" font-size="11" font-weight="bold" fill="#991b1b">Note on Database Evolution:</text>
  <text x="50" y="590" font-size="10" fill="#7f1d1d">EmailOTP model was added in migration 0008 and completely dropped in migration 0009 (streamlined direct signup).</text>

  <!-- Connectors -->
  <line x1="290" y1="160" x2="360" y2="160" stroke="#0284c7" stroke-width="2" />
  <line x1="630" y1="160" x2="680" y2="160" stroke="#16a34a" stroke-width="2" />
  <line x1="165" y1="240" x2="165" y2="360" stroke="#d97706" stroke-width="2" />
  <line x1="290" y1="210" x2="360" y2="390" stroke="#9333ea" stroke-width="1.5" stroke-dasharray="4,4" />
</svg>'''

with open('docs/diagrams/database_er_diagram.svg', 'w', encoding='utf-8') as f:
    f.write(svg_database_er)

print('Generated database_er_diagram.svg')

# 4. Workflow 1: Tracking Workflow
svg_wf1 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 320" width="900" height="320" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <marker id="wfArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb" />
    </marker>
  </defs>
  <text x="450" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#0f172a">WORKFLOW 1: Precision Active Tab Dwell Tracking</text>
  <text x="450" y="50" text-anchor="middle" font-size="12" fill="#64748b">1-Second Heartbeat Pipeline resolving Manifest V3 Service Worker Throttling</text>

  <!-- Box 1: User on Tab -->
  <rect x="30" y="80" width="180" height="200" rx="10" fill="#f8fafc" stroke="#94a3b8" />
  <rect x="40" y="90" width="160" height="24" rx="4" fill="#334155" />
  <text x="120" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">Active Web Browser</text>
  <text x="45" y="130" font-size="10" font-weight="bold" fill="#0f172a">Active Tab (e.g. reddit.com)</text>
  <text x="45" y="148" font-size="9" fill="#475569">• document.hidden == false</text>
  <text x="45" y="163" font-size="9" fill="#475569">• document.hasFocus() == true</text>
  <text x="45" y="185" font-size="9" fill="#16a34a">content.js active</text>
  <text x="45" y="200" font-size="9" fill="#475569">Sends 1s tick payload:</text>
  <text x="45" y="215" font-size="8" font-family="monospace" fill="#0369a1">{type: "PAGE_HEARTBEAT_TICK",</text>
  <text x="45" y="228" font-size="8" font-family="monospace" fill="#0369a1"> domain, url, timestamp}</text>

  <!-- Box 2: Background Receiver -->
  <rect x="250" y="80" width="200" height="200" rx="10" fill="#eff6ff" stroke="#93c5fd" />
  <rect x="260" y="90" width="180" height="24" rx="4" fill="#2563eb" />
  <text x="350" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">background.js Service Worker</text>
  <text x="265" y="130" font-size="10" font-weight="bold" fill="#1e3a8a">onMessage Listener</text>
  <text x="265" y="148" font-size="9" fill="#475569">1. Validates sender.tab.active</text>
  <text x="265" y="163" font-size="9" fill="#475569">2. cleanDomain(hostname)</text>
  <text x="265" y="178" font-size="9" fill="#475569">3. Calculates delta seconds (1s)</text>
  <text x="265" y="193" font-size="9" fill="#475569">4. Checks Shorts/Reels block</text>
  <text x="265" y="208" font-size="9" fill="#475569">5. Checks Focus Mode active</text>
  <text x="265" y="223" font-size="9" fill="#475569">6. Evaluates siteLimits vs 80%/100%</text>

  <!-- Box 3: Storage & Response -->
  <rect x="490" y="80" width="180" height="200" rx="10" fill="#fdf4ff" stroke="#f0abfc" />
  <rect x="500" y="90" width="160" height="24" rx="4" fill="#a855f7" />
  <text x="580" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">Local Storage Commit</text>
  <text x="505" y="130" font-size="10" font-weight="bold" fill="#581c87">chrome.storage.local</text>
  <text x="505" y="148" font-size="9" fill="#475569">• siteTimes[domain] += 1</text>
  <text x="505" y="163" font-size="9" fill="#475569">• unsyncedDeltas[domain] += 1</text>
  <text x="505" y="178" font-size="9" fill="#475569">• activeTrackingSession</text>
  <text x="505" y="200" font-size="9" fill="#a855f7">Response to content.js:</text>
  <text x="505" y="215" font-size="8" font-family="monospace" fill="#701a75">{blocked: false, elapsed,</text>
  <text x="505" y="228" font-size="8" font-family="monospace" fill="#701a75"> limit, nudgeAt}</text>

  <!-- Box 4: Blur / Inactive State -->
  <rect x="710" y="80" width="160" height="200" rx="10" fill="#fef2f2" stroke="#fca5a5" />
  <rect x="720" y="90" width="140" height="24" rx="4" fill="#dc2626" />
  <text x="790" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">Tab Blur / Inactive</text>
  <text x="725" y="130" font-size="10" font-weight="bold" fill="#991b1b">visibilitychange / blur</text>
  <text x="725" y="148" font-size="9" fill="#475569">• clearInterval(heartbeat)</text>
  <text x="725" y="163" font-size="9" fill="#475569">• Sends PAGE_HEARTBEAT_PAUSE</text>
  <text x="725" y="178" font-size="9" fill="#475569">• background commits delta</text>
  <text x="725" y="193" font-size="9" fill="#475569">• No ghost seconds added!</text>

  <!-- Connectors -->
  <line x1="210" y1="180" x2="250" y2="180" stroke="#2563eb" stroke-width="2" marker-end="url(#wfArrow)" />
  <line x1="450" y1="180" x2="490" y2="180" stroke="#2563eb" stroke-width="2" marker-end="url(#wfArrow)" />
  <line x1="670" y1="180" x2="710" y2="180" stroke="#2563eb" stroke-width="2" marker-end="url(#wfArrow)" />
</svg>'''

with open('docs/diagrams/workflow_1_tracking.svg', 'w', encoding='utf-8') as f:
    f.write(svg_wf1)

print('Generated workflow_1_tracking.svg')

# 5. Workflow 2: Escalation & Enforcement Workflow
svg_wf2 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 320" width="900" height="320" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <marker id="escArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#ea580c" />
    </marker>
  </defs>
  <text x="450" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#0f172a">WORKFLOW 2: 3-Tier Timer Escalation &amp; DNR Enforcement</text>
  <text x="450" y="50" text-anchor="middle" font-size="12" fill="#64748b">Live Second Tracking → 80% Gentle Nudge → 100% Declarative Net Request Block</text>

  <!-- Step 1: Active Dwell -->
  <rect x="30" y="80" width="180" height="200" rx="10" fill="#f8fafc" stroke="#cbd5e1" />
  <rect x="40" y="90" width="160" height="24" rx="4" fill="#0284c7" />
  <text x="120" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">1. Browsing Tracked Site</text>
  <text x="45" y="130" font-size="10" fill="#0f172a">Example: instagram.com</text>
  <text x="45" y="145" font-size="9" fill="#64748b">Custom Limit: 2 minutes (120s)</text>
  <text x="45" y="165" font-size="9" fill="#475569">0s .. 95s: Normal browsing</text>
  <text x="45" y="180" font-size="9" fill="#475569">Heartbeat ticks every second</text>
  <text x="45" y="195" font-size="9" fill="#475569">Popup timer counts live</text>

  <!-- Step 2: 80% Nudge -->
  <rect x="250" y="80" width="190" height="200" rx="10" fill="#fffbeb" stroke="#fde68a" />
  <rect x="260" y="90" width="170" height="24" rx="4" fill="#d97706" />
  <text x="345" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">2. 80% Nudge (96s)</text>
  <text x="265" y="130" font-size="10" font-weight="bold" fill="#b45309">Gentle Desktop Alert</text>
  <text x="265" y="148" font-size="9" fill="#475569">• currentSeconds >= 96s</text>
  <text x="265" y="163" font-size="9" fill="#475569">• state.nudged == false</text>
  <text x="265" y="178" font-size="9" fill="#475569">• state.nudged = true</text>
  <text x="265" y="193" font-size="9" fill="#475569">• sendNudgeNotification()</text>
  <text x="265" y="208" font-size="9" fill="#b45309">"Almost at your daily limit!"</text>
  <text x="265" y="223" font-size="9" fill="#16a34a">Encourages mindful closure</text>

  <!-- Step 3: 100% Block Triggered -->
  <rect x="480" y="80" width="190" height="200" rx="10" fill="#fef2f2" stroke="#fecaca" />
  <rect x="490" y="90" width="170" height="24" rx="4" fill="#dc2626" />
  <text x="575" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">3. 100% Limit Reached (120s)</text>
  <text x="495" y="130" font-size="10" font-weight="bold" fill="#991b1b">Enforcement Activation</text>
  <text x="495" y="148" font-size="9" fill="#475569">• currentSeconds >= 120s</text>
  <text x="495" y="163" font-size="9" fill="#475569">• state.blocked = true</text>
  <text x="495" y="178" font-size="9" fill="#475569">• sendLimitReachedNotification()</text>
  <text x="495" y="193" font-size="9" fill="#475569">• blockDomainViaDNR(domain)</text>
  <text x="495" y="208" font-size="9" fill="#dc2626">DNR Rule ID: 1000..1999</text>
  <text x="495" y="223" font-size="9" fill="#475569">Action: block all HTTP traffic</text>

  <!-- Step 4: Redirection & Lock -->
  <rect x="710" y="80" width="160" height="200" rx="10" fill="#f3e8ff" stroke="#d8b4fe" />
  <rect x="720" y="90" width="140" height="24" rx="4" fill="#9333ea" />
  <text x="790" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">4. Redirection &amp; Lockout</text>
  <text x="725" y="130" font-size="10" font-weight="bold" fill="#581c87">blocked.html</text>
  <text x="725" y="148" font-size="9" fill="#475569">• content.js receives {blocked:true}</text>
  <text x="725" y="163" font-size="9" fill="#475569">• Redirects to blocked.html</text>
  <text x="725" y="178" font-size="9" fill="#475569">• Browser network engine blocks future attempts</text>
  <text x="725" y="198" font-size="9" fill="#16a34a">Midnight Reset Alarm:</text>
  <text x="725" y="213" font-size="9" fill="#475569">Clears rule at 00:00:00</text>

  <!-- Connectors -->
  <line x1="210" y1="180" x2="250" y2="180" stroke="#ea580c" stroke-width="2" marker-end="url(#escArrow)" />
  <line x1="440" y1="180" x2="480" y2="180" stroke="#ea580c" stroke-width="2" marker-end="url(#escArrow)" />
  <line x1="670" y1="180" x2="710" y2="180" stroke="#ea580c" stroke-width="2" marker-end="url(#escArrow)" />
</svg>'''

with open('docs/diagrams/workflow_2_escalation_block.svg', 'w', encoding='utf-8') as f:
    f.write(svg_wf2)

print('Generated workflow_2_escalation_block.svg')

# 6. Workflow 3: Scheduled Focus Workflow
svg_wf3 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 300" width="900" height="300" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <marker id="schedArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a" />
    </marker>
  </defs>
  <text x="450" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#0f172a">WORKFLOW 3: Scheduled Focus Mode Lifecycle</text>
  <text x="450" y="50" text-anchor="middle" font-size="12" fill="#64748b">Time Pickers → Dual Alarms (Start &amp; End) → DNR Rule Toggling → Backend Sync</text>

  <!-- Step 1: User Sets Schedule -->
  <rect x="30" y="75" width="190" height="200" rx="10" fill="#f8fafc" stroke="#cbd5e1" />
  <rect x="40" y="85" width="170" height="24" rx="4" fill="#3b82f6" />
  <text x="125" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">1. Popup Time Pickers</text>
  <text x="45" y="125" font-size="10" font-weight="bold" fill="#0f172a">Inline Schedule Row</text>
  <text x="45" y="142" font-size="9" fill="#475569">• Start: 20:00 (8:00 PM)</text>
  <text x="45" y="157" font-size="9" fill="#475569">• End: 22:30 (10:30 PM)</text>
  <text x="45" y="172" font-size="9" fill="#16a34a">Midnight cross support (e.g. 23:00 to 01:00)</text>
  <text x="45" y="190" font-size="9" fill="#475569">User taps "Save Schedule"</text>
  <text x="45" y="205" font-size="9" fill="#2563eb">→ UPDATE_SCHEDULE message</text>

  <!-- Step 2: Alarm Generation -->
  <rect x="260" y="75" width="190" height="200" rx="10" fill="#eff6ff" stroke="#bfdbfe" />
  <rect x="270" y="85" width="170" height="24" rx="4" fill="#0284c7" />
  <text x="355" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">2. Chrome Alarms Created</text>
  <text x="275" y="125" font-size="10" font-weight="bold" fill="#0369a1">updateScheduleAlarms()</text>
  <text x="275" y="142" font-size="9" fill="#475569">• driftless_schedule_start</text>
  <text x="275" y="157" font-size="9" fill="#475569">• driftless_schedule_end</text>
  <text x="275" y="175" font-size="9" fill="#475569">Immediate State Check:</text>
  <text x="275" y="190" font-size="9" fill="#475569">isWithinScheduleWindow()</text>
  <text x="275" y="205" font-size="9" fill="#475569">If inside now → enable Focus</text>

  <!-- Step 3: Execution at Schedule Start -->
  <rect x="490" y="75" width="190" height="200" rx="10" fill="#f0fdf4" stroke="#bbf7d0" />
  <rect x="500" y="85" width="170" height="24" rx="4" fill="#16a34a" />
  <text x="585" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">3. Start Time Reached</text>
  <text x="505" y="125" font-size="10" font-weight="bold" fill="#14532d">Alarm Fires (20:00)</text>
  <text x="505" y="142" font-size="9" fill="#475569">• enableFocusMode()</text>
  <text x="505" y="157" font-size="9" fill="#475569">• Injects DNR rules 100..899</text>
  <text x="505" y="172" font-size="9" fill="#475569">• Blocks distracting site list</text>
  <text x="505" y="187" font-size="9" fill="#475569">• Shows system notification</text>
  <text x="505" y="202" font-size="9" fill="#16a34a">• Syncs focus_mode_active=True</text>

  <!-- Step 4: Schedule End & Restoration -->
  <rect x="720" y="75" width="150" height="200" rx="10" fill="#faf5ff" stroke="#e9d5ff" />
  <rect x="730" y="85" width="130" height="24" rx="4" fill="#9333ea" />
  <text x="795" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">4. End Time (22:30)</text>
  <text x="735" y="125" font-size="10" font-weight="bold" fill="#581c87">Alarm Fires</text>
  <text x="735" y="142" font-size="9" fill="#475569">• disableFocusMode()</text>
  <text x="735" y="157" font-size="9" fill="#475569">• Removes DNR rules</text>
  <text x="735" y="172" font-size="9" fill="#475569">• Unblocks sites</text>
  <text x="735" y="187" font-size="9" fill="#475569">• Re-arms next day alarm</text>

  <!-- Connectors -->
  <line x1="220" y1="175" x2="260" y2="175" stroke="#16a34a" stroke-width="2" marker-end="url(#schedArrow)" />
  <line x1="450" y1="175" x2="490" y2="175" stroke="#16a34a" stroke-width="2" marker-end="url(#schedArrow)" />
  <line x1="680" y1="175" x2="720" y2="175" stroke="#16a34a" stroke-width="2" marker-end="url(#schedArrow)" />
</svg>'''

with open('docs/diagrams/workflow_3_scheduled_focus.svg', 'w', encoding='utf-8') as f:
    f.write(svg_wf3)

print('Generated workflow_3_scheduled_focus.svg')

# 7. Workflow 4: Pomodoro Workflow
svg_wf4 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 300" width="900" height="300" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <marker id="pomoArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#e11d48" />
    </marker>
  </defs>
  <text x="450" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#0f172a">WORKFLOW 4: Pomodoro Focus Sprint State Machine</text>
  <text x="450" y="50" text-anchor="middle" font-size="12" fill="#64748b">25-Minute Work Sprint → Audio &amp; Notification Alert → 5-Minute Break Cycle</text>

  <!-- Box 1: Start 25m Focus -->
  <rect x="30" y="75" width="190" height="200" rx="10" fill="#fff1f2" stroke="#fecdd3" />
  <rect x="40" y="85" width="170" height="24" rx="4" fill="#e11d48" />
  <text x="125" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">1. Start 25m Sprint</text>
  <text x="45" y="125" font-size="10" font-weight="bold" fill="#9f1239">Popup Trigger</text>
  <text x="45" y="142" font-size="9" fill="#475569">• User clicks "Start Pomodoro"</text>
  <text x="45" y="157" font-size="9" fill="#475569">• START_POMODORO message</text>
  <text x="45" y="172" font-size="9" fill="#475569">• mode = 'work' (25 mins)</text>
  <text x="45" y="187" font-size="9" fill="#475569">• enableFocusMode()</text>
  <text x="45" y="202" font-size="9" fill="#e11d48">• DNR rules 100..899 active</text>

  <!-- Box 2: 25m Alarm Fires -->
  <rect x="260" y="75" width="190" height="200" rx="10" fill="#fdf4ff" stroke="#f5d0fe" />
  <rect x="270" y="85" width="170" height="24" rx="4" fill="#a855f7" />
  <text x="355" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">2. 25m Sprint Complete</text>
  <text x="275" y="125" font-size="10" font-weight="bold" fill="#701a75">Alarm: driftless_pomodoro</text>
  <text x="275" y="142" font-size="9" fill="#475569">• Alarm fires at T+25m</text>
  <text x="275" y="157" font-size="9" fill="#475569">• Notification: "Focus Complete!"</text>
  <text x="275" y="172" font-size="9" fill="#475569">• disableFocusMode()</text>
  <text x="275" y="187" font-size="9" fill="#475569">• POST /api/sessions/ recorded</text>
  <text x="275" y="202" font-size="9" fill="#16a34a">• +50 XP awarded</text>

  <!-- Box 3: 5m Break Mode -->
  <rect x="490" y="75" width="190" height="200" rx="10" fill="#f0fdf4" stroke="#bbf7d0" />
  <rect x="500" y="85" width="170" height="24" rx="4" fill="#16a34a" />
  <text x="585" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">3. 5-Minute Break Mode</text>
  <text x="505" y="125" font-size="10" font-weight="bold" fill="#14532d">Rest Phase</text>
  <text x="505" y="142" font-size="9" fill="#475569">• mode = 'break'</text>
  <text x="505" y="157" font-size="9" fill="#475569">• Alarm set for 5 minutes</text>
  <text x="505" y="172" font-size="9" fill="#475569">• Distracting sites unblocked</text>
  <text x="505" y="187" font-size="9" fill="#475569">• Popup displays green break timer</text>

  <!-- Box 4: Break End & Loop -->
  <rect x="720" y="75" width="150" height="200" rx="10" fill="#f8fafc" stroke="#cbd5e1" />
  <rect x="730" y="85" width="130" height="24" rx="4" fill="#475569" />
  <text x="795" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">4. Break Finished</text>
  <text x="735" y="125" font-size="10" font-weight="bold" fill="#0f172a">Cycle Reset</text>
  <text x="735" y="142" font-size="9" fill="#475569">• Notification: "Break over!"</text>
  <text x="735" y="157" font-size="9" fill="#475569">• State switches to idle</text>
  <text x="735" y="172" font-size="9" fill="#475569">• Ready for next sprint</text>

  <!-- Connectors -->
  <line x1="220" y1="175" x2="260" y2="175" stroke="#e11d48" stroke-width="2" marker-end="url(#pomoArrow)" />
  <line x1="450" y1="175" x2="490" y2="175" stroke="#e11d48" stroke-width="2" marker-end="url(#pomoArrow)" />
  <line x1="680" y1="175" x2="720" y2="175" stroke="#e11d48" stroke-width="2" marker-end="url(#pomoArrow)" />
</svg>'''

with open('docs/diagrams/workflow_4_pomodoro.svg', 'w', encoding='utf-8') as f:
    f.write(svg_wf4)

print('Generated workflow_4_pomodoro.svg')

# 8. Workflow 5: Authentication & Onboarding Workflow
svg_wf5 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 320" width="900" height="320" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <marker id="authArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb" />
    </marker>
  </defs>
  <text x="450" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#0f172a">WORKFLOW 5: Streamlined Authentication &amp; Persona Onboarding</text>
  <text x="450" y="50" text-anchor="middle" font-size="12" fill="#64748b">Direct Registration + Google Sign-In + Extension Welcome Screen</text>

  <!-- Box 1: UI Input -->
  <rect x="30" y="80" width="180" height="210" rx="10" fill="#f8fafc" stroke="#cbd5e1" />
  <rect x="40" y="90" width="160" height="24" rx="4" fill="#2563eb" />
  <text x="120" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">1. User Signup / Login</text>
  <text x="45" y="130" font-size="10" font-weight="bold" fill="#0f172a">auth.html Interface</text>
  <text x="45" y="148" font-size="9" fill="#475569">• Option A: Continue with Google</text>
  <text x="45" y="163" font-size="9" fill="#475569">• Option B: Username &amp; Email</text>
  <text x="45" y="180" font-size="9" fill="#2563eb">Frontend Validation:</text>
  <text x="45" y="195" font-size="9" fill="#475569">Strict regex check for valid domain</text>
  <text x="45" y="210" font-size="9" fill="#475569">(Blocks invalid strings before submit)</text>

  <!-- Box 2: Backend Processing -->
  <rect x="250" y="80" width="190" height="210" rx="10" fill="#eff6ff" stroke="#bfdbfe" />
  <rect x="260" y="90" width="170" height="24" rx="4" fill="#0284c7" />
  <text x="345" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">2. Backend Verification</text>
  <text x="265" y="130" font-size="10" font-weight="bold" fill="#0369a1">views.py: register_view</text>
  <text x="265" y="148" font-size="9" fill="#475569">1. Django EmailValidator check</text>
  <text x="265" y="163" font-size="9" fill="#475569">2. Creates User record</text>
  <text x="265" y="178" font-size="9" fill="#475569">3. Sets is_verified = True</text>
  <text x="265" y="193" font-size="9" fill="#475569">4. Seeds Level 5 demo gamification</text>
  <text x="265" y="208" font-size="9" fill="#475569">5. Generates DRF Auth Token</text>
  <text x="265" y="223" font-size="9" fill="#16a34a">6. Immediate 201 redirect to dashboard</text>

  <!-- Box 3: Dashboard Access -->
  <rect x="480" y="80" width="190" height="210" rx="10" fill="#f0fdf4" stroke="#bbf7d0" />
  <rect x="490" y="90" width="170" height="24" rx="4" fill="#16a34a" />
  <text x="575" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">3. Web Dashboard Ready</text>
  <text x="495" y="130" font-size="10" font-weight="bold" fill="#14532d">dashboard.html</text>
  <text x="495" y="148" font-size="9" fill="#475569">• Full 3D Neumorphic dashboard</text>
  <text x="495" y="163" font-size="9" fill="#475569">• Copies API Token to extension</text>
  <text x="495" y="178" font-size="9" fill="#475569">• Displays 3D badges in sidebar</text>
  <text x="495" y="193" font-size="9" fill="#475569">• Green Grove forest initialized</text>

  <!-- Box 4: Extension Onboarding -->
  <rect x="710" y="80" width="160" height="210" rx="10" fill="#fdf4ff" stroke="#f5d0fe" />
  <rect x="720" y="90" width="140" height="24" rx="4" fill="#a855f7" />
  <text x="790" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">4. Extension Persona</text>
  <text x="725" y="130" font-size="10" font-weight="bold" fill="#701a75">Welcome Screen</text>
  <text x="725" y="148" font-size="9" fill="#475569">• Step 1: "Welcome to Driftless"</text>
  <text x="725" y="163" font-size="9" fill="#475569">• Step 2: "Who are you?"</text>
  <text x="725" y="178" font-size="9" fill="#475569">• Selects Student/Professional</text>
  <text x="725" y="193" font-size="9" fill="#475569">• Seeds recommended sites</text>
  <text x="725" y="208" font-size="9" fill="#16a34a">• Never shows again</text>

  <!-- Connectors -->
  <line x1="210" y1="185" x2="250" y2="185" stroke="#2563eb" stroke-width="2" marker-end="url(#authArrow)" />
  <line x1="440" y1="185" x2="480" y2="185" stroke="#2563eb" stroke-width="2" marker-end="url(#authArrow)" />
  <line x1="670" y1="185" x2="710" y2="185" stroke="#2563eb" stroke-width="2" marker-end="url(#authArrow)" />
</svg>'''

with open('docs/diagrams/workflow_5_auth_onboarding.svg', 'w', encoding='utf-8') as f:
    f.write(svg_wf5)

print('Generated workflow_5_auth_onboarding.svg')

# 9. Workflow 6: Periodic Sync Workflow
svg_wf6 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 280" width="900" height="280" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <marker id="syncArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669" />
    </marker>
  </defs>
  <text x="450" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#0f172a">WORKFLOW 6: Periodic Cloud Synchronization</text>
  <text x="450" y="50" text-anchor="middle" font-size="12" fill="#64748b">15-Minute Alarm &amp; Manual Sync Ingesting Usage Deltas and Pulling Settings</text>

  <!-- Box 1: Sync Alarm -->
  <rect x="30" y="75" width="190" height="180" rx="10" fill="#f8fafc" stroke="#cbd5e1" />
  <rect x="40" y="85" width="170" height="24" rx="4" fill="#059669" />
  <text x="125" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">1. Sync Trigger</text>
  <text x="45" y="125" font-size="10" font-weight="bold" fill="#065f46">Alarm or User Action</text>
  <text x="45" y="145" font-size="9" fill="#475569">• driftless_periodic_sync (15m)</text>
  <text x="45" y="160" font-size="9" fill="#475569">• OR User clicks "Sync Now"</text>
  <text x="45" y="175" font-size="9" fill="#475569">• Reads unsyncedDeltas</text>
  <text x="45" y="190" font-size="9" fill="#059669">• Verifies API Token present</text>

  <!-- Box 2: Push Deltas -->
  <rect x="260" y="75" width="190" height="180" rx="10" fill="#eff6ff" stroke="#bfdbfe" />
  <rect x="270" y="85" width="170" height="24" rx="4" fill="#2563eb" />
  <text x="355" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">2. POST /api/usage/</text>
  <text x="275" y="125" font-size="10" font-weight="bold" fill="#1e40af">Batch Payload Delivery</text>
  <text x="275" y="145" font-size="9" fill="#475569">• Sends array of {website_url, seconds}</text>
  <text x="275" y="160" font-size="9" fill="#475569">• DRF ingests into UsageLog</text>
  <text x="275" y="175" font-size="9" fill="#475569">• Resets local unsyncedDeltas</text>
  <text x="275" y="190" font-size="9" fill="#16a34a">• Rate-limited at 120/min</text>

  <!-- Box 3: Pull Settings -->
  <rect x="490" y="75" width="190" height="180" rx="10" fill="#fdf4ff" stroke="#f5d0fe" />
  <rect x="500" y="85" width="170" height="24" rx="4" fill="#a855f7" />
  <text x="585" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">3. GET /api/settings/</text>
  <text x="505" y="125" font-size="10" font-weight="bold" fill="#701a75">Settings Pull</text>
  <text x="505" y="145" font-size="9" fill="#475569">• Fetches schedule_start/end</text>
  <text x="505" y="160" font-size="9" fill="#475569">• Fetches blocked_sites list</text>
  <text x="505" y="175" font-size="9" fill="#475569">• Fetches persona &amp; limits</text>
  <text x="505" y="190" font-size="9" fill="#a855f7">• Updates chrome.storage</text>

  <!-- Box 4: Alarms & DNR Update -->
  <rect x="720" y="75" width="150" height="180" rx="10" fill="#f0fdf4" stroke="#bbf7d0" />
  <rect x="730" y="85" width="130" height="24" rx="4" fill="#16a34a" />
  <text x="795" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">4. Reconfiguration</text>
  <text x="735" y="125" font-size="10" font-weight="bold" fill="#14532d">Active State Sync</text>
  <text x="735" y="145" font-size="9" fill="#475569">• Alarms updated</text>
  <text x="735" y="160" font-size="9" fill="#475569">• DNR rules synced</text>
  <text x="735" y="175" font-size="9" fill="#475569">• Popup UI reflects state</text>

  <!-- Connectors -->
  <line x1="220" y1="165" x2="260" y2="165" stroke="#059669" stroke-width="2" marker-end="url(#syncArrow)" />
  <line x1="450" y1="165" x2="490" y2="165" stroke="#059669" stroke-width="2" marker-end="url(#syncArrow)" />
  <line x1="680" y1="165" x2="720" y2="165" stroke="#059669" stroke-width="2" marker-end="url(#syncArrow)" />
</svg>'''

with open('docs/diagrams/workflow_6_sync.svg', 'w', encoding='utf-8') as f:
    f.write(svg_wf6)

print('Generated workflow_6_sync.svg')

# 10. Workflow 7: Green Grove Calculation Workflow
svg_wf7 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 280" width="900" height="280" style="background:#ffffff; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <marker id="groveArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a" />
    </marker>
  </defs>
  <text x="450" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#0f172a">WORKFLOW 7: 30-Day Green Grove Tree Status Evaluation</text>
  <text x="450" y="50" text-anchor="middle" font-size="12" fill="#64748b">Daily Dwell Aggregation vs Per-Site &amp; Global Thresholds (core/views.py:552-649)</text>

  <!-- Day Evaluation Node -->
  <rect x="30" y="75" width="220" height="180" rx="10" fill="#f8fafc" stroke="#cbd5e1" />
  <rect x="40" y="85" width="200" height="24" rx="4" fill="#334155" />
  <text x="140" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">1. Day Log Aggregation</text>
  <text x="45" y="125" font-size="10" font-weight="bold" fill="#0f172a">Loop 30 Days (T-29 to Today)</text>
  <text x="45" y="145" font-size="9" fill="#475569">Fetch logs for date d_str</text>
  <text x="45" y="160" font-size="9" fill="#475569">Case A: day_logs is empty</text>
  <text x="45" y="175" font-size="9" fill="#64748b">→ status = 'empty' (soil spot)</text>
  <text x="45" y="195" font-size="9" fill="#475569">Case B: day_logs has dwell</text>
  <text x="45" y="210" font-size="9" fill="#0284c7">→ Evaluate limits check</text>

  <!-- Check Per-Site & Global Limits -->
  <rect x="290" y="75" width="230" height="180" rx="10" fill="#eff6ff" stroke="#bfdbfe" />
  <rect x="300" y="85" width="210" height="24" rx="4" fill="#0284c7" />
  <text x="405" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">2. Strict Limit Evaluation</text>
  <text x="305" y="125" font-size="10" font-weight="bold" fill="#0369a1">For each log in day:</text>
  <text x="305" y="145" font-size="9" fill="#475569">1. Custom SiteLimit exists?</text>
  <text x="305" y="160" font-size="9" fill="#dc2626">If time_spent > siteLimit → EXCEEDED</text>
  <text x="305" y="180" font-size="9" fill="#475569">2. Category == 'Distracting sites'?</text>
  <text x="305" y="195" font-size="9" fill="#dc2626">If time_spent > global_limit → EXCEEDED</text>
  <text x="305" y="215" font-size="9" fill="#16a34a">3. Otherwise → Within Limits</text>

  <!-- Final Tree Status Output -->
  <rect x="560" y="75" width="310" height="180" rx="10" fill="#f0fdf4" stroke="#bbf7d0" />
  <rect x="570" y="85" width="290" height="24" rx="4" fill="#16a34a" />
  <text x="715" y="101" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">3. Grove Tree Outcome</text>
  
  <rect x="575" y="120" width="135" height="60" rx="6" fill="#ffffff" stroke="#16a34a" />
  <text x="642" y="140" text-anchor="middle" font-size="10" font-weight="bold" fill="#14532d">🌲 status = 'grown'</text>
  <text x="642" y="155" text-anchor="middle" font-size="9" fill="#475569">No limit exceeded</text>
  <text x="642" y="170" text-anchor="middle" font-size="9" fill="#16a34a">+1 Total Trees Grown</text>

  <rect x="720" y="120" width="135" height="60" rx="6" fill="#ffffff" stroke="#e11d48" />
  <text x="787" y="140" text-anchor="middle" font-size="10" font-weight="bold" fill="#9f1239">🍂 status = 'withered'</text>
  <text x="787" y="155" text-anchor="middle" font-size="9" fill="#475569">Limit was breached</text>
  <text x="787" y="170" text-anchor="middle" font-size="9" fill="#dc2626">Breaks user streak</text>

  <text x="715" y="215" text-anchor="middle" font-size="10" font-weight="bold" fill="#0f172a">Rendered as 30 tactile SVG icons on Dashboard</text>

  <!-- Connectors -->
  <line x1="250" y1="165" x2="290" y2="165" stroke="#16a34a" stroke-width="2" marker-end="url(#groveArrow)" />
  <line x1="520" y1="165" x2="560" y2="165" stroke="#16a34a" stroke-width="2" marker-end="url(#groveArrow)" />
</svg>'''

with open('docs/diagrams/workflow_7_green_grove.svg', 'w', encoding='utf-8') as f:
    f.write(svg_wf7)

print('Generated workflow_7_green_grove.svg')
print('ALL DIAGRAMS GENERATED SUCCESSFULLY!')
