// ─────────────────────────────────────────────────────────────────────────────
// DRIFTLESS BACKGROUND SERVICE WORKER (Manifest V3)
// ─────────────────────────────────────────────────────────────────────────────

const ALARM_MIDNIGHT_RESET     = 'driftless_midnight_reset';
const ALARM_PERIODIC_SYNC      = 'driftless_periodic_sync';
const ALARM_TICK               = 'driftless_tick';

const FOCUS_RULE_BASE_ID       = 100;    // Dynamic rules 100..899 for Focus Mode
const LIMIT_BLOCK_RULE_BASE_ID = 1000;   // Dynamic rules 1000..9999 for 100% limit reached
const DEFAULT_SERVER_URL       = 'http://127.0.0.1:8000';

const PERSONA_DEFAULTS = {
  Student: {
    distracting: ['instagram.com', 'facebook.com', 'reddit.com', 'youtube.com'],
    productive: ['github.com', 'stackoverflow.com', 'docs.google.com', 'geeksforgeeks.org']
  },
  Professional: {
    distracting: ['instagram.com', 'facebook.com', 'youtube.com', 'x.com'],
    productive: ['github.com', 'docs.google.com', 'notion.so', 'stackoverflow.com']
  },
  Influencer: {
    distracting: ['facebook.com', 'reddit.com', 'netflix.com', 'x.com'],
    productive: ['canva.com', 'docs.google.com', 'drive.google.com', 'notion.so']
  },
  Creator: {
    distracting: ['facebook.com', 'reddit.com', 'netflix.com', 'x.com'],
    productive: ['canva.com', 'figma.com', 'behance.net', 'docs.google.com']
  },
  Other: {
    distracting: ['instagram.com', 'youtube.com', 'facebook.com', 'reddit.com'],
    productive: ['github.com', 'docs.google.com', 'stackoverflow.com', 'coursera.org']
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

let currentTabDomain   = null;
let currentTabStartTime= null;
let isWindowFocused    = true;
let isUserActive       = true;

console.log('Driftless Background Service Worker started.');

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
// "Time counts only while that site's tab is the active tab in a focused window."

async function commitActiveTime() {
  if (!currentTabDomain || !currentTabStartTime || !isWindowFocused || !isUserActive) {
    currentTabStartTime = Date.now();
    return;
  }

  const now = Date.now();
  const elapsedSeconds = Math.floor((now - currentTabStartTime) / 1000);
  if (elapsedSeconds <= 0) return;

  currentTabStartTime = now;

  const { siteTimes = {}, unsyncedDeltas = {} } = await chrome.storage.local.get([
    'siteTimes', 'unsyncedDeltas'
  ]);

  siteTimes[currentTabDomain] = (siteTimes[currentTabDomain] || 0) + elapsedSeconds;
  unsyncedDeltas[currentTabDomain] = (unsyncedDeltas[currentTabDomain] || 0) + elapsedSeconds;

  await chrome.storage.local.set({ siteTimes, unsyncedDeltas });
  await evaluateSiteLimits(currentTabDomain, siteTimes[currentTabDomain]);
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
  const allDistracting = Array.from(new Set([...distractingSites, ...blockedSites]));
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
    const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (activeTab && cleanDomain(activeTab.url) === domain) {
      chrome.tabs.reload(activeTab.id);
    }
  } catch (err) {
    console.error('DNR limit block rule error:', err);
  }
}

// ── Focus Mode (DNR Rules) ───────────────────────────────────────────────────

async function enableFocusMode() {
  const { distractingSites = [], blockedSites = [] } = await chrome.storage.local.get([
    'distractingSites', 'blockedSites'
  ]);
  const defaultBlocked = ['instagram.com', 'youtube.com', 'reddit.com', 'x.com'];
  const rawList = distractingSites.length > 0 ? distractingSites : (blockedSites.length > 0 ? blockedSites : defaultBlocked);
  const sitesToBlock = Array.from(new Set(rawList.map(cleanDomain).filter(Boolean)));

  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeIds = existing.filter(r => r.id >= FOCUS_RULE_BASE_ID && r.id < LIMIT_BLOCK_RULE_BASE_ID).map(r => r.id);

  const addRules = sitesToBlock.map((domain, i) => buildBlockRule(FOCUS_RULE_BASE_ID + i, domain));

  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: removeIds,
    addRules
  });
  console.log('Driftless: Focus Mode ON — blocking:', sitesToBlock.join(', '));

  // Reload tab if currently viewing a blocked distracting site
  const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
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

// Idle Detection
chrome.idle.setDetectionInterval(60);
chrome.idle.onStateChanged.addListener(async newState => {
  await commitActiveTime();
  isUserActive = (newState === 'active');
  currentTabStartTime = Date.now();
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

      // If user had empty lists and defaults were never seeded, seed them once from persona
      if (!defaultsSeeded && newDistracting.length === 0 && newProductive.length === 0) {
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
        lastSyncedTime: Date.now()
      });

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

chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name === ALARM_MIDNIGHT_RESET) {
    await performMidnightReset();
  } else if (alarm.name === ALARM_PERIODIC_SYNC) {
    await syncToBackend();
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'SET_FOCUS_MODE') {
    const isEnabled = !!message.enabled;
    const action = isEnabled ? enableFocusMode() : disableFocusMode();
    action
      .then(() => chrome.storage.local.set({ focusModeActive: isEnabled }))
      .then(async () => {
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
      })
      .catch(err => {
        console.error('Focus mode error:', err);
        sendResponse({ success: false, error: err.message });
      });
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
      const { siteLimits = {}, apiToken } = await chrome.storage.local.get(['siteLimits', 'apiToken']);
      siteLimits[domain] = {
        domain,
        daily_limit_minutes: limitMinutes,
        enabled: true,
        is_custom: true
      };
      await chrome.storage.local.set({ siteLimits });

      if (apiToken) {
        const serverUrl = await getServerUrl();
        fetch(`${serverUrl}/api/limits/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${apiToken}` },
          body: JSON.stringify({ domain, daily_limit_minutes: limitMinutes, enabled: true })
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

// Periodic sync alarm every 1 minute
chrome.alarms.create(ALARM_PERIODIC_SYNC, { periodInMinutes: 1 });
scheduleMidnightReset();