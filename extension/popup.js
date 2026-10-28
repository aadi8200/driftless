// ─────────────────────────────────────────────────────────────────────────────
// DRIFTLESS EXTENSION POPUP CONTROLLER
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_SERVER_URL = 'http://127.0.0.1:8000';

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

let liveTickerInterval = null;
let currentCustomDomain = null;
let selectedPersona = 'Student';

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

  const existingDist = (data.distractingSites && data.distractingSites.length > 0)
    ? data.distractingSites
    : (data.blockedSites && data.blockedSites.length > 0 ? data.blockedSites : []);
  const existingProd = (data.productiveSites && data.productiveSites.length > 0)
    ? data.productiveSites
    : (data.allowedSites && data.allowedSites.length > 0 ? data.allowedSites : []);

  // If both lists already have items and not forcing, keep existing user choices
  if (existingDist.length > 0 && existingProd.length > 0 && !force) {
    await chrome.storage.local.set({ defaultsSeeded: true });
    return false;
  }

  const pKey = getPersonaKey(personaName || data.persona || 'Student');
  const pDef = PERSONA_DEFAULTS[pKey] || PERSONA_DEFAULTS.Student;

  const distractingSites = [...pDef.distracting];
  const productiveSites = [...pDef.productive];

  await chrome.storage.local.set({
    defaultsSeeded: true,
    persona: pKey,
    distractingSites,
    blockedSites: distractingSites,
    productiveSites,
    allowedSites: productiveSites
  });

  // Notify background to update DNR rules and internal tracking immediately
  chrome.runtime.sendMessage({
    type: 'UPDATE_SITE_LISTS',
    distractingSites,
    productiveSites
  });

  // If token is linked, sync to backend settings immediately
  if (data.apiToken) {
    const serverUrl = await getServerUrl();
    fetch(`${serverUrl}/api/settings/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${data.apiToken}`
      },
      body: JSON.stringify({
        blocked_sites: distractingSites.join('\n'),
        allowed_sites: productiveSites.join('\n')
      })
    }).catch(() => {});
  }

  return true;
}

async function checkOnboardingState() {
  const {
    onboardingComplete,
    defaultsSeeded,
    apiToken,
    persona,
    distractingSites,
    productiveSites
  } = await chrome.storage.local.get([
    'onboardingComplete', 'defaultsSeeded', 'apiToken', 'persona', 'distractingSites', 'productiveSites'
  ]);

  const onboardingView = document.getElementById('onboardingView');
  const mainView = document.getElementById('mainView');

  const hasLists = (distractingSites && distractingSites.length > 0) || (productiveSites && productiveSites.length > 0);

  // If user has not completed onboarding, has not seeded, has no token, and has no lists -> show onboarding
  if (!onboardingComplete && !defaultsSeeded && !apiToken && !hasLists) {
    if (onboardingView) onboardingView.style.display = 'flex';
    if (mainView) mainView.style.display = 'none';
    setupOnboardingFlow();
  } else {
    if (onboardingView) onboardingView.style.display = 'none';
    if (mainView) mainView.style.display = 'block';

    // Ensure defaults are populated if lists are empty
    if (!hasLists) {
      await seedPersonaDefaults(persona || 'Student', true);
    }
  }
}

function setupOnboardingFlow() {
  const step1 = document.getElementById('onboardStep1');
  const step2 = document.getElementById('onboardStep2');
  const step1Next = document.getElementById('onboardStep1Next');
  const backBtn = document.getElementById('onboardBackBtn');
  const finishBtn = document.getElementById('onboardFinishBtn');
  const skipBtn = document.getElementById('onboardSkipBtn');

  // Persona card clicks
  document.querySelectorAll('.persona-card').forEach(card => {
    card.addEventListener('click', async () => {
      document.querySelectorAll('.persona-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      selectedPersona = card.dataset.persona || 'Student';
      await seedPersonaDefaults(selectedPersona, true);
    });
  });

  if (step1Next) {
    step1Next.addEventListener('click', async () => {
      await seedPersonaDefaults(selectedPersona, true);
      step1.style.display = 'none';
      step2.style.display = 'block';
    });
  }

  if (backBtn) {
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
    'lastSyncedTime'
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

  // 1. Header Streak
  renderStreakBadge(streakDays);

  // 2. Focus Mode Toggle
  const focusToggle = document.getElementById('focusToggle');
  if (focusToggle) focusToggle.checked = focusModeActive;

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
    const usedMins = Math.floor(seconds / 60);
    const customObj = siteLimits[domain];
    const isCustom = customObj && typeof customObj.daily_limit_minutes === 'number' && customObj.daily_limit_minutes > 0;
    const limitMins = isCustom ? customObj.daily_limit_minutes : globalLimit;

    const pct = Math.min(Math.round((usedMins / Math.max(limitMins, 1)) * 100), 100);

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
            <span class="site-time-text" id="time-dist-${domain}">${usedMins}m / ${limitMins}m</span>
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
    const { siteTimes = {}, siteLimits = {}, userTimeLimitMinutes = 60 } = await chrome.storage.local.get([
      'siteTimes', 'siteLimits', 'userTimeLimitMinutes'
    ]);

    // Live update distracting sites
    document.querySelectorAll('#distractingSitesContainer .site-item').forEach(item => {
      const domain = item.dataset.domain;
      if (!domain) return;
      const seconds = siteTimes[domain] || 0;
      const usedMins = Math.floor(seconds / 60);

      const customObj = siteLimits[domain];
      const isCustom = customObj && typeof customObj.daily_limit_minutes === 'number' && customObj.daily_limit_minutes > 0;
      const limitMins = isCustom ? customObj.daily_limit_minutes : userTimeLimitMinutes;

      const pct = Math.min(Math.round((usedMins / Math.max(limitMins, 1)) * 100), 100);

      const textEl = document.getElementById(`time-dist-${domain}`);
      if (textEl) textEl.textContent = `${usedMins}m / ${limitMins}m`;

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
      const seconds = siteTimes[domain] || 0;
      const usedMins = Math.floor(seconds / 60);

      const textEl = document.getElementById(`time-prod-${domain}`);
      if (textEl) textEl.textContent = `${usedMins}m today`;
    });
  }, 1000);
}

// ── Setup Event Listeners ────────────────────────────────────────────────────

function setupEventListeners() {
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