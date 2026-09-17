// ─────────────────────────────────────────────────────────────────────────────
// DRIFTLESS BACKGROUND SERVICE WORKER
// All site lists are dynamic — read from chrome.storage.local (blockedSites).
// No hardcoded domain arrays.
// ─────────────────────────────────────────────────────────────────────────────

const ALARM_NAME             = 'driftless_time_check';
const SYNC_ALARM_NAME        = 'driftless_daily_sync';
const DEFAULT_TIME_LIMIT_SEC = 60;    // Fallback: 1 minute
const FOCUS_RULE_BASE_ID     = 100;   // Dynamic rule IDs start here

// ── Backend API URL — update this to your production URL when deployed ────────
const API_BASE_URL = 'http://127.0.0.1:8000';

let timerTimeout = null;

console.log('Driftless Background Service Worker active.');



// ─────────────────────────────────────────────────────────────────────────────
// BACKEND SYNC — POST daily usage totals to the Django API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Reads siteTimes from local storage and the stored API token,
 * then POSTs all entries as a batch to /api/usage/.
 * Called by the nightly sync alarm and manually when the extension starts.
 */
async function syncToBackend() {
  const { apiToken, siteTimes, lastSyncDate } = await chrome.storage.local.get([
    'apiToken', 'siteTimes', 'lastSyncDate'
  ]);

  // No token means user hasn't linked the extension yet — skip silently.
  if (!apiToken) {
    console.log('Driftless sync: no API token stored, skipping.');
    return;
  }

  const times = siteTimes || {};
  const today = new Date().toISOString().slice(0, 10);

  const entries = Object.entries(times)
    .filter(([, secs]) => secs > 0)
    .map(([website_url, time_spent_seconds]) => ({
      website_url,
      time_spent_seconds,
      date: today,
    }));

  if (entries.length === 0) {
    console.log('Driftless sync: nothing to sync today.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/usage/`, {
      method:  'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Token ${apiToken}`,
      },
      body: JSON.stringify(entries),
    });

    if (!res.ok) {
      const err = await res.text();
      console.error(`Driftless sync failed (${res.status}):`, err);
      return;
    }

    const result = await res.json();
    console.log(`Driftless sync success — created: ${result.created}, updated: ${result.updated}`);
    await chrome.storage.local.set({ lastSyncDate: today });
  } catch (err) {
    console.error('Driftless sync network error:', err);
  }
}

/**
 * Schedules (or reschedules) the nightly midnight sync alarm.
 * Also runs an immediate sync if we haven't synced today yet.
 */
async function scheduleDailySync() {
  // Clear any existing sync alarm before recreating
  await chrome.alarms.clear(SYNC_ALARM_NAME);

  // Midnight tonight (local time) in ms
  const now       = new Date();
  const midnight  = new Date(now);
  midnight.setHours(24, 0, 0, 0); // next midnight
  const msUntilMidnight = midnight.getTime() - now.getTime();

  chrome.alarms.create(SYNC_ALARM_NAME, {
    when:        Date.now() + msUntilMidnight,
    periodInMinutes: 24 * 60,  // repeat every 24 hours
  });

  // If we haven't synced today, do it now
  const { lastSyncDate } = await chrome.storage.local.get(['lastSyncDate']);
  const today = now.toISOString().slice(0, 10);
  if (lastSyncDate !== today) {
    await syncToBackend();
  }

  const minsUntilMidnight = Math.round(msUntilMidnight / 60000);
  console.log(`Driftless: daily sync alarm set (fires in ${minsUntilMidnight} min).`);
}


// ─── Helper: read tracked sites from storage ─────────────────────────────────
async function getBlockedSites() {
  const { blockedSites } = await chrome.storage.local.get(['blockedSites']);
  return Array.isArray(blockedSites) ? blockedSites : [];
}

// ─── Helper: read user time limit ────────────────────────────────────────────
async function getTimeLimitSeconds() {
  const { userTimeLimitMinutes } = await chrome.storage.local.get(['userTimeLimitMinutes']);
  if (userTimeLimitMinutes && userTimeLimitMinutes >= 1) {
    return userTimeLimitMinutes * 60;
  }
  return DEFAULT_TIME_LIMIT_SEC;
}

// ─── Event Listeners (must be synchronous at top level for MV3) ─────────────

// 1. Tab switch
chrome.tabs.onActivated.addListener(async activeInfo => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    await checkSite(tab?.url || '');
  } catch (err) {
    console.debug('Driftless onActivated error:', err);
  }
});

// 2. Tab URL update / reload
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (tab.active && (changeInfo.url || changeInfo.status === 'complete')) {
    await checkSite(tab.url || '');
  }
});

// 3. Tab close
chrome.tabs.onRemoved.addListener(async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    await checkSite(tab?.url || '');
  } catch (err) {
    console.debug('Driftless onRemoved error:', err);
    await checkSite('');
  }
});

// 4. Chrome Alarm (wakes service worker even when idle)
chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name === ALARM_NAME) {
    await checkTimeLimit();
  }
  // Nightly backend sync
  if (alarm.name === SYNC_ALARM_NAME) {
    await syncToBackend();
    console.log('Driftless: nightly sync complete.');
  }
});

// Schedule the daily sync alarm on service worker startup
scheduleDailySync();

// 5. Storage change — handle timer reset from popup
chrome.storage.onChanged.addListener(async (changes, area) => {
  if (area !== 'local') return;

  // Timer reset
  if (changes.siteTimes) {
    const newTimes = changes.siteTimes.newValue || {};
    if (Object.keys(newTimes).length === 0) {
      if (timerTimeout) { clearTimeout(timerTimeout); timerTimeout = null; }
      await chrome.alarms.clear(ALARM_NAME);
      await chrome.storage.local.set({ notifiedSites: {} });
      const { currentActiveSite } = await chrome.storage.local.get(['currentActiveSite']);
      if (currentActiveSite) {
        const limitSec = await getTimeLimitSeconds();
        scheduleCheck(limitSec);
      }
    }
  }

  // If blockedSites changes while Focus Mode is ON, rebuild rules automatically
  if (changes.blockedSites) {
    const { focusModeActive } = await chrome.storage.local.get(['focusModeActive']);
    if (focusModeActive) {
      await enableFocusMode();
    }
  }
});

// 6. Notification click — dismiss
chrome.notifications.onClicked.addListener(id => chrome.notifications.clear(id));

// 7. Message listener (from popup)
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'SET_FOCUS_MODE') {
    const action = message.enabled ? enableFocusMode() : disableFocusMode();
    action
      .then(() => sendResponse({ success: true, focusModeActive: message.enabled }))
      .catch(err => { console.error('Focus Mode error:', err); sendResponse({ success: false, error: err.message }); });
    return true; // keep channel open for async response
  }

  if (message.type === 'REBUILD_FOCUS_RULES') {
    enableFocusMode()
      .then(() => sendResponse({ success: true }))
      .catch(err => { console.error('Rebuild rules error:', err); sendResponse({ success: false }); });
    return true;
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// CORE TRACKING LOGIC
// ─────────────────────────────────────────────────────────────────────────────
async function checkSite(url) {
  const trackedSites = await getBlockedSites();
  const matchedSite  = trackedSites.find(site => (url || '').includes(site)) || null;

  const data = await chrome.storage.local.get([
    'siteTimes', 'currentActiveSite', 'currentStartTime', 'notifiedSites'
  ]);
  const siteTimes     = data.siteTimes     || {};
  const activeSite    = data.currentActiveSite || null;
  const siteStartTime = data.currentStartTime  || 0;
  const notifiedSites = data.notifiedSites || {};

  // No change — nothing to do
  if (activeSite === matchedSite) return;

  // Commit time spent on the previous site
  if (activeSite && siteStartTime > 0) {
    const spent = Math.floor((Date.now() - siteStartTime) / 1000);
    if (spent > 0) siteTimes[activeSite] = (siteTimes[activeSite] || 0) + spent;
  }

  if (timerTimeout) { clearTimeout(timerTimeout); timerTimeout = null; }
  await chrome.alarms.clear(ALARM_NAME);

  if (matchedSite) {
    const now = Date.now();
    await chrome.storage.local.set({
      siteTimes, currentActiveSite: matchedSite, currentStartTime: now
    });
    console.log(`Driftless: tracking ${matchedSite}`);

    const limitSec      = await getTimeLimitSeconds();
    const alreadySpent  = siteTimes[matchedSite] || 0;
    const remaining     = limitSec - alreadySpent;

    if (remaining <= 0) {
      if (!notifiedSites[matchedSite]) {
        await sendNotification(matchedSite, alreadySpent);
        notifiedSites[matchedSite] = true;
        await chrome.storage.local.set({ notifiedSites });
      }
    } else {
      scheduleCheck(remaining);
    }
  } else {
    await chrome.storage.local.set({
      siteTimes, currentActiveSite: null, currentStartTime: null
    });
    console.log('Driftless: off tracked site, timer paused.');
  }
}

function scheduleCheck(seconds) {
  if (timerTimeout) { clearTimeout(timerTimeout); timerTimeout = null; }
  chrome.alarms.create(ALARM_NAME, { when: Date.now() + seconds * 1000 });
  timerTimeout = setTimeout(async () => { await checkTimeLimit(); }, seconds * 1000);
}

async function checkTimeLimit() {
  const data = await chrome.storage.local.get([
    'siteTimes', 'currentActiveSite', 'currentStartTime', 'notifiedSites'
  ]);
  const activeSite    = data.currentActiveSite;
  const siteStartTime = data.currentStartTime;
  const siteTimes     = data.siteTimes    || {};
  const notifiedSites = data.notifiedSites || {};

  if (!activeSite || !siteStartTime) return;

  const limitSec    = await getTimeLimitSeconds();
  const liveTime    = Math.floor((Date.now() - siteStartTime) / 1000);
  const totalSec    = (siteTimes[activeSite] || 0) + liveTime;

  if (totalSec >= limitSec) {
    if (!notifiedSites[activeSite]) {
      await sendNotification(activeSite, totalSec);
      notifiedSites[activeSite] = true;
      await chrome.storage.local.set({ notifiedSites });
    }
  } else {
    scheduleCheck(limitSec - totalSec);
  }
}

async function sendNotification(site, totalSeconds) {
  const name    = site.split('.')[0];
  const display = name.charAt(0).toUpperCase() + name.slice(1);
  const minutes = Math.floor(totalSeconds / 60) || 1;
  const timeText = `${minutes} minute${minutes > 1 ? 's' : ''}`;

  await chrome.storage.local.set({ limitExceededToday: true });
  console.log('Driftless: daily limit exceeded — streak at risk.');

  await chrome.notifications.create(`driftless-${site}-${Date.now()}`, {
    type:     'basic',
    iconUrl:  'icons/icon-128.png',
    title:    'Driftless — Focus Alert',
    message:  `You have spent ${timeText} on ${display}! Time to refocus.`,
    priority: 2
  }, id => {
    if (chrome.runtime.lastError) {
      console.error('Notification error:', chrome.runtime.lastError);
    } else {
      console.log('Notification sent:', id);
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// FOCUS MODE — declarativeNetRequest dynamic rules, built from blockedSites
// ─────────────────────────────────────────────────────────────────────────────
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

async function enableFocusMode() {
  const sites = await getBlockedSites();

  // Remove ALL existing dynamic rules first (clean slate)
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeIds = existing.map(r => r.id);

  const rulesToAdd = sites.map((domain, i) => buildBlockRule(FOCUS_RULE_BASE_ID + i, domain));

  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: removeIds,
    addRules:      rulesToAdd
  });
  console.log('Driftless Focus Mode ON — blocking:', sites.join(', '));
}

async function disableFocusMode() {
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeIds = existing.map(r => r.id);
  await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: removeIds, addRules: [] });
  console.log('Driftless Focus Mode OFF — all rules cleared.');
}