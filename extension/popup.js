// ─────────────────────────────────────────────────────────────────────────────
// DRIFTLESS EXTENSION POPUP
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE_URL = 'http://127.0.0.1:8000';

// ── Profile Defaults ─────────────────────────────────────────────────────────
const PROFILE_DEFAULTS = {
  student:      ['instagram.com', 'facebook.com', 'reddit.com', 'youtube.com'],
  influencer:   ['reddit.com', 'netflix.com'],
  professional: ['instagram.com', 'facebook.com', 'twitter.com', 'youtube.com'],
};

// ── Onboarding Screen ─────────────────────────────────────────────────────────
const onboardingScreen = document.getElementById('onboardingScreen');
const mainDashboard    = document.getElementById('mainDashboard');

function showDashboard() {
  if (onboardingScreen) onboardingScreen.style.display = 'none';
  if (mainDashboard)    mainDashboard.style.display    = 'block';
}

function showOnboarding() {
  if (onboardingScreen) onboardingScreen.style.display = 'flex';
  if (mainDashboard)    mainDashboard.style.display    = 'none';
}

// Profile button click: save profile + default blocked sites, then show dashboard
document.querySelectorAll('.profile-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const profile      = btn.dataset.profile;
    const blockedSites = PROFILE_DEFAULTS[profile] || [];
    chrome.storage.local.set({ userProfile: profile, blockedSites }, () => {
      // Notify background to rebuild focus rules with the new list
      chrome.runtime.sendMessage({ type: 'REBUILD_FOCUS_RULES' });
      showDashboard();
      initDashboard();
    });
  });
});

// Entry point: check for existing profile
chrome.storage.local.get(['userProfile'], result => {
  if (result.userProfile) {
    showDashboard();
    initDashboard();
  } else {
    showOnboarding();
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// DASHBOARD INITIALISATION — runs only after profile is confirmed
// ─────────────────────────────────────────────────────────────────────────────
function initDashboard() {
  initTimerDisplay();
  initResetBtn();
  initFocusMode();
  initDailyLimit();
  initManageSites();
  evaluateAndDisplayStreak();
  initApiToken();
  syncSettingsWithBackend();
}

// ─────────────────────────────────────────────────────────────────────────────
// TIMER DISPLAY (reads blockedSites dynamically)
// ─────────────────────────────────────────────────────────────────────────────
let timerInterval = null;

function updateTime() {
  chrome.storage.local.get(
    ['siteTimes', 'currentActiveSite', 'currentStartTime', 'blockedSites'],
    result => {
      let times    = result.siteTimes || {};
      const sites  = result.blockedSites || [];

      // Add live time for the currently active site
      if (result.currentActiveSite && result.currentStartTime) {
        const liveTime = Math.floor((Date.now() - result.currentStartTime) / 1000);
        times[result.currentActiveSite] = (times[result.currentActiveSite] || 0) + liveTime;
      }

      const timerEl = document.getElementById('timer');
      if (!timerEl) return;

      if (sites.length === 0) {
        timerEl.innerHTML =
          '<p style="justify-content:center;color:var(--text-muted);font-size:12px;">No sites tracked yet.</p>';
        return;
      }

      let html = '';
      sites.forEach(site => {
        const totalSeconds = times[site] || 0;
        const minutes  = Math.floor(totalSeconds / 60);
        const seconds  = totalSeconds % 60;
        const formatted = (minutes < 10 ? '0' + minutes : minutes) + ':' +
                          (seconds < 10 ? '0' + seconds : seconds);
        const name = site.split('.')[0];
        const displayName = name.charAt(0).toUpperCase() + name.slice(1);
        html += `<p><strong>${displayName}</strong><span class="time-val">${formatted}</span></p>`;
      });
      timerEl.innerHTML = html;
    }
  );
}

function initTimerDisplay() {
  if (timerInterval) clearInterval(timerInterval);
  updateTime();
  timerInterval = setInterval(updateTime, 1000);
}

// ─────────────────────────────────────────────────────────────────────────────
// RESET BUTTON
// ─────────────────────────────────────────────────────────────────────────────
function initResetBtn() {
  const resetBtn = document.getElementById('resetBtn');
  if (!resetBtn) return;
  resetBtn.addEventListener('click', () => {
    chrome.storage.local.set({
      siteTimes:        {},
      currentStartTime: Date.now(),
      notifiedSites:    {}
    }, () => {
      updateTime();
      console.log('Timer reset successful!');
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// FOCUS MODE TOGGLE (Synced bidirectionally with backend & background worker)
// ─────────────────────────────────────────────────────────────────────────────
function applyFocusUI(isActive) {
  const focusToggle = document.getElementById('focusToggle');
  const focusStatus = document.getElementById('focusStatus');
  if (focusToggle) focusToggle.checked = isActive;
  if (focusStatus) {
    if (isActive) {
      focusStatus.textContent = 'ON — Sites Blocked';
      focusStatus.classList.add('active');
    } else {
      focusStatus.textContent = 'OFF';
      focusStatus.classList.remove('active');
    }
  }
}

function initFocusMode() {
  const focusToggle = document.getElementById('focusToggle');
  if (!focusToggle) return;

  chrome.storage.local.get(['focusModeActive'], result => {
    applyFocusUI(result.focusModeActive === true);
  });

  focusToggle.addEventListener('change', async () => {
    const isActive = focusToggle.checked;
    await chrome.storage.local.set({ focusModeActive: isActive });
    applyFocusUI(isActive);

    // 1. Tell background service worker to update declarativeNetRequest rules
    chrome.runtime.sendMessage({ type: 'SET_FOCUS_MODE', enabled: isActive }, response => {
      if (chrome.runtime.lastError) {
        console.error('Focus Mode message error:', chrome.runtime.lastError.message);
      } else {
        console.log('Focus Mode response:', response);
      }
    });

    // 2. Sync to Django backend if API token is configured
    const { apiToken } = await chrome.storage.local.get(['apiToken']);
    if (apiToken) {
      try {
        await fetch(`${API_BASE_URL}/api/settings/`, {
          method: 'PATCH',
          headers: {
            'Content-Type':  'application/json',
            'Authorization': `Token ${apiToken}`,
          },
          body: JSON.stringify({ focus_mode_active: isActive }),
        });
        console.log('Driftless: focus mode state synced to backend.');
      } catch (err) {
        console.warn('Driftless: could not sync focus mode to backend:', err);
      }
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// DAILY TIME LIMIT (Synced bidirectionally with backend)
// ─────────────────────────────────────────────────────────────────────────────
function initDailyLimit() {
  const limitInput   = document.getElementById('limitInput');
  const saveLimitBtn = document.getElementById('saveLimitBtn');
  const limitSaveMsg = document.getElementById('limitSaveMsg');
  if (!limitInput || !saveLimitBtn) return;

  chrome.storage.local.get(['userTimeLimitMinutes'], result => {
    if (result.userTimeLimitMinutes) limitInput.value = result.userTimeLimitMinutes;
  });

  function showLimitMsg(text, isError = false) {
    if (!limitSaveMsg) return;
    limitSaveMsg.textContent = text;
    limitSaveMsg.style.color = isError ? '#FF453A' : '#32D74B';
    limitSaveMsg.style.opacity = '1';
    setTimeout(() => { limitSaveMsg.style.opacity = '0'; }, 2500);
  }

  saveLimitBtn.addEventListener('click', async () => {
    const raw = parseInt(limitInput.value, 10);
    if (!raw || raw < 1 || raw > 1440) {
      showLimitMsg('Enter a value between 1 and 1440 mins.', true);
      return;
    }

    await chrome.storage.local.set({ userTimeLimitMinutes: raw });
    showLimitMsg(`✅ Limit set to ${raw} min${raw > 1 ? 's' : ''}!`);

    // Sync to backend if token is present
    const { apiToken } = await chrome.storage.local.get(['apiToken']);
    if (apiToken) {
      try {
        await fetch(`${API_BASE_URL}/api/settings/`, {
          method: 'PATCH',
          headers: {
            'Content-Type':  'application/json',
            'Authorization': `Token ${apiToken}`,
          },
          body: JSON.stringify({ daily_limit_minutes: raw }),
        });
        console.log('Driftless: daily limit synced to backend.');
      } catch (err) {
        console.warn('Driftless: could not sync daily limit to backend:', err);
      }
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// MANAGE SITES
// ─────────────────────────────────────────────────────────────────────────────
function initManageSites() {
  const newSiteInput = document.getElementById('newSiteInput');
  const addSiteBtn   = document.getElementById('addSiteBtn');
  const siteMsg      = document.getElementById('siteMsg');
  if (!newSiteInput || !addSiteBtn) return;

  function showSiteMsg(text, isError = false) {
    if (!siteMsg) return;
    siteMsg.textContent = text;
    siteMsg.style.color = isError ? '#FF453A' : '#32D74B';
    siteMsg.style.opacity = '1';
    setTimeout(() => { siteMsg.style.opacity = '0'; }, 2500);
  }

  function renderSiteList(sites) {
    const list = document.getElementById('siteList');
    if (!list) return;

    if (!sites || sites.length === 0) {
      list.innerHTML = '<div class="sites-empty">No sites added yet.</div>';
      return;
    }
    list.innerHTML = sites.map((site, i) => `
      <div class="site-row">
        <span class="site-domain">${site}</span>
        <button class="site-delete-btn" data-index="${i}" title="Remove ${site}">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14H6L5 6"/>
            <path d="M10 11v6M14 11v6"/>
            <path d="M9 6V4h6v2"/>
          </svg>
        </button>
      </div>
    `).join('');

    // Delete button handlers
    list.querySelectorAll('.site-delete-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.index, 10);
        chrome.storage.local.get(['blockedSites'], res => {
          const updated = (res.blockedSites || []).filter((_, i) => i !== idx);
          chrome.storage.local.set({ blockedSites: updated }, () => {
            renderSiteList(updated);
            // Sync focus rules if focus mode is currently ON
            chrome.storage.local.get(['focusModeActive'], r => {
              if (r.focusModeActive) {
                chrome.runtime.sendMessage({ type: 'REBUILD_FOCUS_RULES' });
              }
            });
            showSiteMsg('Site removed.');
          });
        });
      });
    });
  }

  // Initial render
  chrome.storage.local.get(['blockedSites'], result => {
    renderSiteList(result.blockedSites || []);
  });

  // Add site button
  addSiteBtn.addEventListener('click', () => addSite());
  newSiteInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') addSite();
  });

  function normalizeDomain(raw) {
    return raw.trim().toLowerCase()
      .replace(/^https?:\/\//i, '')
      .replace(/^www\./i, '')
      .split('/')[0];
  }

  function addSite() {
    const raw = newSiteInput.value;
    const domain = normalizeDomain(raw);
    if (!domain || !domain.includes('.')) {
      showSiteMsg('Enter a valid domain (e.g. twitter.com)', true);
      return;
    }
    chrome.storage.local.get(['blockedSites'], res => {
      const current = res.blockedSites || [];
      if (current.includes(domain)) {
        showSiteMsg(`${domain} is already in your list.`, true);
        return;
      }
      const updated = [...current, domain];
      chrome.storage.local.set({ blockedSites: updated }, () => {
        newSiteInput.value = '';
        renderSiteList(updated);
        // Sync focus rules if focus mode is ON
        chrome.storage.local.get(['focusModeActive'], r => {
          if (r.focusModeActive) {
            chrome.runtime.sendMessage({ type: 'REBUILD_FOCUS_RULES' });
          }
        });
        showSiteMsg(`✅ ${domain} added!`);
      });
    });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// FOCUS STREAK & SYNC
// ─────────────────────────────────────────────────────────────────────────────
function renderStreak(streak) {
  const el = document.getElementById('streakBadge');
  if (!el) return;
  const count = parseInt(streak, 10) || 0;
  if (count === 0) {
    el.textContent = '— No streak yet';
    el.classList.remove('streak-active');
  } else {
    el.textContent = `🔥 ${count} day streak`;
    el.classList.add('streak-active');
  }
}

async function evaluateAndDisplayStreak() {
  const { apiToken, streakDays } = await chrome.storage.local.get(['apiToken', 'streakDays']);

  if (apiToken) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/settings/`, {
        headers: { 'Authorization': `Token ${apiToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        const streak = data.streak_days !== undefined ? data.streak_days : (streakDays || 0);
        await chrome.storage.local.set({ streakDays: streak });
        renderStreak(streak);
        return;
      }
    } catch (err) {
      console.warn('Driftless: evaluateAndDisplayStreak network error:', err);
    }
  }

  // Fallback to local storage
  renderStreak(streakDays || 0);
}

// ─────────────────────────────────────────────────────────────────────────────
// SETTINGS SYNC WITH BACKEND (Focus mode, daily limits, streaks)
// ─────────────────────────────────────────────────────────────────────────────
async function syncSettingsWithBackend() {
  const { apiToken } = await chrome.storage.local.get(['apiToken']);
  if (!apiToken) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/settings/`, {
      headers: { 'Authorization': `Token ${apiToken}` }
    });
    if (!res.ok) return;

    const data = await res.json();

    // 1. Sync Focus Mode
    if (data.focus_mode_active !== undefined) {
      const { focusModeActive } = await chrome.storage.local.get(['focusModeActive']);
      if (focusModeActive !== data.focus_mode_active) {
        await chrome.storage.local.set({ focusModeActive: data.focus_mode_active });
        applyFocusUI(data.focus_mode_active);
        chrome.runtime.sendMessage({
          type: 'SET_FOCUS_MODE',
          enabled: data.focus_mode_active
        });
      }
    }

    // 2. Sync Daily Time Limit
    if (data.daily_limit_minutes !== undefined) {
      const limitInput = document.getElementById('limitInput');
      if (limitInput) limitInput.value = data.daily_limit_minutes;
      await chrome.storage.local.set({ userTimeLimitMinutes: data.daily_limit_minutes });
    }

    // 3. Sync Streak Days
    if (data.streak_days !== undefined) {
      await chrome.storage.local.set({ streakDays: data.streak_days });
      renderStreak(data.streak_days);
    }
    console.log('Driftless: settings synced successfully with backend.');
  } catch (err) {
    console.debug('Driftless: settings sync error:', err);
  }
}

// ───────────────────────────────────────────────────────────────────────────────
// API TOKEN — save & load from chrome.storage.local
// ───────────────────────────────────────────────────────────────────────────────
function initApiToken() {
  const input   = document.getElementById('apiTokenInput');
  const saveBtn = document.getElementById('saveTokenBtn');
  const saveMsg = document.getElementById('tokenSaveMsg');
  if (!input || !saveBtn) return;

  /** Show the tail of the stored token, masked */
  function maskToken(token) {
    if (!token || token.length < 9) return token || '';
    return '•'.repeat(token.length - 8) + token.slice(-8);
  }

  function showTokenMsg(text, isError = false) {
    if (!saveMsg) return;
    saveMsg.textContent = text;
    saveMsg.style.color = isError ? '#FF453A' : '#4DA6FF';
    saveMsg.style.opacity = '1';
    setTimeout(() => { saveMsg.style.opacity = '0'; }, 3000);
  }

  // Pre-populate with masked stored token
  chrome.storage.local.get(['apiToken'], result => {
    if (result.apiToken) {
      input.value = maskToken(result.apiToken);
      input.dataset.saved = 'true';
    }
  });

  // Clear masked placeholder on focus so user can paste a fresh token
  input.addEventListener('focus', () => {
    if (input.dataset.saved === 'true') {
      input.value = '';
      input.dataset.saved = 'false';
    }
  });

  saveBtn.addEventListener('click', () => {
    const raw = input.value.trim();

    if (!raw || raw.length < 10) {
      showTokenMsg('⚠️ Token looks too short. Paste the full token from the dashboard.', true);
      return;
    }

    // If the value is still showing masked chars, user didn't change it — skip
    if (raw.includes('•')) {
      showTokenMsg('✅ Token already saved.', false);
      return;
    }

    chrome.storage.local.set({ apiToken: raw }, async () => {
      input.value = maskToken(raw);
      input.dataset.saved = 'true';
      showTokenMsg('✅ Token saved! Syncing immediately…');
      console.log('Driftless: API token saved.');

      // Immediate bidirectional sync
      await syncSettingsWithBackend();
      await evaluateAndDisplayStreak();
      chrome.runtime.sendMessage({ type: 'TRIGGER_SYNC' });
    });
  });
}