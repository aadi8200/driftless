// ─────────────────────────────────────────────────────────────────────────────
// DRIFTLESS BACKGROUND SERVICE WORKER (Manifest V3)
// ─────────────────────────────────────────────────────────────────────────────

const ALARM_MIDNIGHT_RESET     = 'driftless_midnight_reset';
const ALARM_PERIODIC_SYNC      = 'driftless_periodic_sync';
const ALARM_TICK               = 'driftless_tick';
const ALARM_SCHEDULE_START     = 'driftless_schedule_start';
const ALARM_SCHEDULE_END       = 'driftless_schedule_end';

const FOCUS_RULE_BASE_ID       = 100;    // Dynamic rules 100..899 for Focus Mode
const LIMIT_BLOCK_RULE_BASE_ID = 1000;   // Dynamic rules 1000..9999 for 100% limit reached
const DEFAULT_SERVER_URL       = 'http://127.0.0.1:8000';

const PERSONA_DEFAULTS = {
  Student: {
    distracting: ['instagram.com', 'facebook.com', 'reddit.com', 'youtube.com'],
    productive: ['github.com', 'stackoverflow.com', 'docs.google.com', 'geeksforgeeks.org'],
    scheduleStart: '20:00',
    scheduleEnd: '22:30'
  },
  Professional: {
    distracting: ['instagram.com', 'facebook.com', 'youtube.com', 'x.com'],
    productive: ['github.com', 'docs.google.com', 'notion.so', 'stackoverflow.com'],
    scheduleStart: '09:00',
    scheduleEnd: '12:00'
  },
  Influencer: {
    distracting: ['facebook.com', 'reddit.com', 'netflix.com', 'x.com'],
    productive: ['canva.com', 'docs.google.com', 'drive.google.com', 'notion.so'],
    scheduleStart: '14:00',
    scheduleEnd: '17:00'
  },
  Creator: {
    distracting: ['facebook.com', 'reddit.com', 'netflix.com', 'x.com'],
    productive: ['canva.com', 'figma.com', 'behance.net', 'docs.google.com'],
    scheduleStart: '10:00',
    scheduleEnd: '13:00'
  },
  Other: {
    distracting: ['instagram.com', 'youtube.com', 'facebook.com', 'reddit.com'],
    productive: ['github.com', 'docs.google.com', 'stackoverflow.com', 'coursera.org'],
    scheduleStart: '19:00',
    scheduleEnd: '21:00'
  }
};

function getPersonaKey(raw) {
  if (!raw) return 'Student';
  const norm = raw.trim().toLowerCase();
  if (norm.startsWith('stud')) return 'Student';
  if (norm.startsWith('prof')) return 'Professional';
  if (norm.startsWith('influ')) return 'Influencer';
  if (norm.startsWith('creat')) return 'Creator';
  return 'Other';
}

let currentTabDomain    = null;
let lastCommitTimestamp = Date.now();
let isWindowFocused     = true;
let isUserActive        = true;
let isCommitting        = false;

console.log('Driftless Background Service Worker started.');

// ── Helpers ──────────────────────────────────────────────────────────────────

function cleanDomain(url) {
  if (!url || typeof url !== 'string') return null;
  let str = url.trim().toLowerCase();
  if (!str) return null;
  if (str.startsWith('chrome:') || str.startsWith('about:') || str.startsWith('edge:') || str.startsWith('chrome-extension:')) {
    return null;
  }
  if (!/^https?:\/\//i.test(str)) {
    str = 'https://' + str;
  }
  try {
    const u = new URL(str);
    if (!['http:', 'https:'].includes(u.protocol)) return null;
    let host = u.hostname.toLowerCase();
    if (host.startsWith('www.')) host = host.slice(4);
    return host || null;
  } catch (e) {
    return null;
  }
}

async function getActiveTabSafe() {
  try {
    let [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true }).catch(() => []);
    if (!tab) {
      [tab] = await chrome.tabs.query({ active: true, currentWindow: true }).catch(() => []);
    }
    return tab || null;
  } catch (e) {
    return null;
  }
}

async function getServerUrl() {
  const { serverUrl } = await chrome.storage.local.get(['serverUrl']);
  return (serverUrl && serverUrl.trim()) ? serverUrl.trim().replace(/\/+$/, '') : DEFAULT_SERVER_URL;
}

function buildBlockRule(id, domain) {
  return {
    id,
    priority: 1,
    action: { type: 'block' },
    condition: {
      urlFilter: `||${domain}`,
      resourceTypes: [
        'main_frame', 'sub_frame', 'xmlhttprequest',
        'script', 'image', 'stylesheet', 'font', 'media', 'websocket', 'other'
      ]
    }
  };
}

// ── Time Accumulation ────────────────────────────────────────────────────────
// Driven by active tab events, setInterval when active, and chrome.alarms when waking up.

async function commitActiveTime() {
  if (isCommitting) return;
  isCommitting = true;
  try {
    const now = Date.now();
    const data = await chrome.storage.local.get([
      'activeTrackingSession',
      'siteTimes',
      'unsyncedDeltas'
    ]);

    const session = data.activeTrackingSession || {};
    const siteTimes = data.siteTimes || {};
    const unsyncedDeltas = data.unsyncedDeltas || {};

    const domain = currentTabDomain || session.domain || null;
    const lastTime = session.lastCommitTimestamp || lastCommitTimestamp || now;
    const focused = isWindowFocused && (session.isWindowFocused !== false);
    const active = isUserActive && (session.isUserActive !== false);

    if (!domain || !focused || !active) {
      lastCommitTimestamp = now;
      await chrome.storage.local.set({
        activeTrackingSession: {
          domain: currentTabDomain,
          lastCommitTimestamp: now,
          isWindowFocused,
          isUserActive
        }
      });
      return;
    }

    const elapsedSeconds = Math.floor((now - lastTime) / 1000);
    if (elapsedSeconds <= 0) return;

    // Cap elapsed time to 300s (5m) to avoid runaway accumulation across system suspends
    let effectiveElapsed = Math.min(elapsedSeconds, 300);
    try {
      const idleState = await chrome.idle.queryState(60);
      if (idleState !== 'active') {
        isUserActive = false;
        effectiveElapsed = Math.min(effectiveElapsed, 60);
      }
    } catch (e) {}

    lastCommitTimestamp = now;

    siteTimes[domain] = (siteTimes[domain] || 0) + effectiveElapsed;
    unsyncedDeltas[domain] = (unsyncedDeltas[domain] || 0) + effectiveElapsed;

    await chrome.storage.local.set({
      siteTimes,
      unsyncedDeltas,
      activeTrackingSession: {
        domain,
        lastCommitTimestamp: now,
        isWindowFocused,
        isUserActive
      }
    });

    await evaluateSiteLimits(domain, siteTimes[domain]);
  } catch (err) {
    console.error('Error committing active time:', err);
  } finally {
    isCommitting = false;
  }
}

// ── Escalation & Limit Enforcement for Distracting Sites ─────────────────────

async function evaluateSiteLimits(domain, totalSeconds) {
  const {
    distractingSites = [],
    blockedSites = [],
    siteLimits = {},
    userTimeLimitMinutes = 60,
    escalationState = {} // { [domain]: { nudged: bool, blocked: bool } }
  } = await chrome.storage.local.get([
    'distractingSites', 'blockedSites', 'siteLimits', 'userTimeLimitMinutes', 'escalationState'
  ]);

  // Combined distracting list
  const allDistracting = Array.from(new Set([...distractingSites, ...blockedSites].map(cleanDomain).filter(Boolean)));
  if (!allDistracting.includes(domain)) {
    // Only distracting sites have limits or blocks. Productive sites have NO timers/blocks.
    return;
  }

  // Determine effective limit for this domain
  let limitMins = userTimeLimitMinutes || 60;
  const customLimit = siteLimits[domain];
  if (customLimit && typeof customLimit.daily_limit_minutes === 'number' && customLimit.daily_limit_minutes > 0) {
    limitMins = customLimit.daily_limit_minutes;
  }
  if (limitMins < 1) limitMins = 1;

  const limitSeconds = limitMins * 60;
  const nudgeSeconds = Math.floor(limitSeconds * 0.8);
  const state = escalationState[domain] || { nudged: false, blocked: false };

  // 1. At 80% of limit: send ONE Chrome notification as a nudge
  if (totalSeconds >= nudgeSeconds && !state.nudged) {
    state.nudged = true;
    escalationState[domain] = state;
    await chrome.storage.local.set({ escalationState });
    sendNudgeNotification(domain);
  }

  // 2. At 100%: send ONE Chrome notification AND block that site with declarativeNetRequest
  if (totalSeconds >= limitSeconds && !state.blocked) {
    state.blocked = true;
    escalationState[domain] = state;
    await chrome.storage.local.set({ escalationState });
    sendLimitReachedNotification(domain);
    await blockDomainViaDNR(domain);
  }
}

function sendNudgeNotification(domain) {
  chrome.notifications.create(`nudge-${domain}-${Date.now()}`, {
    type:     'basic',
    iconUrl:  'icons/icon-128.png',
    title:    'Driftless — Focus Alert',
    message:  `You've used 80% of your time on ${domain}. Time to get back to your work.`,
    priority: 1
  });
}

function sendLimitReachedNotification(domain) {
  chrome.notifications.create(`limit-${domain}-${Date.now()}`, {
    type:     'basic',
    iconUrl:  'icons/icon-128.png',
    title:    'Driftless — Focus Alert',
    message:  `Time's up for ${domain}`,
    priority: 2
  });
}

async function blockDomainViaDNR(domain) {
  try {
    const existing = await chrome.declarativeNetRequest.getDynamicRules();
    const existingRule = existing.find(r => r.id >= LIMIT_BLOCK_RULE_BASE_ID && r.condition && r.condition.urlFilter === `||${domain}`);
    if (existingRule) return;

    // Generate unique ID in the 1000+ range
    const usedIds = new Set(existing.map(r => r.id));
    let newId = LIMIT_BLOCK_RULE_BASE_ID;
    while (usedIds.has(newId)) newId++;

    const rule = {
      ...buildBlockRule(newId, domain),
      priority: 2
    };

    await chrome.declarativeNetRequest.updateDynamicRules({
      addRules: [rule],
      removeRuleIds: []
    });
    console.log(`Driftless: 100% daily limit DNR block applied to ${domain} (rule id: ${newId})`);

    // If user's active tab is currently on this domain, reload to trigger DNR block immediately
    const activeTab = await getActiveTabSafe();
    if (activeTab && cleanDomain(activeTab.url) === domain) {
      chrome.tabs.reload(activeTab.id);
    }
  } catch (err) {
    console.error('DNR limit block rule error:', err);
  }
}

// ── Focus Mode (DNR Rules) ───────────────────────────────────────────────────

async function enableFocusMode() {
  const {
    distractingSites = [],
    blockedSites = [],
    productiveSites = [],
    allowedSites = []
  } = await chrome.storage.local.get([
    'distractingSites', 'blockedSites', 'productiveSites', 'allowedSites'
  ]);
  const defaultBlocked = ['instagram.com', 'youtube.com', 'reddit.com', 'x.com'];
  const rawList = distractingSites.length > 0 ? distractingSites : (blockedSites.length > 0 ? blockedSites : defaultBlocked);
  const productiveList = new Set([...productiveSites, ...allowedSites].map(cleanDomain).filter(Boolean));
  // Productive sites stay accessible as normal
  const sitesToBlock = Array.from(new Set(rawList.map(cleanDomain).filter(Boolean)))
    .filter(domain => !productiveList.has(domain));

  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeIds = existing.filter(r => r.id >= FOCUS_RULE_BASE_ID && r.id < LIMIT_BLOCK_RULE_BASE_ID).map(r => r.id);

  const addRules = sitesToBlock.map((domain, i) => buildBlockRule(FOCUS_RULE_BASE_ID + i, domain));

  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: removeIds,
    addRules
  });
  console.log('Driftless: Focus Mode ON — blocking:', sitesToBlock.join(', '));

  // Reload tab if currently viewing a blocked distracting site
  const activeTab = await getActiveTabSafe();
  if (activeTab && sitesToBlock.includes(cleanDomain(activeTab.url))) {
    chrome.tabs.reload(activeTab.id);
  }
}

async function disableFocusMode() {
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeIds = existing.filter(r => r.id >= FOCUS_RULE_BASE_ID && r.id < LIMIT_BLOCK_RULE_BASE_ID).map(r => r.id);
  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: removeIds,
    addRules: []
  });
  console.log('Driftless: Focus Mode OFF — dynamic focus rules cleared.');
}

// ── Scheduled Focus Mode (Manifest V3 Alarms) ────────────────────────────────

function parseTimeMinutes(timeStr) {
  if (!timeStr || typeof timeStr !== 'string') return null;
  const parts = timeStr.trim().split(':');
  if (parts.length < 2) return null;
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(h) || isNaN(m) || h < 0 || h > 23 || m < 0 || m > 59) return null;
  return h * 60 + m;
}

function isWithinScheduleWindow(startStr, endStr, now = new Date()) {
  const startMin = parseTimeMinutes(startStr);
  const endMin = parseTimeMinutes(endStr);
  if (startMin === null || endMin === null || startMin === endMin) return false;

  const nowMin = now.getHours() * 60 + now.getMinutes();

  if (startMin < endMin) {
    // Normal window on same calendar day (e.g. 09:00 to 12:00)
    return nowMin >= startMin && nowMin < endMin;
  } else {
    // Window crosses midnight (e.g. 22:00 to 02:00)
    return nowMin >= startMin || nowMin < endMin;
  }
}

function getNextOccurrenceMs(timeStr, now = new Date()) {
  const mins = parseTimeMinutes(timeStr);
  if (mins === null) return null;
  const target = new Date(now);
  target.setHours(Math.floor(mins / 60), mins % 60, 0, 0);
  if (target.getTime() <= now.getTime()) {
    target.setDate(target.getDate() + 1);
  }
  return target.getTime();
}

async function syncFocusModeToBackend(isEnabled) {
  try {
    const { apiToken } = await chrome.storage.local.get(['apiToken']);
    if (apiToken) {
      const serverUrl = await getServerUrl();
      await fetch(`${serverUrl}/api/settings/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
        body: JSON.stringify({ focus_mode_active: isEnabled })
      }).catch(() => {});
    }
  } catch (err) {
    console.debug('Failed to sync focus mode to backend:', err);
  }
}

async function updateScheduleAlarms() {
  try {
    await chrome.alarms.clear(ALARM_SCHEDULE_START);
    await chrome.alarms.clear(ALARM_SCHEDULE_END);

    const { scheduleEnabled = false, scheduleStart = '20:00', scheduleEnd = '22:00' } = await chrome.storage.local.get([
      'scheduleEnabled', 'scheduleStart', 'scheduleEnd'
    ]);

    if (!scheduleEnabled) {
      console.log('Driftless: Schedule is disabled. Schedule alarms cleared.');
      return;
    }

    const startMs = getNextOccurrenceMs(scheduleStart);
    const endMs = getNextOccurrenceMs(scheduleEnd);

    if (startMs) {
      chrome.alarms.create(ALARM_SCHEDULE_START, {
        when: startMs,
        periodInMinutes: 24 * 60
      });
      console.log(`Driftless: Alarm ${ALARM_SCHEDULE_START} set for ${new Date(startMs).toLocaleTimeString()}`);
    }
    if (endMs) {
      chrome.alarms.create(ALARM_SCHEDULE_END, {
        when: endMs,
        periodInMinutes: 24 * 60
      });
      console.log(`Driftless: Alarm ${ALARM_SCHEDULE_END} set for ${new Date(endMs).toLocaleTimeString()}`);
    }
  } catch (err) {
    console.error('Failed to update schedule alarms:', err);
  }
}

async function evaluateScheduleState(reason = '') {
  try {
    const {
      scheduleEnabled = false,
      scheduleStart = '20:00',
      scheduleEnd = '22:00',
      focusModeActive = false,
      focusModeSource = null
    } = await chrome.storage.local.get([
      'scheduleEnabled', 'scheduleStart', 'scheduleEnd', 'focusModeActive', 'focusModeSource'
    ]);

    if (!scheduleEnabled) {
      // If schedule turned OFF and focus mode was ON via schedule, disable it
      if (focusModeActive && focusModeSource === 'schedule') {
        console.log(`Driftless: Schedule disabled, turning OFF scheduled Focus Mode (${reason})`);
        await chrome.storage.local.set({ focusModeActive: false, focusModeSource: null });
        await disableFocusMode();
        await syncFocusModeToBackend(false);
      }
      return;
    }

    const inWindow = isWithinScheduleWindow(scheduleStart, scheduleEnd);

    if (inWindow) {
      // Currently inside prime time window: should be ON
      if (!focusModeActive) {
        console.log(`Driftless: Scheduled focus window active (${scheduleStart} - ${scheduleEnd}), activating Focus Mode (${reason})`);
        await chrome.storage.local.set({ focusModeActive: true, focusModeSource: 'schedule' });
        await enableFocusMode();
        await syncFocusModeToBackend(true);
      }
    } else {
      // Currently outside prime time window
      // Requirement 7: If the user had already turned Focus Mode ON manually, the schedule must NOT turn it OFF
      if (focusModeActive && focusModeSource === 'schedule') {
        console.log(`Driftless: Scheduled focus window ended (${scheduleStart} - ${scheduleEnd}), turning Focus Mode OFF (${reason})`);
        await chrome.storage.local.set({ focusModeActive: false, focusModeSource: null });
        await disableFocusMode();
        await syncFocusModeToBackend(false);
      }
    }
  } catch (err) {
    console.error('Failed to evaluate schedule state:', err);
  }
}

// ── Tab & Window Tracking Events ─────────────────────────────────────────────

async function onActiveTabChanged() {
  await commitActiveTime();
  try {
    const tab = await getActiveTabSafe();
    currentTabDomain = cleanDomain(tab?.url);
    lastCommitTimestamp = Date.now();
    await chrome.storage.local.set({
      activeTrackingSession: {
        domain: currentTabDomain,
        lastCommitTimestamp,
        isWindowFocused,
        isUserActive
      }
    });
  } catch (e) {
    currentTabDomain = null;
  }
}

chrome.tabs.onActivated.addListener(async () => {
  await onActiveTabChanged();
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (tab.active && (changeInfo.url || changeInfo.status === 'complete')) {
    await commitActiveTime();
    currentTabDomain = cleanDomain(tab.url);
    lastCommitTimestamp = Date.now();
    await chrome.storage.local.set({
      activeTrackingSession: {
        domain: currentTabDomain,
        lastCommitTimestamp,
        isWindowFocused,
        isUserActive
      }
    });
  }
});

chrome.windows.onFocusChanged.addListener(async windowId => {
  await commitActiveTime();
  isWindowFocused = (windowId !== chrome.windows.WINDOW_ID_NONE);
  lastCommitTimestamp = Date.now();
  await chrome.storage.local.set({
    activeTrackingSession: {
      domain: currentTabDomain,
      lastCommitTimestamp,
      isWindowFocused,
      isUserActive
    }
  });
});

// Idle Detection
chrome.idle.setDetectionInterval(60);
chrome.idle.onStateChanged.addListener(async newState => {
  await commitActiveTime();
  isUserActive = (newState === 'active');
  lastCommitTimestamp = Date.now();
  await chrome.storage.local.set({
    activeTrackingSession: {
      domain: currentTabDomain,
      lastCommitTimestamp,
      isWindowFocused,
      isUserActive
    }
  });
});

// Regular ticker to commit time accurately while browsing on active tab
setInterval(async () => {
  await commitActiveTime();
}, 1000);

// ── Midnight Reset ────────────────────────────────────────────────────────────

async function scheduleMidnightReset() {
  await chrome.alarms.clear(ALARM_MIDNIGHT_RESET);

  const now = new Date();
  const midnight = new Date(now);
  midnight.setHours(24, 0, 0, 0);
  const msUntilMidnight = midnight.getTime() - now.getTime();

  chrome.alarms.create(ALARM_MIDNIGHT_RESET, {
    when: Date.now() + msUntilMidnight,
    periodInMinutes: 24 * 60
  });
  console.log(`Driftless: midnight reset scheduled in ${Math.round(msUntilMidnight / 60000)} mins.`);
}

async function performMidnightReset() {
  await commitActiveTime();
  await syncToBackend(); // Final flush for yesterday

  // Clear DNR dynamic limit block rules (1000+)
  const dynamicRules = await chrome.declarativeNetRequest.getDynamicRules();
  const limitRuleIds = dynamicRules
    .filter(r => r.id >= LIMIT_BLOCK_RULE_BASE_ID)
    .map(r => r.id);

  if (limitRuleIds.length > 0) {
    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: limitRuleIds,
      addRules: []
    });
  }

  // Reset daily counters & escalation states
  await chrome.storage.local.set({
    siteTimes: {},
    unsyncedDeltas: {},
    escalationState: {},
    lastResetDate: new Date().toISOString().slice(0, 10)
  });

  console.log('Driftless: midnight reset performed successfully. All counters and blocks cleared.');
  scheduleMidnightReset();
}

// ── Backend Sync (Bidirectional Sync) ─────────────────────────────────────────

async function syncToBackend() {
  await commitActiveTime();

  const {
    apiToken,
    unsyncedDeltas = {},
    siteTimes = {},
    distractingSites = [],
    productiveSites = []
  } = await chrome.storage.local.get([
    'apiToken', 'unsyncedDeltas', 'siteTimes', 'distractingSites', 'productiveSites'
  ]);

  if (!apiToken) return;

  const serverUrl = await getServerUrl();
  const today = new Date().toISOString().slice(0, 10);

  // 1. Push unsynced usage deltas
  const entries = Object.entries(unsyncedDeltas)
    .filter(([, secs]) => secs > 0)
    .map(([website_url, time_spent_seconds]) => ({
      website_url,
      time_spent_seconds,
      date: today
    }));

  if (entries.length > 0) {
    try {
      const res = await fetch(`${serverUrl}/api/usage/`, {
        method:  'POST',
        headers: {
          'Content-Type':  'application/json',
          'Authorization': `Token ${apiToken}`,
        },
        body: JSON.stringify(entries),
      });

      if (res.ok) {
        await chrome.storage.local.set({ unsyncedDeltas: {}, lastSyncedTime: Date.now() });
        console.log(`Driftless sync: pushed ${entries.length} domain logs.`);
      }
    } catch (err) {
      console.warn('Driftless sync offline / push error:', err);
    }
  }

  // 2. Pull settings, summary, and limits from server (Single Source of Truth)
  try {
    const sRes = await fetch(`${serverUrl}/api/summary/`, {
      headers: { 'Authorization': `Token ${apiToken}` }
    });

    if (sRes.ok) {
      const summary = await sRes.json();
      const settings = summary.settings || {};
      const stats = summary.stats || {};
      const daily = summary.daily || [];
      const distractions = summary.distractions || [];

      // Streak
      const streak = settings.streak_days !== undefined ? settings.streak_days : (stats.streak || 0);

      // Focus Mode Active
      const focusModeActive = !!settings.focus_mode_active;

      // Global Daily Limit
      const userTimeLimitMinutes = settings.daily_limit_minutes || 60;

      // Synchronize Site Lists:
      // STRICT RULE: A sync from the server must NEVER replace a non-empty local list with an empty list.
      const { defaultsSeeded = false, persona = 'Student' } = await chrome.storage.local.get(['defaultsSeeded', 'persona']);
      const serverPersona = (summary.user && summary.user.persona) ? summary.user.persona : persona;
      let didSeed = defaultsSeeded;

      let newDistracting = [...distractingSites];
      if (settings.blocked_sites && settings.blocked_sites.trim()) {
        const parsedBlocked = settings.blocked_sites.split(/[\r\n,]+/).map(cleanDomain).filter(Boolean);
        if (parsedBlocked.length > 0) {
          newDistracting = parsedBlocked;
        } else if (distractingSites.length > 0) {
          // Keep non-empty local list and push to server
          fetch(`${serverUrl}/api/settings/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
            body: JSON.stringify({ blocked_sites: distractingSites.join('\n') })
          }).catch(() => {});
        }
      } else if (distractingSites.length > 0) {
        // Push local distracting list to server
        fetch(`${serverUrl}/api/settings/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
          body: JSON.stringify({ blocked_sites: distractingSites.join('\n') })
        }).catch(() => {});
      }

      let newProductive = [...productiveSites];
      if (settings.allowed_sites && settings.allowed_sites.trim()) {
        const parsedAllowed = settings.allowed_sites.split(/[\r\n,]+/).map(cleanDomain).filter(Boolean);
        if (parsedAllowed.length > 0) {
          newProductive = parsedAllowed;
        } else if (productiveSites.length > 0) {
          // Keep non-empty local list and push to server
          fetch(`${serverUrl}/api/settings/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
            body: JSON.stringify({ allowed_sites: productiveSites.join('\n') })
          }).catch(() => {});
        }
      } else if (productiveSites.length > 0) {
        // Push local productive list to server
        fetch(`${serverUrl}/api/settings/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
          body: JSON.stringify({ allowed_sites: productiveSites.join('\n') })
        }).catch(() => {});
      }

      // If user has empty lists, seed them from persona defaults
      if (newDistracting.length === 0 && newProductive.length === 0) {
        const pKey = getPersonaKey(serverPersona);
        const pDef = PERSONA_DEFAULTS[pKey] || PERSONA_DEFAULTS.Student;
        newDistracting = [...pDef.distracting];
        newProductive = [...pDef.productive];
        didSeed = true;

        fetch(`${serverUrl}/api/settings/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
          body: JSON.stringify({
            blocked_sites: newDistracting.join('\n'),
            allowed_sites: newProductive.join('\n')
          })
        }).catch(() => {});
      }

      // Never replace non-empty local list with empty list
      if (distractingSites.length > 0 && newDistracting.length === 0) {
        newDistracting = distractingSites;
      }
      if (productiveSites.length > 0 && newProductive.length === 0) {
        newProductive = productiveSites;
      }

      // Sync siteTimes: server today seconds is ground truth, preserve any local unsynced deltas
      const updatedSiteTimes = { ...siteTimes };
      daily.forEach(item => {
        const domain = cleanDomain(item.website_url);
        if (domain) {
          const localDelta = (unsyncedDeltas[domain] || 0);
          updatedSiteTimes[domain] = Math.max(item.total_seconds + localDelta, updatedSiteTimes[domain] || 0);
        }
      });

      // Sync siteLimits
      const { siteLimits = {} } = await chrome.storage.local.get(['siteLimits']);
      const updatedSiteLimits = { ...siteLimits };
      distractions.forEach(item => {
        const domain = cleanDomain(item.website_url);
        if (domain && item.limit_id) {
          updatedSiteLimits[domain] = {
            id: item.limit_id,
            domain,
            daily_limit_minutes: item.limit_minutes,
            enabled: item.enabled,
            is_custom: true
          };
        }
      });

      // Sync Schedule from backend
      const serverScheduleEnabled = settings.schedule_enabled !== undefined ? !!settings.schedule_enabled : false;
      const serverScheduleStart = settings.schedule_start || '20:00';
      const serverScheduleEnd = settings.schedule_end || '22:00';

      await chrome.storage.local.set({
        defaultsSeeded: didSeed,
        streakDays: streak,
        focusModeActive,
        userTimeLimitMinutes,
        distractingSites: newDistracting,
        blockedSites: newDistracting,
        productiveSites: newProductive,
        allowedSites: newProductive,
        siteTimes: updatedSiteTimes,
        siteLimits: updatedSiteLimits,
        scheduleEnabled: serverScheduleEnabled,
        scheduleStart: serverScheduleStart,
        scheduleEnd: serverScheduleEnd,
        lastSyncedTime: Date.now()
      });

      await updateScheduleAlarms();
      await evaluateScheduleState('sync');

      if (focusModeActive) {
        await enableFocusMode();
      } else {
        await disableFocusMode();
      }
      console.log('Driftless: bidirectional sync complete.');
    }
  } catch (err) {
    console.debug('Driftless sync pull error:', err);
  }
}

// ── Alarms & Message Handlers ────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(async () => {
  const data = await chrome.storage.local.get(['distractingSites', 'productiveSites', 'persona']);
  const hasDist = Array.isArray(data.distractingSites) && data.distractingSites.length > 0;
  const hasProd = Array.isArray(data.productiveSites) && data.productiveSites.length > 0;
  if (!hasDist || !hasProd) {
    const pKey = getPersonaKey(data.persona || 'Student');
    const pDef = PERSONA_DEFAULTS[pKey] || PERSONA_DEFAULTS.Student;
    const distractingSites = hasDist ? data.distractingSites : [...pDef.distracting];
    const productiveSites = hasProd ? data.productiveSites : [...pDef.productive];
    await chrome.storage.local.set({
      defaultsSeeded: true,
      persona: pKey,
      distractingSites,
      blockedSites: distractingSites,
      productiveSites,
      allowedSites: productiveSites
    });
  }
});

chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name === ALARM_MIDNIGHT_RESET) {
    await performMidnightReset();
  } else if (alarm.name === ALARM_PERIODIC_SYNC) {
    await syncToBackend();
  } else if (alarm.name === ALARM_TICK) {
    await commitActiveTime();
    await evaluateScheduleState('tick');
  } else if (alarm.name === ALARM_SCHEDULE_START || alarm.name === ALARM_SCHEDULE_END) {
    await evaluateScheduleState(alarm.name);
    await updateScheduleAlarms();
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'SET_FOCUS_MODE') {
    (async () => {
      try {
        const isEnabled = !!message.enabled;
        await chrome.storage.local.set({
          focusModeActive: isEnabled,
          focusModeSource: isEnabled ? 'manual' : null
        });
        if (isEnabled) {
          await enableFocusMode();
        } else {
          await disableFocusMode();
        }

        // Sync to backend if token present
        const { apiToken } = await chrome.storage.local.get(['apiToken']);
        if (apiToken) {
          const serverUrl = await getServerUrl();
          fetch(`${serverUrl}/api/settings/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
            body: JSON.stringify({ focus_mode_active: isEnabled })
          }).catch(() => {});
        }
        sendResponse({ success: true, focusModeActive: isEnabled });
      } catch (err) {
        console.error('Focus mode error:', err);
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true;
  }

  if (message.type === 'UPDATE_SCHEDULE') {
    (async () => {
      try {
        const { scheduleEnabled, scheduleStart, scheduleEnd } = message;
        const updates = {};
        if (scheduleEnabled !== undefined) updates.scheduleEnabled = !!scheduleEnabled;
        if (scheduleStart !== undefined) updates.scheduleStart = scheduleStart;
        if (scheduleEnd !== undefined) updates.scheduleEnd = scheduleEnd;

        await chrome.storage.local.set(updates);
        await updateScheduleAlarms();
        await evaluateScheduleState('update_schedule');

        // Sync to backend if token present
        const { apiToken } = await chrome.storage.local.get(['apiToken']);
        if (apiToken) {
          const serverUrl = await getServerUrl();
          const patchData = {};
          if (scheduleEnabled !== undefined) patchData.schedule_enabled = !!scheduleEnabled;
          if (scheduleStart !== undefined) patchData.schedule_start = scheduleStart;
          if (scheduleEnd !== undefined) patchData.schedule_end = scheduleEnd;

          fetch(`${serverUrl}/api/settings/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
            body: JSON.stringify(patchData)
          }).catch(() => {});
        }
        sendResponse({ success: true, ...updates });
      } catch (err) {
        console.error('Update schedule error:', err);
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true;
  }

  if (message.type === 'UPDATE_SITE_LISTS') {
    (async () => {
      const { distractingSites, productiveSites } = message;
      await chrome.storage.local.set({
        distractingSites,
        blockedSites: distractingSites,
        productiveSites,
        allowedSites: productiveSites
      });

      const { focusModeActive, apiToken } = await chrome.storage.local.get(['focusModeActive', 'apiToken']);
      if (focusModeActive) {
        await enableFocusMode();
      }

      // Sync to backend
      if (apiToken) {
        const serverUrl = await getServerUrl();
        fetch(`${serverUrl}/api/settings/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
          body: JSON.stringify({
            blocked_sites: distractingSites.join('\n'),
            allowed_sites: productiveSites.join('\n')
          })
        }).catch(() => {});
      }

      sendResponse({ success: true });
    })();
    return true;
  }

  if (message.type === 'SET_GLOBAL_LIMIT') {
    (async () => {
      const limitMinutes = parseInt(message.limitMinutes, 10) || 60;
      await chrome.storage.local.set({ userTimeLimitMinutes: limitMinutes });

      const { apiToken } = await chrome.storage.local.get(['apiToken']);
      if (apiToken) {
        const serverUrl = await getServerUrl();
        fetch(`${serverUrl}/api/settings/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
          body: JSON.stringify({ daily_limit_minutes: limitMinutes })
        }).catch(() => {});
      }
      sendResponse({ success: true });
    })();
    return true;
  }

  if (message.type === 'SET_CUSTOM_LIMIT') {
    (async () => {
      const { domain, limitMinutes } = message;
      const cleanDom = cleanDomain(domain) || domain;
      const { siteLimits = {}, siteTimes = {}, escalationState = {}, apiToken } = await chrome.storage.local.get([
        'siteLimits', 'siteTimes', 'escalationState', 'apiToken'
      ]);
      siteLimits[cleanDom] = {
        domain: cleanDom,
        daily_limit_minutes: limitMinutes,
        enabled: true,
        is_custom: true
      };

      // If user increased limit above current usage, reset blocked state and remove dynamic DNR limit block
      const currentSeconds = siteTimes[cleanDom] || 0;
      const newLimitSeconds = limitMinutes * 60;
      const newNudgeSeconds = Math.floor(newLimitSeconds * 0.8);
      const state = escalationState[cleanDom] || { nudged: false, blocked: false };

      if (currentSeconds < newLimitSeconds && state.blocked) {
        state.blocked = false;
        const rules = await chrome.declarativeNetRequest.getDynamicRules();
        const ruleToRemove = rules.find(r => r.id >= LIMIT_BLOCK_RULE_BASE_ID && r.condition && r.condition.urlFilter === `||${cleanDom}`);
        if (ruleToRemove) {
          await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: [ruleToRemove.id], addRules: [] });
        }
      }
      if (currentSeconds < newNudgeSeconds) {
        state.nudged = false;
      }
      escalationState[cleanDom] = state;

      await chrome.storage.local.set({ siteLimits, escalationState });
      await evaluateSiteLimits(cleanDom, currentSeconds);

      if (apiToken) {
        const serverUrl = await getServerUrl();
        fetch(`${serverUrl}/api/limits/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
          body: JSON.stringify({ domain: cleanDom, daily_limit_minutes: limitMinutes, enabled: true })
        }).catch(() => {});
      }
      sendResponse({ success: true });
    })();
    return true;
  }

  if (message.type === 'REMOVE_CUSTOM_LIMIT') {
    (async () => {
      const { domain } = message;
      const { siteLimits = {}, apiToken } = await chrome.storage.local.get(['siteLimits', 'apiToken']);
      const limitObj = siteLimits[domain];
      delete siteLimits[domain];
      await chrome.storage.local.set({ siteLimits });

      if (apiToken && limitObj && limitObj.id) {
        const serverUrl = await getServerUrl();
        fetch(`${serverUrl}/api/limits/${limitObj.id}/`, {
          method: 'DELETE',
          headers: { 'Authorization': `Token ${apiToken}` }
        }).catch(() => {});
      }
      sendResponse({ success: true });
    })();
    return true;
  }

  if (message.type === 'TRIGGER_SYNC') {
    syncToBackend()
      .then(() => sendResponse({ success: true }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === 'RESET_ALL_TIMERS') {
    (async () => {
      // Clear limit block rules
      const rules = await chrome.declarativeNetRequest.getDynamicRules();
      const limitIds = rules.filter(r => r.id >= LIMIT_BLOCK_RULE_BASE_ID).map(r => r.id);
      if (limitIds.length > 0) {
        await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: limitIds, addRules: [] });
      }

      await chrome.storage.local.set({
        siteTimes: {},
        unsyncedDeltas: {},
        escalationState: {}
      });
      sendResponse({ success: true });
    })();
    return true;
  }
});

// ── Alarms & Tracker Initialization ──────────────────────────────────────────

async function setupAlarms() {
  const existing = await chrome.alarms.getAll();
  const existingNames = new Set(existing.map(a => a.name));

  if (!existingNames.has(ALARM_TICK)) {
    chrome.alarms.create(ALARM_TICK, { periodInMinutes: 1 });
  }
  if (!existingNames.has(ALARM_PERIODIC_SYNC)) {
    chrome.alarms.create(ALARM_PERIODIC_SYNC, { periodInMinutes: 1 });
  }
  scheduleMidnightReset();
  await updateScheduleAlarms();
}

// Re-create alarms & evaluate schedule on browser startup and install
chrome.runtime.onStartup.addListener(async () => {
  await setupAlarms();
  await updateScheduleAlarms();
  await evaluateScheduleState('onStartup');
});

chrome.runtime.onInstalled.addListener(async () => {
  await setupAlarms();
  await updateScheduleAlarms();
  await evaluateScheduleState('onInstalled');
});

async function initTracker() {
  try {
    const lastFocused = await chrome.windows.getLastFocused({ populate: false }).catch(() => null);
    if (lastFocused) {
      isWindowFocused = !!lastFocused.focused;
    }
    const tab = await getActiveTabSafe();
    if (tab && tab.url) {
      currentTabDomain = cleanDomain(tab.url);
    }
    lastCommitTimestamp = Date.now();
    await commitActiveTime();
  } catch (e) {
    console.error('Failed to init tracker:', e);
  }
}

// Storage change listener to ensure Focus Mode is applied whenever storage changes
chrome.storage.onChanged.addListener(async (changes, areaName) => {
  if (areaName !== 'local') return;
  if (changes.focusModeActive && changes.focusModeActive.oldValue !== changes.focusModeActive.newValue) {
    const isEnabled = !!changes.focusModeActive.newValue;
    if (isEnabled) {
      await enableFocusMode();
    } else {
      await disableFocusMode();
    }
  }
  if (changes.scheduleEnabled || changes.scheduleStart || changes.scheduleEnd) {
    await updateScheduleAlarms();
    await evaluateScheduleState('storage_change');
  }
});

// Run tracker initialization and setup alarms
initTracker();
setupAlarms();
updateScheduleAlarms();
evaluateScheduleState('script_init');

// Also check Focus Mode state on startup to ensure rules are active if enabled
chrome.storage.local.get(['focusModeActive'], async ({ focusModeActive }) => {
  if (focusModeActive) {
    await enableFocusMode();
  }
});