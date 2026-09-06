// ─────────────────────────────────────────────────────────────────────────────
// PROFILE DEFAULTS
// ─────────────────────────────────────────────────────────────────────────────
const PROFILE_DEFAULTS = {
  student:      ['instagram.com', 'facebook.com', 'reddit.com', 'youtube.com'],
  influencer:   ['reddit.com', 'netflix.com'],
  professional: ['instagram.com', 'facebook.com', 'twitter.com', 'youtube.com'],
};

// ─────────────────────────────────────────────────────────────────────────────
// ONBOARDING — show or hide based on stored profile
// ─────────────────────────────────────────────────────────────────────────────
const onboardingScreen = document.getElementById('onboardingScreen');
const mainDashboard    = document.getElementById('mainDashboard');

function showDashboard() {
  onboardingScreen.style.display = 'none';
  mainDashboard.style.display = 'block';
}

function showOnboarding() {
  onboardingScreen.style.display = 'flex';
  mainDashboard.style.display    = 'none';
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

      if (sites.length === 0) {
        document.getElementById('timer').innerHTML =
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
      document.getElementById('timer').innerHTML = html;
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
  document.getElementById('resetBtn').addEventListener('click', () => {
    chrome.storage.local.set({
      siteTimes:    {},
      currentStartTime: Date.now(),
      notifiedSites: {}
    }, () => {
      updateTime();
      console.log('Timer reset successful!');
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// FOCUS MODE TOGGLE
// ─────────────────────────────────────────────────────────────────────────────
function initFocusMode() {
  const focusToggle = document.getElementById('focusToggle');
  const focusStatus = document.getElementById('focusStatus');

  function applyFocusUI(isActive) {
    focusToggle.checked = isActive;
    if (isActive) {
      focusStatus.textContent = 'ON — Sites Blocked';
      focusStatus.classList.add('active');
    } else {
      focusStatus.textContent = 'OFF';
      focusStatus.classList.remove('active');
    }
  }

  chrome.storage.local.get(['focusModeActive'], result => {
    applyFocusUI(result.focusModeActive === true);
  });

  focusToggle.addEventListener('change', () => {
    const isActive = focusToggle.checked;
    chrome.storage.local.set({ focusModeActive: isActive });
    applyFocusUI(isActive);
    chrome.runtime.sendMessage({ type: 'SET_FOCUS_MODE', enabled: isActive }, response => {
      if (chrome.runtime.lastError) {
        console.error('Focus Mode message error:', chrome.runtime.lastError.message);
      } else {
        console.log('Focus Mode response:', response);
      }
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// DAILY TIME LIMIT
// ─────────────────────────────────────────────────────────────────────────────
function initDailyLimit() {
  const limitInput   = document.getElementById('limitInput');
  const saveLimitBtn = document.getElementById('saveLimitBtn');
  const limitSaveMsg = document.getElementById('limitSaveMsg');

  chrome.storage.local.get(['userTimeLimitMinutes'], result => {
    if (result.userTimeLimitMinutes) limitInput.value = result.userTimeLimitMinutes;
  });

  function showLimitMsg(text, isError = false) {
    limitSaveMsg.textContent = text;
    limitSaveMsg.style.color = isError ? '#FF453A' : '#32D74B';
    limitSaveMsg.style.opacity = '1';
    setTimeout(() => { limitSaveMsg.style.opacity = '0'; }, 2500);
  }

  saveLimitBtn.addEventListener('click', () => {
    const raw = parseInt(limitInput.value, 10);
    if (!raw || raw < 1 || raw > 1440) {
      showLimitMsg('Enter a value between 1 and 1440 mins.', true);
      return;
    }
    chrome.storage.local.set({ userTimeLimitMinutes: raw }, () => {
      showLimitMsg(`✅ Limit set to ${raw} min${raw > 1 ? 's' : ''}!`);
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// MANAGE SITES
// ─────────────────────────────────────────────────────────────────────────────
function initManageSites() {
  const newSiteInput = document.getElementById('newSiteInput');
  const addSiteBtn   = document.getElementById('addSiteBtn');
  const siteMsg      = document.getElementById('siteMsg');

  function showSiteMsg(text, isError = false) {
    siteMsg.textContent = text;
    siteMsg.style.color = isError ? '#FF453A' : '#32D74B';
    siteMsg.style.opacity = '1';
    setTimeout(() => { siteMsg.style.opacity = '0'; }, 2500);
  }

  function renderSiteList(sites) {
    const list = document.getElementById('siteList');
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
// FOCUS STREAK
// ─────────────────────────────────────────────────────────────────────────────
function todayUTC() {
  return new Date().toISOString().slice(0, 10);
}

function renderStreak(streak) {
  const el = document.getElementById('streakBadge');
  if (!el) return;
  if (streak === 0) {
    el.textContent = '— No streak yet';
    el.classList.remove('streak-active');
  } else {
    el.textContent = `🔥 ${streak} day streak`;
    el.classList.add('streak-active');
  }
}

async function evaluateAndDisplayStreak() {
  const data = await chrome.storage.local.get([
    'currentStreak', 'lastActiveDate', 'limitExceededToday'
  ]);
  let streak       = data.currentStreak   ?? 0;
  const lastDate   = data.lastActiveDate  ?? null;
  const failed     = data.limitExceededToday === true;
  const today      = todayUTC();

  if (lastDate === null) {
    await chrome.storage.local.set({ currentStreak: 0, lastActiveDate: today, limitExceededToday: false });
    renderStreak(0);
    return;
  }
  if (lastDate === today) {
    renderStreak(streak);
    return;
  }
  const yesterday    = new Date(Date.now() - 86_400_000).toISOString().slice(0, 10);
  const wasYesterday = (lastDate === yesterday);
  if (wasYesterday && !failed) {
    streak += 1;
  } else {
    streak = 0;
  }
  await chrome.storage.local.set({ currentStreak: streak, lastActiveDate: today, limitExceededToday: false });
  renderStreak(streak);
}