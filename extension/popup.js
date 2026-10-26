// ─────────────────────────────────────────────────────────────────────────────
// DRIFTLESS EXTENSION POPUP CONTROLLER
// Bidirectional Sync, Per-Site Limits, Focus Timer, Confirmation Dialogs
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_SERVER_URL = 'http://127.0.0.1:8000';

let timerInterval = null;

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initial trigger sync to get latest numbers immediately on open
  chrome.runtime.sendMessage({ type: 'TRIGGER_SYNC' }, () => {
    loadPopupState();
  });

  setupEventListeners();
  loadPopupState();
  startLiveTimerTicker();
});

async function getServerUrl() {
  const { serverUrl } = await chrome.storage.local.get(['serverUrl']);
  return (serverUrl && serverUrl.trim()) ? serverUrl.trim().replace(/\/+$/, '') : DEFAULT_SERVER_URL;
}

// ── Load & Render Popup State ────────────────────────────────────────────────

async function loadPopupState() {
  const {
    apiToken,
    serverUrl,
    streakDays = 0,
    focusModeActive = false,
    focusTimerActive = false,
    focusTimerEndTime = 0,
    siteTimes = {},
    siteLimits = {},
    lastSyncedTime
  } = await chrome.storage.local.get([
    'apiToken', 'serverUrl', 'streakDays', 'focusModeActive',
    'focusTimerActive', 'focusTimerEndTime', 'siteTimes', 'siteLimits', 'lastSyncedTime'
  ]);

  // Server & Token
  const server = serverUrl || DEFAULT_SERVER_URL;
  const sDisplay = document.getElementById('serverDisplay');
  if (sDisplay) sDisplay.textContent = server;
  
  const tokenInput = document.getElementById('apiTokenInput');
  if (tokenInput && apiToken) {
    tokenInput.value = apiToken.slice(0, 8) + '••••••••';
  }

  const syncStatus = document.getElementById('syncStatusText');
  if (syncStatus) {
    syncStatus.textContent = apiToken ? 'Connected' : 'Not Linked';
    syncStatus.style.color = apiToken ? 'var(--prod)' : 'var(--ent)';
  }

  // Streak (strictly matches server)
  const streakCount = document.getElementById('streakCountText');
  if (streakCount) {
    streakCount.textContent = `${streakDays} Day${streakDays === 1 ? '' : 's'}`;
  }

  // Focus Mode Toggle
  const focusToggle = document.getElementById('focusToggle');
  if (focusToggle) focusToggle.checked = focusModeActive;

  // Focus Timer Countdown
  renderFocusTimerCountdown(focusTimerActive, focusTimerEndTime);

  // Per-Site Limits & Trackers
  renderSiteList(siteTimes, siteLimits);

  // Synced status dot
  renderSyncTime(lastSyncedTime);
}

function renderSyncTime(lastSyncedTime) {
  const label = document.getElementById('lastSyncedLabel');
  if (!label) return;

  if (!lastSyncedTime) {
    label.textContent = 'Synced · just now';
    return;
  }

  const diffSec = Math.floor((Date.now() - lastSyncedTime) / 1000);
  if (diffSec < 60) {
    label.textContent = 'Synced · just now';
  } else {
    const mins = Math.floor(diffSec / 60);
    label.textContent = `Synced · ${mins}m ago`;
  }
}

// ── Render Per-Site List ─────────────────────────────────────────────────────

function renderSiteList(siteTimes, siteLimits) {
  const container = document.getElementById('siteListContainer');
  if (!container) return;

  // Merge domains from siteLimits and active siteTimes
  const allDomains = new Set([
    ...Object.keys(siteLimits),
    ...Object.keys(siteTimes).filter(d => siteTimes[d] > 0)
  ]);

  if (allDomains.size === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:16px 8px; font-size:12px; color:var(--ink-muted);">
        No sites tracked yet today.<br>Browse normally to start tracking.
      </div>
    `;
    return;
  }

  let html = '';
  allDomains.forEach(domain => {
    const seconds = siteTimes[domain] || 0;
    const usedMins = Math.floor(seconds / 60);
    const limitObj = siteLimits[domain];
    const limitMins = limitObj ? limitObj.daily_limit_minutes : null;

    let timeText = `${usedMins}m`;
    let pct = 0;
    let barColor = 'var(--pri)';

    if (limitMins && limitMins > 0) {
      pct = Math.min(Math.round((usedMins / limitMins) * 100), 100);
      timeText = `${usedMins}m / ${limitMins}m`;
      if (pct >= 80) barColor = 'var(--ent)';
      else if (pct >= 60) barColor = 'var(--soc)';
    } else {
      timeText = `${usedMins}m (no limit)`;
      pct = Math.min(usedMins * 2, 100);
    }

    // Determine category dot
    let dotClass = 'other';
    if (['github.com', 'stackoverflow.com', 'leetcode.com', 'notion.so', 'coursera.org'].includes(domain) || domain.endsWith('.edu')) {
      dotClass = 'productive';
    } else if (['instagram.com', 'facebook.com', 'reddit.com', 'twitter.com', 'x.com'].includes(domain)) {
      dotClass = 'social';
    } else if (['youtube.com', 'netflix.com', 'twitch.tv', 'spotify.com'].includes(domain)) {
      dotClass = 'entertainment';
    }

    html += `
      <div class="site-item">
        <div class="site-item-top">
          <div class="site-name">
            <span class="site-dot ${dotClass}"></span>
            <span>${domain}</span>
          </div>
          <span class="site-timer">${timeText}</span>
        </div>
        <div class="mini-bar">
          <div class="mini-bar-inner" style="width:${pct}%; background:${barColor};"></div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

// ── Focus Timer ──────────────────────────────────────────────────────────────

function renderFocusTimerCountdown(isActive, endTime) {
  const cd = document.getElementById('timerCountdown');
  if (!cd) return;

  if (!isActive || !endTime || Date.now() >= endTime) {
    cd.textContent = '';
    document.querySelectorAll('.timer-btn').forEach(b => b.classList.remove('active'));
    return;
  }

  const remainingSec = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
  const m = String(Math.floor(remainingSec / 60)).padStart(2, '0');
  const s = String(remainingSec % 60).padStart(2, '0');
  cd.textContent = `⏱ ${m}:${s}`;
}

function startLiveTimerTicker() {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(async () => {
    const { focusTimerActive, focusTimerEndTime } = await chrome.storage.local.get([
      'focusTimerActive', 'focusTimerEndTime'
    ]);
    renderFocusTimerCountdown(focusTimerActive, focusTimerEndTime);
  }, 1000);
}

// ── Event Handlers ───────────────────────────────────────────────────────────

function setupEventListeners() {
  // Focus Mode Toggle
  const focusToggle = document.getElementById('focusToggle');
  if (focusToggle) {
    focusToggle.addEventListener('change', async e => {
      const isChecked = e.target.checked;
      await chrome.storage.local.set({ focusModeActive: isChecked });

      // Sync to backend if token present
      const { apiToken } = await chrome.storage.local.get(['apiToken']);
      if (apiToken) {
        const serverUrl = await getServerUrl();
        fetch(`${serverUrl}/api/settings/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${apiToken}`
          },
          body: JSON.stringify({ focus_mode_active: isChecked })
        }).catch(err => console.debug('Focus toggle sync error:', err));
      }

      chrome.runtime.sendMessage({
        type: isChecked ? 'SET_FOCUS_MODE' : 'SET_FOCUS_MODE',
        enabled: isChecked
      });
    });
  }

  // Focus Timer Preset Buttons (25, 45, 60 mins)
  document.querySelectorAll('.timer-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const mins = parseInt(btn.dataset.min, 10);
      document.querySelectorAll('.timer-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      chrome.runtime.sendMessage({
        type: 'START_FOCUS_TIMER',
        durationMinutes: mins
      }, () => {
        loadPopupState();
      });
    });
  });

  // Add Site Limit
  const addBtn = document.getElementById('addLimitBtn');
  if (addBtn) {
    addBtn.addEventListener('click', async () => {
      const domainInput = document.getElementById('addDomainInput');
      const minsInput   = document.getElementById('addMinsInput');

      let domain = (domainInput.value || '').trim().toLowerCase();
      domain = domain.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
      const limitMins = parseInt(minsInput.value, 10);

      if (!domain || !domain.includes('.')) {
        alert('Please enter a valid domain name (e.g. reddit.com)');
        return;
      }
      if (!limitMins || limitMins < 1 || limitMins > 1440) {
        alert('Please enter a limit between 1 and 1440 minutes.');
        return;
      }

      const { siteLimits = {}, apiToken } = await chrome.storage.local.get(['siteLimits', 'apiToken']);
      siteLimits[domain] = { domain, daily_limit_minutes: limitMins, enabled: true };
      await chrome.storage.local.set({ siteLimits });

      // Sync to backend if token present
      if (apiToken) {
        const serverUrl = await getServerUrl();
        fetch(`${serverUrl}/api/limits/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${apiToken}`
          },
          body: JSON.stringify({ domain, daily_limit_minutes: limitMins, enabled: true })
        }).catch(e => console.debug('Add limit sync error:', e));
      }

      domainInput.value = '';
      minsInput.value = '';
      loadPopupState();
    });
  }

  // Save Token
  const saveTokenBtn = document.getElementById('saveTokenBtn');
  if (saveTokenBtn) {
    saveTokenBtn.addEventListener('click', async () => {
      const input = document.getElementById('apiTokenInput');
      const token = (input.value || '').trim();
      if (!token || token.includes('••••')) return;

      await chrome.storage.local.set({ apiToken: token });
      saveTokenBtn.textContent = '✓ Saved';
      saveTokenBtn.style.background = 'var(--prod)';
      setTimeout(() => {
        saveTokenBtn.textContent = 'Save';
        saveTokenBtn.style.background = 'var(--ink)';
      }, 2000);

      chrome.runtime.sendMessage({ type: 'TRIGGER_SYNC' }, () => {
        loadPopupState();
      });
    });
  }

  // Reset All Timers Confirmation Dialog
  const resetBtn = document.getElementById('resetTimersBtn');
  const overlay = document.getElementById('confirmOverlay');
  const cancelBtn = document.getElementById('cancelResetBtn');
  const confirmBtn = document.getElementById('confirmResetBtn');

  if (resetBtn && overlay) {
    resetBtn.addEventListener('click', () => { overlay.style.display = 'flex'; });
    cancelBtn.addEventListener('click', () => { overlay.style.display = 'none'; });
    confirmBtn.addEventListener('click', () => {
      overlay.style.display = 'none';
      chrome.runtime.sendMessage({ type: 'RESET_ALL_TIMERS' }, () => {
        loadPopupState();
      });
    });
  }
}