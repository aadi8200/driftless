// ─────────────────────────────────────────────────────────────────────────────
// DRIFTLESS EXTENSION POPUP CONTROLLER
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_SERVER_URL = 'https://driftless-g5cb.onrender.com';

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

let liveTickerInterval = null;
let currentCustomDomain = null;
let selectedPersona = 'Student';

// ── Pomodoro Timer State & UI ────────────────────────────────────────────────
let pomodoroLocalState = {
  mode: 'work', // 'work' | 'rest'
  state: 'idle', // 'idle' | 'running' | 'paused'
  remainingSec: 1500, // 25m focus = 1500s, 5m rest = 300s
  startTime: null,
  endTime: null
};

function formatPomoTime(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds || 0));
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

async function renderPomodoroUI() {
  const data = await chrome.storage.local.get([
    'pomodoroMode',
    'pomodoroState',
    'pomodoroRemainingSec',
    'pomodoroStartTime',
    'pomodoroEndTime'
  ]);

  const mode = data.pomodoroMode || 'work';
  let state = data.pomodoroState || 'idle';
  let remaining = data.pomodoroRemainingSec !== undefined ? data.pomodoroRemainingSec : (mode === 'rest' ? 300 : 1500);
  const endTime = data.pomodoroEndTime || null;
  const startTime = data.pomodoroStartTime || null;

  if (state === 'running' && endTime) {
    const now = Date.now();
    const diff = Math.max(0, Math.round((endTime - now) / 1000));
    if (diff <= 0) {
      // Alarm in background worker will handle phase transition
      remaining = 0;
    } else {
      remaining = diff;
    }
  }

  pomodoroLocalState = { mode, state, remainingSec: remaining, startTime, endTime };

  const badge = document.getElementById('pomoPhaseBadge');
  if (badge) {
    if (mode === 'work') {
      badge.textContent = state === 'running' ? 'Focus (25m)' : 'Focus';
      badge.classList.remove('break');
    } else {
      badge.textContent = state === 'running' ? 'Rest (5m)' : 'Rest';
      badge.classList.add('break');
    }
  }

  const display = document.getElementById('pomoDisplay');
  if (display) display.textContent = formatPomoTime(remaining);

  const startBtn = document.getElementById('pomoStartBtn');
  if (startBtn) {
    if (state === 'running') {
      startBtn.textContent = 'Running';
      startBtn.style.opacity = '0.85';
      startBtn.style.background = 'var(--grad)';
    } else {
      startBtn.textContent = 'Start';
      startBtn.style.opacity = '1';
      startBtn.style.background = 'var(--grad)';
    }
  }
}

async function startPomodoroSession() {
  const mode = 'work';
  const durationSec = 1500; // 25 minutes
  const now = Date.now();
  const endTime = now + (durationSec * 1000);

  await chrome.storage.local.set({
    pomodoroMode: mode,
    pomodoroState: 'running',
    pomodoroStartTime: now,
    pomodoroEndTime: endTime,
    pomodoroRemainingSec: durationSec
  });

  chrome.runtime.sendMessage({
    type: 'START_POMODORO',
    mode,
    startTime: now,
    endTime,
    remainingSec: durationSec
  });

  await renderPomodoroUI();
}

async function stopPomodoroSession() {
  await chrome.storage.local.set({
    pomodoroMode: 'work',
    pomodoroState: 'idle',
    pomodoroStartTime: null,
    pomodoroEndTime: null,
    pomodoroRemainingSec: 1500
  });

  chrome.runtime.sendMessage({ type: 'STOP_POMODORO' });
  await renderPomodoroUI();
}

document.addEventListener('DOMContentLoaded', async () => {
  await initTheme();
  await checkOnboardingState();
  setupEventListeners();

  // Trigger sync on popup open to ensure server ground truth
  chrome.runtime.sendMessage({ type: 'TRIGGER_SYNC' }, () => {
    loadPopupState();
  });

  loadPopupState();
  startLiveTicker();
});

// ── Theme Management ─────────────────────────────────────────────────────────

async function initTheme() {
  const { theme = 'light' } = await chrome.storage.local.get(['theme']);
  applyTheme(theme);

  const toggle1 = document.getElementById('popupThemeToggle');
  const toggle2 = document.getElementById('onboardThemeToggle');

  const handler = async () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    await chrome.storage.local.set({ theme: next });
  };

  if (toggle1) toggle1.addEventListener('click', handler);
  if (toggle2) toggle2.addEventListener('click', handler);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
}

// ── Persona Seeding & Onboarding ─────────────────────────────────────────────

// Helper to determine all default domains across all personas
function getAllDefaultDomains() {
  const dist = new Set();
  const prod = new Set();
  Object.values(PERSONA_DEFAULTS).forEach(p => {
    p.distracting.forEach(d => dist.add(d));
    p.productive.forEach(d => prod.add(d));
  });
  return { dist, prod };
}

async function seedPersonaDefaults(personaName, force = false) {
  const data = await chrome.storage.local.get([
    'defaultsSeeded',
    'persona',
    'distractingSites',
    'blockedSites',
    'productiveSites',
    'allowedSites',
    'apiToken'
  ]);

  const pKey = getPersonaKey(personaName || data.persona || 'Student');
  const pDef = PERSONA_DEFAULTS[pKey] || PERSONA_DEFAULTS.Student;

  const existingDist = (data.distractingSites && data.distractingSites.length > 0)
    ? data.distractingSites
    : (data.blockedSites && data.blockedSites.length > 0 ? data.blockedSites : []);
  const existingProd = (data.productiveSites && data.productiveSites.length > 0)
    ? data.productiveSites
    : (data.allowedSites && data.allowedSites.length > 0 ? data.allowedSites : []);

  // Rule 6: Sites the user added themselves must never be deleted when persona changes.
  // We extract any domain the user manually added (not part of all default persona lists)
  const { dist: allDefaultDist, prod: allDefaultProd } = getAllDefaultDomains();
  const userAddedDist = existingDist.filter(d => !allDefaultDist.has(d));
  const userAddedProd = existingProd.filter(d => !allDefaultProd.has(d));

  // Merge the chosen persona's recommendations with the user's custom added sites
  const distractingSites = Array.from(new Set([...pDef.distracting, ...userAddedDist]));
  const productiveSites = Array.from(new Set([...pDef.productive, ...userAddedProd]));

  const scheduleStart = data.scheduleStart || pDef.scheduleStart || '20:00';
  const scheduleEnd = data.scheduleEnd || pDef.scheduleEnd || '22:30';
  const scheduleEnabled = data.scheduleEnabled !== undefined ? data.scheduleEnabled : false;

  // Turn off Block Shorts and Reels if persona is not Student
  let blockShortsReels = data.blockShortsReels;
  if (pKey !== 'Student') {
    blockShortsReels = false;
  }

  await chrome.storage.local.set({
    defaultsSeeded: true,
    persona: pKey,
    distractingSites,
    blockedSites: distractingSites,
    productiveSites,
    allowedSites: productiveSites,
    scheduleStart,
    scheduleEnd,
    scheduleEnabled,
    blockShortsReels
  });

  // Notify background to update schedule
  chrome.runtime.sendMessage({
    type: 'UPDATE_SCHEDULE',
    scheduleStart,
    scheduleEnd,
    scheduleEnabled
  });

  // Notify background to update DNR rules and internal tracking immediately
  chrome.runtime.sendMessage({
    type: 'UPDATE_SITE_LISTS',
    distractingSites,
    productiveSites
  });

  if (pKey !== 'Student') {
    chrome.runtime.sendMessage({
      type: 'TOGGLE_SHORTS_REELS',
      enabled: false
    });
  }

  // If token is linked, sync persona and lists to backend settings immediately
  if (data.apiToken) {
    const serverUrl = await getServerUrl();
    fetch(`${serverUrl}/api/settings/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${data.apiToken}`
      },
      body: JSON.stringify({
        persona: pKey.toLowerCase(),
        blocked_sites: distractingSites.join('\n'),
        allowed_sites: productiveSites.join('\n')
      })
    }).catch(() => {});
  }

  return true;
}

async function checkOnboardingState() {
  const {
    apiToken,
    persona
  } = await chrome.storage.local.get(['apiToken', 'persona']);

  const onboardingView = document.getElementById('onboardingView');
  const mainView = document.getElementById('mainView');

  // If user has a token, query backend summary to see if the user already has a persona from signup
  if (apiToken) {
    try {
      const serverUrl = await getServerUrl();
      const res = await fetch(`${serverUrl}/api/summary/`, {
        headers: { 'Authorization': `Token ${apiToken}` }
      });
      if (res.ok) {
        const summary = await res.json();
        if (summary.user && summary.user.persona) {
          const websitePersona = getPersonaKey(summary.user.persona);
          // If extension doesn't have a persona or website has a persona, prioritize website persona
          if (!persona || persona !== websitePersona) {
            await seedPersonaDefaults(websitePersona, false);
          }
          if (onboardingView) onboardingView.style.display = 'none';
          if (mainView) mainView.style.display = 'block';
          return;
        }
      }
    } catch (e) {
      console.debug('Failed to fetch user persona from backend:', e);
    }
  }

  // If no persona is saved at all, show the Welcome screen inside popup
  if (!persona) {
    if (onboardingView) onboardingView.style.display = 'flex';
    if (mainView) mainView.style.display = 'none';
    setupOnboardingFlow();
  } else {
    if (onboardingView) onboardingView.style.display = 'none';
    if (mainView) mainView.style.display = 'block';
  }
}

function setupOnboardingFlow() {
  const welcomeCard = document.getElementById('onboardWelcome');
  const welcomeNextBtn = document.getElementById('onboardWelcomeNext');
  const step1 = document.getElementById('onboardStep1');
  const step2 = document.getElementById('onboardStep2');
  const step1Next = document.getElementById('onboardStep1Next');
  const backBtn = document.getElementById('onboardBackBtn');
  const finishBtn = document.getElementById('onboardFinishBtn');
  const skipBtn = document.getElementById('onboardSkipBtn');
  const onboardSubTitle = document.getElementById('onboardSubTitle');

  // Step 0: Welcome screen Next button
  if (welcomeNextBtn && welcomeCard && step1) {
    welcomeNextBtn.addEventListener('click', () => {
      welcomeCard.style.display = 'none';
      step1.style.display = 'block';
      if (onboardSubTitle) onboardSubTitle.textContent = 'Who are you?';
    });
  }

  // Step 1: Persona card clicks
  document.querySelectorAll('.persona-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.persona-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      selectedPersona = card.dataset.persona || 'Student';
    });
  });

  // Step 1: Persona choice submitted -> save persona and open main view (or optional token step)
  if (step1Next) {
    step1Next.addEventListener('click', async () => {
      await seedPersonaDefaults(selectedPersona, true);
      // Item 1 Rule 3: After the user chooses, save the persona and show the normal popup.
      document.getElementById('onboardingView').style.display = 'none';
      document.getElementById('mainView').style.display = 'block';
      await loadPopupState();
    });
  }

  if (backBtn && step1 && step2) {
    backBtn.addEventListener('click', () => {
      step2.style.display = 'none';
      step1.style.display = 'block';
    });
  }

  const completeOnboarding = async (token) => {
    const personaKey = getPersonaKey(selectedPersona);
    await seedPersonaDefaults(personaKey, true);

    const updates = { onboardingComplete: true };
    if (token) {
      updates.apiToken = token;
    }
    await chrome.storage.local.set(updates);

    if (token) {
      chrome.runtime.sendMessage({ type: 'TRIGGER_SYNC' }, () => {
        loadPopupState();
      });
    }

    document.getElementById('onboardingView').style.display = 'none';
    document.getElementById('mainView').style.display = 'block';
    await loadPopupState();
  };

  if (finishBtn) {
    finishBtn.addEventListener('click', async () => {
      const tokenInput = document.getElementById('onboardTokenInput');
      const token = (tokenInput?.value || '').trim();
      await completeOnboarding(token);
    });
  }

  if (skipBtn) {
    skipBtn.addEventListener('click', async () => {
      await completeOnboarding('');
    });
  }
}

// ── State Loader & Renderers ─────────────────────────────────────────────────

async function getServerUrl() {
  const { serverUrl } = await chrome.storage.local.get(['serverUrl']);
  return (serverUrl && serverUrl.trim()) ? serverUrl.trim().replace(/\/+$/, '') : DEFAULT_SERVER_URL;
}

function cleanInputDomain(str) {
  if (!str) return '';
  let d = str.trim().toLowerCase();
  d = d.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0].split('?')[0].split(':')[0];
  return d;
}

async function loadPopupState() {
  const data = await chrome.storage.local.get([
    'apiToken',
    'serverUrl',
    'streakDays',
    'focusModeActive',
    'distractingSites',
    'blockedSites',
    'productiveSites',
    'allowedSites',
    'siteTimes',
    'siteLimits',
    'userTimeLimitMinutes',
    'lastSyncedTime',
    'scheduleEnabled',
    'scheduleStart',
    'scheduleEnd',
    'persona'
  ]);

  const apiToken = data.apiToken || '';
  const server = data.serverUrl || DEFAULT_SERVER_URL;
  const streakDays = data.streakDays !== undefined ? data.streakDays : 0;
  const focusModeActive = !!data.focusModeActive;
  const globalLimit = data.userTimeLimitMinutes || 60;
  const siteTimes = data.siteTimes || {};
  const siteLimits = data.siteLimits || {};

  // Resolve distracting sites (already seeded into storage, or empty if user cleared)
  let distracting = data.distractingSites || data.blockedSites || [];
  let productive = data.productiveSites || data.allowedSites || [];

  if (distracting.length === 0 && productive.length === 0) {
    const pKey = getPersonaKey(data.persona || selectedPersona || 'Student');
    const pDef = PERSONA_DEFAULTS[pKey] || PERSONA_DEFAULTS.Student;
    distracting = [...pDef.distracting];
    productive = [...pDef.productive];
    await chrome.storage.local.set({
      defaultsSeeded: true,
      persona: pKey,
      distractingSites: distracting,
      blockedSites: distracting,
      productiveSites: productive,
      allowedSites: productive
    });
    chrome.runtime.sendMessage({
      type: 'UPDATE_SITE_LISTS',
      distractingSites: distracting,
      productiveSites: productive
    });
  }

  // 0. Pomodoro Focus Timer
  await renderPomodoroUI();

  // 1. Header Streak
  renderStreakBadge(streakDays);

  // 2. Focus Mode Toggle
  const focusToggle = document.getElementById('focusToggle');
  if (focusToggle) focusToggle.checked = focusModeActive;

  // 2a. Shorts & Reels Blocker Toggle (Item 4: Student Persona Only)
  const currentPersonaKey = getPersonaKey(data.persona || selectedPersona);
  const shortsReelsRow = document.getElementById('shortsReelsRow');
  const shortsToggle = document.getElementById('blockShortsReelsToggle');

  if (currentPersonaKey === 'Student') {
    if (shortsReelsRow) shortsReelsRow.style.display = 'flex';
    const { blockShortsReels = false } = await chrome.storage.local.get(['blockShortsReels']);
    if (shortsToggle) shortsToggle.checked = !!blockShortsReels;
  } else {
    // Hide switch and ensure feature is off for other personas
    if (shortsReelsRow) shortsReelsRow.style.display = 'none';
    if (shortsToggle) shortsToggle.checked = false;
    await chrome.storage.local.set({ blockShortsReels: false });
    chrome.runtime.sendMessage({ type: 'TOGGLE_SHORTS_REELS', enabled: false });
  }

  // 2b. Scheduled Focus Mode
  const pKey = currentPersonaKey;
  const pDef = PERSONA_DEFAULTS[pKey] || PERSONA_DEFAULTS.Student;
  const scheduleEnabled = data.scheduleEnabled !== undefined ? data.scheduleEnabled : false;
  const scheduleStart = data.scheduleStart || pDef.scheduleStart || '20:00';
  const scheduleEnd = data.scheduleEnd || pDef.scheduleEnd || '22:00';
  renderScheduleStatus(scheduleEnabled, scheduleStart, scheduleEnd);

  // 3. Global Default Timer
  const globalLabel = document.getElementById('globalLimitLabel');
  if (globalLabel) globalLabel.textContent = `${globalLimit}m`;

  // 4. Distracting Sites Section
  renderDistractingSites(distracting, siteTimes, siteLimits, globalLimit);

  // 5. Productive Sites Section
  renderProductiveSites(productive, siteTimes);

  // 6. Sync & Account Area
  const sDisplay = document.getElementById('serverDisplay');
  if (sDisplay) sDisplay.textContent = server;

  const connectedText = document.getElementById('connectedAccountText');
  const { connectedAccountName } = await chrome.storage.local.get(['connectedAccountName']);
  if (connectedText) {
    if (apiToken && connectedAccountName) {
      connectedText.textContent = `Connected as ${connectedAccountName}`;
      connectedText.style.color = 'var(--ink)';
    } else if (apiToken) {
      connectedText.textContent = 'Connected account';
      connectedText.style.color = 'var(--ink)';
    } else {
      connectedText.textContent = 'Not signed in';
      connectedText.style.color = 'var(--ink-muted)';
    }
  }

  const tokenInput = document.getElementById('apiTokenInput');
  if (tokenInput && apiToken) {
    tokenInput.value = apiToken.slice(0, 8) + '••••••••';
    tokenInput.dataset.saved = 'true';
  }

  const syncStatus = document.getElementById('syncStatusText');
  const footerDot = document.getElementById('footerStatusDot');
  if (syncStatus) {
    syncStatus.textContent = apiToken ? 'Connected' : 'Not Linked';
    syncStatus.style.color = apiToken ? 'var(--prod)' : 'var(--ent)';
  }
  if (footerDot) {
    footerDot.className = apiToken ? 'status-dot' : 'status-dot not-linked';
  }

  // 7. Last Synced Label
  renderLastSynced(data.lastSyncedTime);
}

function renderStreakBadge(streak) {
  const count = parseInt(streak, 10) || 0;
  const textEl = document.getElementById('streakCountText');
  if (!textEl) return;
  if (count === 0) {
    textEl.textContent = '— No streak yet';
  } else if (count === 1) {
    textEl.textContent = '1-Day Streak';
  } else {
    textEl.textContent = `${count}-Day Streak`;
  }
}

function formatTime12h(timeStr) {
  if (!timeStr) return '';
  const parts = timeStr.split(':');
  if (parts.length < 2) return timeStr;
  let h = parseInt(parts[0], 10);
  const m = parts[1].padStart(2, '0');
  const ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12;
  if (h === 0) h = 12;
  return `${h}:${m} ${ampm}`;
}

function formatTimeMmSs(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds || 0));
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function isInsideSchedule(startStr, endStr) {
  if (!startStr || !endStr) return false;
  const sParts = startStr.split(':').map(Number);
  const eParts = endStr.split(':').map(Number);
  if (isNaN(sParts[0]) || isNaN(eParts[0])) return false;
  const startMin = sParts[0] * 60 + (sParts[1] || 0);
  const endMin = eParts[0] * 60 + (eParts[1] || 0);
  const now = new Date();
  const nowMin = now.getHours() * 60 + now.getMinutes();
  if (startMin < endMin) {
    return nowMin >= startMin && nowMin < endMin;
  } else {
    return nowMin >= startMin || nowMin < endMin;
  }
}

function renderScheduleStatus(enabled, startStr = '20:00', endStr = '22:00') {
  const toggle = document.getElementById('scheduleToggle');
  const statusText = document.getElementById('scheduleStatusText');
  const badge = document.getElementById('scheduleTimesBadge');
  const startInput = document.getElementById('popupSchedStart');
  const endInput = document.getElementById('popupSchedEnd');

  if (toggle) toggle.checked = !!enabled;
  if (badge) {
    badge.textContent = `${formatTime12h(startStr)} to ${formatTime12h(endStr)}`;
  }
  if (startInput && document.activeElement !== startInput) {
    startInput.value = startStr;
  }
  if (endInput && document.activeElement !== endInput) {
    endInput.value = endStr;
  }
  if (!statusText) return;

  if (!enabled) {
    statusText.textContent = 'Schedule off';
  } else {
    const inside = isInsideSchedule(startStr, endStr);
    if (inside) {
      statusText.textContent = `Active until ${formatTime12h(endStr)}`;
    } else {
      statusText.textContent = `Next focus: ${formatTime12h(startStr)}`;
    }
  }
}

function renderLastSynced(lastSyncedTime) {
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

// ── Distracting Sites List ───────────────────────────────────────────────────

function renderDistractingSites(sites, siteTimes, siteLimits, globalLimit) {
  const container = document.getElementById('distractingSitesContainer') || document.getElementById('distractingListContainer');
  if (!container) return;

  if (!sites || sites.length === 0) {
    container.innerHTML = '<div style="text-align:center; padding:12px; font-size:11.5px; color:var(--ink-muted);">No distracting sites added.</div>';
    return;
  }

  let html = '';
  sites.forEach(domain => {
    const seconds = siteTimes[domain] || 0;
    const customObj = siteLimits[domain];
    const isCustom = customObj && typeof customObj.daily_limit_minutes === 'number' && customObj.daily_limit_minutes > 0;
    const limitMins = isCustom ? customObj.daily_limit_minutes : globalLimit;
    const limitSeconds = limitMins * 60;

    const pct = Math.min(Math.round((seconds / Math.max(limitSeconds, 1)) * 100), 100);

    let barColor = 'var(--pri)';
    if (pct >= 100) barColor = 'var(--ent)';
    else if (pct >= 80) barColor = 'var(--soc)';

    const limitPillLabel = isCustom ? `${limitMins}m (custom)` : `${limitMins}m (default)`;

    html += `
      <div class="site-item" data-domain="${domain}">
        <div class="site-item-top">
          <div class="site-name-wrap">
            <span class="site-dot distracting"></span>
            <span class="site-name" title="${domain}">${domain}</span>
          </div>
          <div class="site-controls">
            <span class="site-time-text" id="time-dist-${domain}">${formatTimeMmSs(seconds)} / ${formatTimeMmSs(limitSeconds)}</span>
            <button class="limit-pill ${isCustom ? 'is-custom' : ''}" data-domain="${domain}" data-limit="${limitMins}" data-custom="${isCustom}" title="Click to customize timer">${limitPillLabel}</button>
            <button class="delete-btn delete-distracting-btn" data-domain="${domain}" title="Delete site">✕</button>
          </div>
        </div>
        <div class="mini-bar">
          <div class="mini-bar-inner" id="bar-dist-${domain}" style="width:${pct}%; background:${barColor};"></div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;

  // Bind custom limit modal openers
  container.querySelectorAll('.limit-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      openCustomLimitModal(btn.dataset.domain, btn.dataset.limit, btn.dataset.custom === 'true');
    });
  });

  // Bind delete site buttons
  container.querySelectorAll('.delete-distracting-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      await deleteDistractingSite(btn.dataset.domain);
    });
  });
}

// ── Productive Sites List ────────────────────────────────────────────────────

function renderProductiveSites(sites, siteTimes) {
  const container = document.getElementById('productiveSitesContainer') || document.getElementById('productiveListContainer');
  if (!container) return;

  if (!sites || sites.length === 0) {
    container.innerHTML = '<div style="text-align:center; padding:12px; font-size:11.5px; color:var(--ink-muted);">No productive sites added.</div>';
    return;
  }

  let html = '';
  sites.forEach(domain => {
    const seconds = siteTimes[domain] || 0;
    const usedMins = Math.floor(seconds / 60);

    html += `
      <div class="site-item" data-domain="${domain}">
        <div class="site-item-top">
          <div class="site-name-wrap">
            <span class="site-dot productive"></span>
            <span class="site-name" title="${domain}">${domain}</span>
          </div>
          <div class="site-controls">
            <span class="site-time-text" id="time-prod-${domain}">${usedMins}m today</span>
            <button class="delete-btn delete-productive-btn" data-domain="${domain}" title="Delete site">✕</button>
          </div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;

  // Bind delete buttons
  container.querySelectorAll('.delete-productive-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      await deleteProductiveSite(btn.dataset.domain);
    });
  });
}

// ── Site Management Actions ──────────────────────────────────────────────────

async function addDistractingSite(domain) {
  const d = cleanInputDomain(domain);
  if (!d || !d.includes('.')) {
    alert('Please enter a valid domain name (e.g. reddit.com)');
    return;
  }

  const { distractingSites = [], productiveSites = [] } = await chrome.storage.local.get([
    'distractingSites', 'productiveSites'
  ]);

  if (distractingSites.includes(d)) {
    alert(`${d} is already in the distracting list.`);
    return;
  }

  // If site was in productive, remove from productive
  const newProductive = productiveSites.filter(s => s !== d);
  const newDistracting = [...distractingSites, d];

  await chrome.storage.local.set({
    distractingSites: newDistracting,
    blockedSites: newDistracting,
    productiveSites: newProductive,
    allowedSites: newProductive
  });

  chrome.runtime.sendMessage({
    type: 'UPDATE_SITE_LISTS',
    distractingSites: newDistracting,
    productiveSites: newProductive
  });

  loadPopupState();
}

async function deleteDistractingSite(domain) {
  const { distractingSites = [], productiveSites = [] } = await chrome.storage.local.get([
    'distractingSites', 'productiveSites'
  ]);

  const newDistracting = distractingSites.filter(s => s !== domain);

  await chrome.storage.local.set({
    distractingSites: newDistracting,
    blockedSites: newDistracting
  });

  chrome.runtime.sendMessage({
    type: 'UPDATE_SITE_LISTS',
    distractingSites: newDistracting,
    productiveSites
  });

  loadPopupState();
}

async function addProductiveSite(domain) {
  const d = cleanInputDomain(domain);
  if (!d || !d.includes('.')) {
    alert('Please enter a valid domain name (e.g. github.com)');
    return;
  }

  const { distractingSites = [], productiveSites = [] } = await chrome.storage.local.get([
    'distractingSites', 'productiveSites'
  ]);

  if (productiveSites.includes(d)) {
    alert(`${d} is already in the productive list.`);
    return;
  }

  // If site was in distracting, remove from distracting
  const newDistracting = distractingSites.filter(s => s !== d);
  const newProductive = [...productiveSites, d];

  await chrome.storage.local.set({
    distractingSites: newDistracting,
    blockedSites: newDistracting,
    productiveSites: newProductive,
    allowedSites: newProductive
  });

  chrome.runtime.sendMessage({
    type: 'UPDATE_SITE_LISTS',
    distractingSites: newDistracting,
    productiveSites: newProductive
  });

  loadPopupState();
}

async function deleteProductiveSite(domain) {
  const { distractingSites = [], productiveSites = [] } = await chrome.storage.local.get([
    'distractingSites', 'productiveSites'
  ]);

  const newProductive = productiveSites.filter(s => s !== domain);

  await chrome.storage.local.set({
    productiveSites: newProductive,
    allowedSites: newProductive
  });

  chrome.runtime.sendMessage({
    type: 'UPDATE_SITE_LISTS',
    distractingSites,
    productiveSites: newProductive
  });

  loadPopupState();
}

// ── Modals: Custom Limit & Global Limit ───────────────────────────────────────

function openCustomLimitModal(domain, currentLimit, isCustom) {
  currentCustomDomain = domain;
  const modal = document.getElementById('customLimitModal');
  const title = document.getElementById('modalDomainTitle');
  const input = document.getElementById('modalCustomLimitInput');
  const revertBtn = document.getElementById('modalRevertDefaultBtn');

  if (title) title.textContent = domain;
  if (input) input.value = currentLimit || 60;
  if (revertBtn) revertBtn.style.display = isCustom ? 'block' : 'none';
  if (modal) modal.style.display = 'flex';
}

function closeCustomLimitModal() {
  const modal = document.getElementById('customLimitModal');
  if (modal) modal.style.display = 'none';
  currentCustomDomain = null;
}

function openGlobalLimitModal() {
  chrome.storage.local.get(['userTimeLimitMinutes'], data => {
    const modal = document.getElementById('globalLimitModal');
    const input = document.getElementById('modalGlobalLimitInput');
    if (input) input.value = data.userTimeLimitMinutes || 60;
    if (modal) modal.style.display = 'flex';
  });
}

function closeGlobalLimitModal() {
  const modal = document.getElementById('globalLimitModal');
  if (modal) modal.style.display = 'none';
}

// ── Live Ticker ──────────────────────────────────────────────────────────────

function startLiveTicker() {
  if (liveTickerInterval) clearInterval(liveTickerInterval);
  liveTickerInterval = setInterval(async () => {
    const {
      siteTimes = {},
      siteLimits = {},
      userTimeLimitMinutes = 60,
      activeTrackingSession = {}
    } = await chrome.storage.local.get([
      'siteTimes', 'siteLimits', 'userTimeLimitMinutes', 'activeTrackingSession'
    ]);

    const activeDomain = (activeTrackingSession.isWindowFocused && activeTrackingSession.isUserActive && activeTrackingSession.domain)
      ? activeTrackingSession.domain : null;
    const now = Date.now();
    const liveDelta = (activeDomain && activeTrackingSession.lastCommitTimestamp)
      ? Math.max(0, Math.floor((now - activeTrackingSession.lastCommitTimestamp) / 1000))
      : 0;

    // Live update distracting sites
    document.querySelectorAll('#distractingSitesContainer .site-item').forEach(item => {
      const domain = item.dataset.domain;
      if (!domain) return;
      let seconds = siteTimes[domain] || 0;
      if (domain === activeDomain && liveDelta > 0 && liveDelta < 60) {
        seconds += liveDelta;
      }

      const customObj = siteLimits[domain];
      const isCustom = customObj && typeof customObj.daily_limit_minutes === 'number' && customObj.daily_limit_minutes > 0;
      const limitMins = isCustom ? customObj.daily_limit_minutes : userTimeLimitMinutes;
      const limitSeconds = limitMins * 60;

      const pct = Math.min(Math.round((seconds / Math.max(limitSeconds, 1)) * 100), 100);

      const textEl = document.getElementById(`time-dist-${domain}`);
      if (textEl) textEl.textContent = `${formatTimeMmSs(seconds)} / ${formatTimeMmSs(limitSeconds)}`;

      const barEl = document.getElementById(`bar-dist-${domain}`);
      if (barEl) {
        barEl.style.width = `${pct}%`;
        if (pct >= 100) barEl.style.background = 'var(--ent)';
        else if (pct >= 80) barEl.style.background = 'var(--soc)';
        else barEl.style.background = 'var(--pri)';
      }
    });

    // Live update productive sites
    document.querySelectorAll('#productiveSitesContainer .site-item').forEach(item => {
      const domain = item.dataset.domain;
      if (!domain) return;
      let seconds = siteTimes[domain] || 0;
      if (domain === activeDomain && liveDelta > 0 && liveDelta < 60) {
        seconds += liveDelta;
      }

      const textEl = document.getElementById(`time-prod-${domain}`);
      if (textEl) textEl.textContent = `${formatTimeMmSs(seconds)} today`;
    });

    // Live update Pomodoro Timer
    if (pomodoroLocalState.state === 'running' && pomodoroLocalState.endTime) {
      const diff = Math.max(0, Math.round((pomodoroLocalState.endTime - Date.now()) / 1000));
      pomodoroLocalState.remainingSec = diff;
      const display = document.getElementById('pomoDisplay');
      if (display) display.textContent = formatPomoTime(diff);
      if (diff <= 0) {
        renderPomodoroUI();
      }
    }
  }, 1000);
}

// ── Setup Event Listeners ────────────────────────────────────────────────────

function setupEventListeners() {
  // 0. Pomodoro Controls (Start / Stop)
  const pomoStartBtn = document.getElementById('pomoStartBtn');
  const pomoResetBtn = document.getElementById('pomoResetBtn');

  if (pomoStartBtn) pomoStartBtn.addEventListener('click', startPomodoroSession);
  if (pomoResetBtn) pomoResetBtn.addEventListener('click', stopPomodoroSession);

  // 1. Focus Mode Toggle
  const focusToggle = document.getElementById('focusToggle');
  if (focusToggle) {
    focusToggle.addEventListener('change', async e => {
      const isChecked = e.target.checked;
      await chrome.storage.local.set({ focusModeActive: isChecked });
      chrome.runtime.sendMessage({
        type: 'SET_FOCUS_MODE',
        enabled: isChecked
      }, res => {
        if (!res || !res.success) {
          focusToggle.checked = !isChecked;
          chrome.storage.local.set({ focusModeActive: !isChecked });
        }
      });
    });
  }

  // 1a. Shorts & Reels Blocker Toggle
  const shortsToggle = document.getElementById('blockShortsReelsToggle');
  if (shortsToggle) {
    shortsToggle.addEventListener('change', async e => {
      const isChecked = e.target.checked;
      await chrome.storage.local.set({ blockShortsReels: isChecked });
      chrome.runtime.sendMessage({
        type: 'TOGGLE_SHORTS_REELS',
        enabled: isChecked
      });
    });
  }

  // 1b. Scheduled Focus Mode Toggle & Inline Editor
  const schedRow = document.getElementById('scheduleRow');
  const schedToggle = document.getElementById('scheduleToggle');
  const schedEditor = document.getElementById('scheduleEditor');
  const saveSchedBtn = document.getElementById('popupSaveSchedBtn');
  const schedStartInput = document.getElementById('popupSchedStart');
  const schedEndInput = document.getElementById('popupSchedEnd');
  const schedErrorMsg = document.getElementById('scheduleErrorMsg');

  if (schedRow && schedEditor) {
    schedRow.addEventListener('click', (e) => {
      if (e.target && e.target.closest('.switch')) return;
      const isHidden = schedEditor.style.display === 'none' || !schedEditor.style.display;
      schedEditor.style.display = isHidden ? 'block' : 'none';
    });
  }

  if (schedToggle) {
    if (schedToggle.parentElement) {
      schedToggle.parentElement.addEventListener('click', e => {
        e.stopPropagation();
      });
    }
    schedToggle.addEventListener('change', async e => {
      const isChecked = e.target.checked;
      if (isChecked && schedEditor) {
        schedEditor.style.display = 'block';
      }
      chrome.runtime.sendMessage({
        type: 'UPDATE_SCHEDULE',
        scheduleEnabled: isChecked
      }, res => {
        chrome.storage.local.get(['scheduleStart', 'scheduleEnd'], d => {
          renderScheduleStatus(isChecked, d.scheduleStart || '20:00', d.scheduleEnd || '22:00');
        });
      });
    });
  }

  if (saveSchedBtn && schedStartInput && schedEndInput) {
    saveSchedBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const sVal = schedStartInput.value.trim();
      const eVal = schedEndInput.value.trim();

      if (!sVal || !eVal) {
        if (schedErrorMsg) {
          schedErrorMsg.textContent = 'Please choose both start and end times.';
          schedErrorMsg.style.display = 'block';
        }
        return;
      }

      // Requirement 4: Reject an end time equal to the start time
      if (sVal === eVal) {
        if (schedErrorMsg) {
          schedErrorMsg.textContent = 'Start time and end time cannot be the same.';
          schedErrorMsg.style.display = 'block';
        }
        return;
      }

      if (schedErrorMsg) schedErrorMsg.style.display = 'none';

      // Save and sync immediately to background and backend
      chrome.runtime.sendMessage({
        type: 'UPDATE_SCHEDULE',
        scheduleStart: sVal,
        scheduleEnd: eVal,
        scheduleEnabled: true
      }, res => {
        renderScheduleStatus(true, sVal, eVal);
        const origText = saveSchedBtn.textContent;
        const origBg = saveSchedBtn.style.background;
        saveSchedBtn.textContent = 'Saved ✓';
        saveSchedBtn.style.background = '#10B981';
        setTimeout(() => {
          saveSchedBtn.textContent = origText;
          saveSchedBtn.style.background = origBg;
        }, 1500);
      });
    });
  }

  // 2. Add Distracting Site
  const addDistBtn = document.getElementById('addDistractingBtn');
  const addDistInput = document.getElementById('addDistractingInput');
  if (addDistBtn && addDistInput) {
    const handleAdd = () => {
      addDistractingSite(addDistInput.value);
      addDistInput.value = '';
    };
    addDistBtn.addEventListener('click', handleAdd);
    addDistInput.addEventListener('keydown', e => { if (e.key === 'Enter') handleAdd(); });
  }

  // 3. Add Productive Site
  const addProdBtn = document.getElementById('addProductiveBtn');
  const addProdInput = document.getElementById('addProductiveInput');
  if (addProdBtn && addProdInput) {
    const handleAdd = () => {
      addProductiveSite(addProdInput.value);
      addProdInput.value = '';
    };
    addProdBtn.addEventListener('click', handleAdd);
    addProdInput.addEventListener('keydown', e => { if (e.key === 'Enter') handleAdd(); });
  }

  // 4. Global Limit Modal Triggers
  const openGlobalBtn = document.getElementById('openGlobalLimitModalBtn');
  if (openGlobalBtn) openGlobalBtn.addEventListener('click', openGlobalLimitModal);

  const cancelGlobalBtn = document.getElementById('modalCancelGlobalBtn');
  if (cancelGlobalBtn) cancelGlobalBtn.addEventListener('click', closeGlobalLimitModal);

  const saveGlobalBtn = document.getElementById('modalSaveGlobalBtn');
  if (saveGlobalBtn) {
    saveGlobalBtn.addEventListener('click', () => {
      const input = document.getElementById('modalGlobalLimitInput');
      const val = parseInt(input?.value, 10);
      if (!val || val < 1 || val > 1440) {
        alert('Please enter a limit between 1 and 1440 minutes.');
        return;
      }
      chrome.runtime.sendMessage({ type: 'SET_GLOBAL_LIMIT', limitMinutes: val }, () => {
        closeGlobalLimitModal();
        loadPopupState();
      });
    });
  }

  // 5. Custom Limit Modal Triggers
  const cancelCustomBtn = document.getElementById('modalCancelCustomBtn');
  if (cancelCustomBtn) cancelCustomBtn.addEventListener('click', closeCustomLimitModal);

  const saveCustomBtn = document.getElementById('modalSaveCustomBtn');
  if (saveCustomBtn) {
    saveCustomBtn.addEventListener('click', () => {
      if (!currentCustomDomain) return;
      const input = document.getElementById('modalCustomLimitInput');
      const val = parseInt(input?.value, 10);
      if (!val || val < 1 || val > 1440) {
        alert('Please enter a limit between 1 and 1440 minutes.');
        return;
      }
      chrome.runtime.sendMessage({
        type: 'SET_CUSTOM_LIMIT',
        domain: currentCustomDomain,
        limitMinutes: val
      }, () => {
        closeCustomLimitModal();
        loadPopupState();
      });
    });
  }

  const revertDefaultBtn = document.getElementById('modalRevertDefaultBtn');
  if (revertDefaultBtn) {
    revertDefaultBtn.addEventListener('click', () => {
      if (!currentCustomDomain) return;
      chrome.runtime.sendMessage({
        type: 'REMOVE_CUSTOM_LIMIT',
        domain: currentCustomDomain
      }, () => {
        closeCustomLimitModal();
        loadPopupState();
      });
    });
  }

  // 6. Save API Token
  const saveTokenBtn = document.getElementById('saveTokenBtn');
  const tokenInput = document.getElementById('apiTokenInput');
  const tokenMsg = document.getElementById('tokenSaveMsg');

  function showTokenMsg(text, isError = false) {
    if (!tokenMsg) return;
    tokenMsg.textContent = text;
    tokenMsg.style.color = isError ? 'var(--ent)' : 'var(--prod)';
    tokenMsg.style.opacity = '1';
    setTimeout(() => { if (tokenMsg) tokenMsg.style.opacity = '0'; }, 3000);
  }

  if (tokenInput) {
    tokenInput.addEventListener('focus', () => {
      if (tokenInput.dataset.saved === 'true') {
        tokenInput.value = '';
        tokenInput.dataset.saved = 'false';
      }
    });
  }

  if (saveTokenBtn && tokenInput) {
    saveTokenBtn.addEventListener('click', async () => {
      const raw = tokenInput.value.trim();
      if (!raw || raw.includes('••••')) {
        showTokenMsg('Token already saved.', false);
        return;
      }
      if (raw.length < 10) {
        showTokenMsg('Token looks too short.', true);
        return;
      }

      await chrome.storage.local.set({ apiToken: raw });
      tokenInput.value = raw.slice(0, 8) + '••••••••';
      tokenInput.dataset.saved = 'true';
      showTokenMsg('✅ Token saved! Syncing now…', false);

      // Push local site lists to server so server UserSettings are immediately populated
      const { distractingSites = [], productiveSites = [] } = await chrome.storage.local.get([
        'distractingSites', 'productiveSites'
      ]);
      const serverUrl = await getServerUrl();
      if (distractingSites.length > 0 || productiveSites.length > 0) {
        fetch(`${serverUrl}/api/settings/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${raw}`
          },
          body: JSON.stringify({
            blocked_sites: distractingSites.join('\n'),
            allowed_sites: productiveSites.join('\n')
          })
        }).catch(() => {});
      }

      chrome.runtime.sendMessage({ type: 'TRIGGER_SYNC' }, () => {
        loadPopupState();
      });
    });
  }

  // 7. Reset All Timers Modal
  const resetBtn = document.getElementById('resetTimersBtn');
  const overlay = document.getElementById('confirmOverlay');
  const cancelResetBtn = document.getElementById('cancelResetBtn');
  const confirmResetBtn = document.getElementById('confirmResetBtn');

  if (resetBtn && overlay) {
    resetBtn.addEventListener('click', () => { overlay.style.display = 'flex'; });
    cancelResetBtn.addEventListener('click', () => { overlay.style.display = 'none'; });
    confirmResetBtn.addEventListener('click', () => {
      overlay.style.display = 'none';
      chrome.runtime.sendMessage({ type: 'RESET_ALL_TIMERS' }, () => {
        loadPopupState();
      });
    });
  }
}

// Keep popup in sync if storage changes while popup is open
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local') return;
  if (changes.scheduleEnabled || changes.scheduleStart || changes.scheduleEnd) {
    chrome.storage.local.get(['scheduleEnabled', 'scheduleStart', 'scheduleEnd'], d => {
      renderScheduleStatus(d.scheduleEnabled, d.scheduleStart, d.scheduleEnd);
    });
  }
  if (changes.focusModeActive) {
    const fToggle = document.getElementById('focusToggle');
    if (fToggle) fToggle.checked = !!changes.focusModeActive.newValue;
  }
  if (changes.blockShortsReels) {
    const sToggle = document.getElementById('blockShortsReelsToggle');
    if (sToggle) sToggle.checked = !!changes.blockShortsReels.newValue;
  }
  if (changes.pomodoroState || changes.pomodoroEndTime || changes.pomodoroMode || changes.pomodoroRemainingSec) {
    renderPomodoroUI();
  }
});