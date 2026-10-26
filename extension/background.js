// ─────────────────────────────────────────────────────────────────────────────
// DRIFTLESS BACKGROUND SERVICE WORKER (Manifest V3)
// Full domain tracking (Productive + Distracting + Other)
// Per-site limits, 3-tier escalation logic (80% Nudge -> 100% Alert -> +5m DNR block)
// Focus timer session logging & bidirectional sync with Django REST API.
// ─────────────────────────────────────────────────────────────────────────────

const ALARM_CHECK_TIMER       = 'driftless_check_timer';
const ALARM_MIDNIGHT_RESET    = 'driftless_midnight_reset';
const ALARM_PERIODIC_SYNC     = 'driftless_periodic_sync';
const ALARM_FOCUS_TIMER_END   = 'driftless_focus_timer_end';

const FOCUS_RULE_BASE_ID      = 100;
const LIMIT_BLOCK_RULE_BASE_ID= 1000;
const DEFAULT_SERVER_URL      = 'http://127.0.0.1:8000';

let currentTabDomain  = null;
let currentTabStartTime = null;
let isWindowFocused   = true;
let isUserActive      = true;

console.log('Driftless Background Service Worker initialized.');

// ── Helpers ──────────────────────────────────────────────────────────────────

function cleanDomain(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    if (!['http:', 'https:'].includes(u.protocol)) return null;
    let host = u.hostname.toLowerCase();
    if (host.startsWith('www.')) host = host.slice(4);
    return host;
  } catch (e) {
    return null;
  }
}

async function getServerUrl() {
  const { serverUrl } = await chrome.storage.local.get(['serverUrl']);
  return (serverUrl && serverUrl.trim()) ? serverUrl.trim().replace(/\/+$/, '') : DEFAULT_SERVER_URL;
}

// ── Time Accumulation ────────────────────────────────────────────────────────

async function commitActiveTime() {
  if (!currentTabDomain || !currentTabStartTime || !isWindowFocused || !isUserActive) {
    currentTabStartTime = Date.now();
    return;
  }

  const now = Date.now();
  const elapsedSeconds = Math.floor((now - currentTabStartTime) / 1000);
  currentTabStartTime = now;

  if (elapsedSeconds <= 0) return;

  const { siteTimes = {}, unsyncedDeltas = {} } = await chrome.storage.local.get([
    'siteTimes', 'unsyncedDeltas'
  ]);

  siteTimes[currentTabDomain] = (siteTimes[currentTabDomain] || 0) + elapsedSeconds;
  unsyncedDeltas[currentTabDomain] = (unsyncedDeltas[currentTabDomain] || 0) + elapsedSeconds;

  await chrome.storage.local.set({ siteTimes, unsyncedDeltas });
  await evaluateSiteLimits(currentTabDomain, siteTimes[currentTabDomain]);
}

// ── Escalation Logic (80% Nudge -> 100% Alert -> +5m Block) ──────────────────

async function evaluateSiteLimits(domain, totalSeconds) {
  const {
    siteLimits = {},
    userTimeLimitMinutes = 60,
    escalationState = {} // { [domain]: { nudged: bool, alerted: bool, blocked: bool } }
  } = await chrome.storage.local.get(['siteLimits', 'userTimeLimitMinutes', 'escalationState']);

  const siteConfig = siteLimits[domain];
  let limitMins = userTimeLimitMinutes;
  let isEnabled = true;

  if (siteConfig && typeof siteConfig.daily_limit_minutes === 'number') {
    limitMins = siteConfig.daily_limit_minutes;
    isEnabled = siteConfig.enabled !== false;
  }

  if (!isEnabled) return;

  const limitSeconds = limitMins * 60;
  const gracePeriodSeconds = 5 * 60; // 5 minutes grace past 100%
  const state = escalationState[domain] || { nudged: false, alerted: false, blocked: false };

  // 1. 80% Threshold — Gentle Nudge
  if (totalSeconds >= limitSeconds * 0.8 && !state.nudged) {
    state.nudged = true;
    escalationState[domain] = state;
    await chrome.storage.local.set({ escalationState });
    sendNudgeNotification(domain, Math.round(totalSeconds / 60), limitMins);
  }

  // 2. 100% Threshold — Alert
  if (totalSeconds >= limitSeconds && !state.alerted) {
    state.alerted = true;
    escalationState[domain] = state;
    await chrome.storage.local.set({ escalationState, streakAtRisk: true });
    sendAlertNotification(domain, limitMins);
  }

  // 3. 100% + 5m Grace Period Exceeded — Block Site
  if (totalSeconds >= (limitSeconds + gracePeriodSeconds) && !state.blocked) {
    state.blocked = true;
    escalationState[domain] = state;
    await chrome.storage.local.set({ escalationState });
    await blockDomainViaDNR(domain);
  }
}

function sendNudgeNotification(domain, currentMins, limitMins) {
  chrome.notifications.create(`nudge-${domain}-${Date.now()}`, {
    type:     'basic',
    iconUrl:  'icons/icon-128.png',
    title:    'Driftless — Nudge ⏳',
    message:  `You've used ${currentMins}m of your ${limitMins}m daily limit on ${domain}.`,
    priority: 1
  });
}

function sendAlertNotification(domain, limitMins) {
  chrome.notifications.create(`alert-${domain}-${Date.now()}`, {
    type:     'basic',
    iconUrl:  'icons/icon-128.png',
    title:    'Driftless — 100% Limit Reached ⚠️',
    message:  `Daily limit of ${limitMins}m reached on ${domain}! 5m grace period active before site is blocked.`,
    priority: 2
  });
}

async function blockDomainViaDNR(domain) {
  try {
    const existing = await chrome.declarativeNetRequest.getDynamicRules();
    const existingRule = existing.find(r => r.condition && r.condition.urlFilter === `||${domain}`);
    
    if (existingRule) return;

    const newId = LIMIT_BLOCK_RULE_BASE_ID + Math.floor(Math.random() * 8000);
    const redirectUrl = chrome.runtime.getURL(`blocked.html?site=${encodeURIComponent(domain)}`);

    await chrome.declarativeNetRequest.updateDynamicRules({
      addRules: [{
        id: newId,
        priority: 2,
        action: {
          type: 'redirect',
          redirect: { url: redirectUrl }
        },
        condition: {
          urlFilter: `||${domain}`,
          resourceTypes: ['main_frame']
        }
      }],
      removeRuleIds: []
    });

    console.log(`Driftless: DNR block rule applied to ${domain}`);
    
    // Redirect existing active tab if currently on this site
    const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (activeTab && cleanDomain(activeTab.url) === domain) {
      chrome.tabs.update(activeTab.id, { url: redirectUrl });
    }
  } catch (err) {
    console.error('DNR block rule error:', err);
  }
}

// ── Tab & Window Tracking Events ─────────────────────────────────────────────

async function onActiveTabChanged() {
  await commitActiveTime();
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTabDomain = cleanDomain(tab?.url);
    currentTabStartTime = Date.now();
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
    currentTabStartTime = Date.now();
  }
});

chrome.windows.onFocusChanged.addListener(async windowId => {
  await commitActiveTime();
  isWindowFocused = (windowId !== chrome.windows.WINDOW_ID_NONE);
  currentTabStartTime = Date.now();
});

// Idle Detection (do not count idle time)
chrome.idle.setDetectionInterval(60); // 60 seconds of inactivity
chrome.idle.onStateChanged.addListener(async newState => {
  await commitActiveTime();
  isUserActive = (newState === 'active');
  currentTabStartTime = Date.now();
});

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

  // Clear DNR dynamic limit block rules
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

  // Reset daily usage counters & escalation states
  await chrome.storage.local.set({
    siteTimes: {},
    unsyncedDeltas: {},
    escalationState: {},
    streakAtRisk: false,
    lastResetDate: new Date().toISOString().slice(0, 10)
  });

  console.log('Driftless: midnight reset performed successfully.');
}

// ── Backend Sync (POST deltas, pull settings & limits) ─────────────────────────

async function syncToBackend() {
  await commitActiveTime();

  const {
    apiToken,
    unsyncedDeltas = {},
    siteTimes = {}
  } = await chrome.storage.local.get(['apiToken', 'unsyncedDeltas', 'siteTimes']);

  if (!apiToken) return;

  const serverUrl = await getServerUrl();
  const today = new Date().toISOString().slice(0, 10);

  // Send batch of deltas if any
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
        // Clear synced deltas
        const remainingDeltas = {};
        await chrome.storage.local.set({ unsyncedDeltas: remainingDeltas, lastSyncedTime: Date.now() });
        console.log(`Driftless sync: pushed ${entries.length} domain logs.`);
      }
    } catch (err) {
      console.warn('Driftless sync offline / network error:', err);
    }
  }

  // Pull settings & site limits from backend
  await pullBackendConfig(serverUrl, apiToken);
}

async function pullBackendConfig(serverUrl, apiToken) {
  try {
    // 1. Settings
    const sRes = await fetch(`${serverUrl}/api/settings/`, {
      headers: { 'Authorization': `Token ${apiToken}` }
    });
    if (sRes.ok) {
      const settings = await sRes.json();
      await chrome.storage.local.set({
        focusModeActive: settings.focus_mode_active,
        userTimeLimitMinutes: settings.daily_limit_minutes,
        streakDays: settings.streak_days,
        requireChallenge: settings.require_challenge
      });
      if (settings.focus_mode_active) {
        await enableFocusMode();
      } else {
        await disableFocusMode();
      }
    }

    // 2. Per-Site Limits
    const lRes = await fetch(`${serverUrl}/api/limits/`, {
      headers: { 'Authorization': `Token ${apiToken}` }
    });
    if (lRes.ok) {
      const limitsList = await lRes.json();
      const siteLimits = {};
      limitsList.forEach(item => {
        siteLimits[item.domain] = item;
      });
      await chrome.storage.local.set({ siteLimits });
    }
  } catch (err) {
    console.debug('Driftless config pull error:', err);
  }
}

// ── Focus Mode (DNR Rules) ───────────────────────────────────────────────────

async function enableFocusMode() {
  const { blockedSites = [] } = await chrome.storage.local.get(['blockedSites']);
  const defaultBlocked = ['instagram.com', 'youtube.com', 'reddit.com', 'x.com', 'twitter.com', 'tiktok.com', 'netflix.com'];
  const sitesToBlock = blockedSites.length > 0 ? blockedSites : defaultBlocked;

  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeIds = existing.filter(r => r.id >= FOCUS_RULE_BASE_ID && r.id < LIMIT_BLOCK_RULE_BASE_ID).map(r => r.id);

  const addRules = sitesToBlock.map((domain, i) => ({
    id: FOCUS_RULE_BASE_ID + i,
    priority: 1,
    action: {
      type: 'redirect',
      redirect: { url: chrome.runtime.getURL(`blocked.html?site=${encodeURIComponent(domain)}`) }
    },
    condition: {
      urlFilter: `||${domain}`,
      resourceTypes: ['main_frame']
    }
  }));

  await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: removeIds, addRules });
}

async function disableFocusMode() {
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeIds = existing.filter(r => r.id >= FOCUS_RULE_BASE_ID && r.id < LIMIT_BLOCK_RULE_BASE_ID).map(r => r.id);
  await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: removeIds, addRules: [] });
}

// ── Alarms & Message Handlers ────────────────────────────────────────────────

chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name === ALARM_MIDNIGHT_RESET) {
    await performMidnightReset();
  } else if (alarm.name === ALARM_PERIODIC_SYNC) {
    await syncToBackend();
  } else if (alarm.name === ALARM_FOCUS_TIMER_END) {
    // Focus timer completed
    await disableFocusMode();
    await chrome.storage.local.set({ focusModeActive: false, focusTimerActive: false });
    
    // Log session to backend
    const { apiToken, lastFocusTimerDuration = 25 } = await chrome.storage.local.get(['apiToken', 'lastFocusTimerDuration']);
    if (apiToken) {
      const serverUrl = await getServerUrl();
      fetch(`${serverUrl}/api/sessions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
        body: JSON.stringify({ duration_minutes: lastFocusTimerDuration })
      }).catch(e => console.debug('Session log error:', e));
    }

    chrome.notifications.create(`focus-done-${Date.now()}`, {
      type: 'basic',
      iconUrl: 'icons/icon-128.png',
      title: 'Driftless — Focus Session Completed! 🎯',
      message: `Great job! Your ${lastFocusTimerDuration}-minute focus block is complete.`,
      priority: 2
    });
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'START_FOCUS_TIMER') {
    const durationMins = message.durationMinutes || 25;
    enableFocusMode()
      .then(() => chrome.storage.local.set({
        focusModeActive: true,
        focusTimerActive: true,
        focusTimerEndTime: Date.now() + (durationMins * 60 * 1000),
        lastFocusTimerDuration: durationMins
      }))
      .then(() => chrome.alarms.create(ALARM_FOCUS_TIMER_END, { delayInMinutes: durationMins }))
      .then(() => sendResponse({ success: true }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === 'STOP_FOCUS_TIMER') {
    chrome.alarms.clear(ALARM_FOCUS_TIMER_END);
    disableFocusMode()
      .then(() => chrome.storage.local.set({ focusModeActive: false, focusTimerActive: false }))
      .then(() => sendResponse({ success: true }));
    return true;
  }

  if (message.type === 'TRIGGER_SYNC') {
    syncToBackend()
      .then(() => sendResponse({ success: true }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === 'RESET_ALL_TIMERS') {
    chrome.storage.local.set({
      siteTimes: {},
      unsyncedDeltas: {},
      escalationState: {}
    }).then(async () => {
      // Clear dynamic block rules
      const rules = await chrome.declarativeNetRequest.getDynamicRules();
      const limitIds = rules.filter(r => r.id >= LIMIT_BLOCK_RULE_BASE_ID).map(r => r.id);
      if (limitIds.length > 0) {
        await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: limitIds, addRules: [] });
      }
      sendResponse({ success: true });
    });
    return true;
  }
});

// Periodic sync alarm: every 1 minute as requested in Section 4
chrome.alarms.create(ALARM_PERIODIC_SYNC, { periodInMinutes: 1 });
scheduleMidnightReset();