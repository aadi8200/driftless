// ── Timer Display ────────────────────────────────────────────────────────────

function updateTime() {
    chrome.storage.local.get(['siteTimes', 'currentActiveSite', 'currentStartTime'], function(result) {
        let times = result.siteTimes || {};
        let displayHTML = "";
        const sites = ["youtube.com", "instagram.com", "facebook.com", "reddit.com"];

        // Asli Jadoo: Agar koi site abhi khuli hui hai, toh uska live time calculate karke jod do!
        if (result.currentActiveSite && result.currentStartTime) {
            let liveTimeSpent = Math.floor((Date.now() - result.currentStartTime) / 1000);
            times[result.currentActiveSite] = (times[result.currentActiveSite] || 0) + liveTimeSpent;
        }

        sites.forEach(site => {
            let totalSeconds = times[site] || 0;
            let minutes = Math.floor(totalSeconds / 60);
            let seconds = totalSeconds % 60;

            let formattedTime =
                (minutes < 10 ? "0" + minutes : minutes) + ":" +
                (seconds < 10 ? "0" + seconds : seconds);

            let displayName = site.split('.')[0];
            displayName = displayName.charAt(0).toUpperCase() + displayName.slice(1);

            displayHTML += `<p><strong>${displayName}</strong><span class="time-val">${formattedTime}</span></p>`;

        });

        document.getElementById('timer').innerHTML = displayHTML;
    });
}

updateTime();
// Har 1 second (1000ms) mein popup refresh hota rahega
setInterval(updateTime, 1000);

// Reset Button ka Logic
document.getElementById('resetBtn').addEventListener('click', function() {
    // Reset accumulated times, current start time, and notification flags
    chrome.storage.local.set({
        siteTimes: {},
        currentStartTime: Date.now(),
        notifiedSites: {}
    }, function() {
        updateTime(); // Screen ko turant update karo
        console.log("Timer reset successful!");
    });
});


// ── Focus Mode Toggle ─────────────────────────────────────────────────────────

const focusToggle = document.getElementById('focusToggle');
const focusStatus = document.getElementById('focusStatus');

/**
 * Applies the visual state of the toggle to match the given boolean.
 */
function applyFocusUI(isActive) {
    focusToggle.checked = isActive;
    if (isActive) {
        focusStatus.textContent = "ON — Sites Blocked";
        focusStatus.classList.add('active');
    } else {
        focusStatus.textContent = "OFF";
        focusStatus.classList.remove('active');
    }
}

// On popup open: read the stored state and restore the toggle position.
chrome.storage.local.get(['focusModeActive'], function(result) {
    const isActive = result.focusModeActive === true;
    applyFocusUI(isActive);
});

// When the user flips the toggle:
focusToggle.addEventListener('change', function() {
    const isActive = focusToggle.checked;

    // 1. Persist state so the toggle survives popup close/reopen.
    chrome.storage.local.set({ focusModeActive: isActive });

    // 2. Update UI immediately.
    applyFocusUI(isActive);

    // 3. Notify background.js to enable/disable declarativeNetRequest rules.
    chrome.runtime.sendMessage({ type: 'SET_FOCUS_MODE', enabled: isActive }, function(response) {
        if (chrome.runtime.lastError) {
            console.error("Focus Mode message error:", chrome.runtime.lastError.message);
        } else {
            console.log("Focus Mode response:", response);
        }
    });
});


// ── Daily Time Limit ──────────────────────────────────────────────────────────

const limitInput   = document.getElementById('limitInput');
const saveLimitBtn = document.getElementById('saveLimitBtn');
const limitSaveMsg = document.getElementById('limitSaveMsg');

// On popup open: populate the input with whatever is already stored.
chrome.storage.local.get(['userTimeLimitMinutes'], function(result) {
    if (result.userTimeLimitMinutes) {
        limitInput.value = result.userTimeLimitMinutes;
    }
});

// Show a transient success/error message below the input.
function showLimitMsg(text, isError = false) {
    limitSaveMsg.textContent = text;
    limitSaveMsg.style.color = isError ? '#ff6b6b' : '#8FBFA0';
    limitSaveMsg.style.opacity = '1';
    setTimeout(() => { limitSaveMsg.style.opacity = '0'; }, 2500);
}

saveLimitBtn.addEventListener('click', function() {
    const raw = parseInt(limitInput.value, 10);

    if (!raw || raw < 1 || raw > 1440) {
        showLimitMsg('Enter a value between 1 and 1440 mins.', true);
        return;
    }

    // Persist in storage — background.js reads this on every check.
    chrome.storage.local.set({ userTimeLimitMinutes: raw }, function() {
        console.log(`Time limit saved: ${raw} minute(s)`);
        showLimitMsg(`✅ Limit set to ${raw} min${raw > 1 ? 's' : ''}!`);
    });
});


// ── Focus Streak ──────────────────────────────────────────────────────────────

/**
 * Returns today's date as a UTC ISO date string, e.g. "2026-09-06".
 * Using UTC prevents timezone-edge bugs where local midnight ≠ UTC midnight.
 */
function todayUTC() {
    return new Date().toISOString().slice(0, 10);
}

/**
 * Updates the streak badge in the UI.
 * @param {number} streak - the current streak count
 */
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

/**
 * Reads streak state from storage, evaluates whether a new day has started,
 * updates the streak accordingly, and renders it.
 *
 * Storage keys used:
 *   currentStreak      {number}  — current consecutive-day count
 *   lastActiveDate     {string}  — ISO date of last streak evaluation
 *   limitExceededToday {boolean} — true if limit was breached today (set by background.js)
 */
async function evaluateAndDisplayStreak() {
    const data = await chrome.storage.local.get([
        'currentStreak',
        'lastActiveDate',
        'limitExceededToday'
    ]);

    let streak   = data.currentStreak   ?? 0;
    const lastDate = data.lastActiveDate  ?? null;
    const failed   = data.limitExceededToday === true;
    const today    = todayUTC();

    if (lastDate === null) {
        // First time ever — initialise cleanly.
        await chrome.storage.local.set({
            currentStreak:      0,
            lastActiveDate:     today,
            limitExceededToday: false
        });
        renderStreak(0);
        return;
    }

    if (lastDate === today) {
        // Same day — just show whatever is stored, no mutation.
        renderStreak(streak);
        return;
    }

    // A new day has started since the last evaluation.
    // Determine if yesterday was a success (no limit breach).
    const yesterday = new Date(Date.now() - 86_400_000).toISOString().slice(0, 10);
    const wasYesterday = (lastDate === yesterday);

    if (wasYesterday && !failed) {
        // Kept focus yesterday — extend the streak.
        streak += 1;
        console.log(`🔥 Streak extended to ${streak} day(s)!`);
    } else {
        // Either skipped a day or blew the limit — reset.
        streak = 0;
        console.log('💔 Streak reset — limit was exceeded or a day was missed.');
    }

    await chrome.storage.local.set({
        currentStreak:      streak,
        lastActiveDate:     today,
        limitExceededToday: false   // Reset flag for the new day
    });

    renderStreak(streak);
}

// Run streak evaluation every time the popup opens.
evaluateAndDisplayStreak();