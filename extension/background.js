const TRACKED_SITES = ["youtube.com", "instagram.com", "facebook.com", "reddit.com"];
const ALARM_NAME = "driftless_time_check";
const DEFAULT_TIME_LIMIT_SECONDS = 60; // Fallback: 1 minute

/**
 * Returns the user-defined time limit in seconds.
 * Reads `userTimeLimitMinutes` from storage; falls back to 60 s if not set.
 */
async function getTimeLimitSeconds() {
    const { userTimeLimitMinutes } = await chrome.storage.local.get(['userTimeLimitMinutes']);
    if (userTimeLimitMinutes && userTimeLimitMinutes >= 1) {
        return userTimeLimitMinutes * 60;
    }
    return DEFAULT_TIME_LIMIT_SECONDS;
}

let timerTimeout = null;

console.log("🚀 Driftless Background Service Worker active and monitoring.");

// Synchronous top-level event listeners (Manifest V3 requirement)

// 1. Tab switch listener
chrome.tabs.onActivated.addListener(async (activeInfo) => {
    try {
        const tab = await chrome.tabs.get(activeInfo.tabId);
        await checkSite(tab?.url || "");
    } catch (err) {
        console.debug("Driftless onActivated tab error:", err);
    }
});

// 2. Tab URL update / reload listener
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (tab.active && (changeInfo.url || changeInfo.status === "complete")) {
        await checkSite(tab.url || "");
    }
});

// 3. Tab close listener
chrome.tabs.onRemoved.addListener(async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        await checkSite(tab?.url || "");
    } catch (err) {
        console.debug("Driftless onRemoved query error:", err);
        await checkSite("");
    }
});

// 4. Chrome Alarm listener (wakes up service worker even if idle)
chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === ALARM_NAME) {
        console.log("⏰ Driftless alarm triggered, checking time limit...");
        await checkTimeLimit();
    }
});

// 5. Storage change listener (syncs reset from popup)
chrome.storage.onChanged.addListener(async (changes, areaName) => {
    if (areaName === "local" && changes.siteTimes) {
        const newTimes = changes.siteTimes.newValue || {};
        if (Object.keys(newTimes).length === 0) {
            // Timer was reset in popup
            if (timerTimeout) {
                clearTimeout(timerTimeout);
                timerTimeout = null;
            }
            await chrome.alarms.clear(ALARM_NAME);
            await chrome.storage.local.set({ notifiedSites: {} });

            const { currentActiveSite } = await chrome.storage.local.get(["currentActiveSite"]);
            if (currentActiveSite) {
                const limitSeconds = await getTimeLimitSeconds();
                scheduleCheck(limitSeconds);
            }
        }
    }
});

// 6. Dismiss notification click
chrome.notifications.onClicked.addListener((notificationId) => {
    chrome.notifications.clear(notificationId);
});

// Core logic: Site checking and session management
async function checkSite(url) {
    const matchedSite = TRACKED_SITES.find(site => (url || "").includes(site)) || null;

    const data = await chrome.storage.local.get([
        "siteTimes",
        "currentActiveSite",
        "currentStartTime",
        "notifiedSites"
    ]);

    const siteTimes = data.siteTimes || {};
    const activeSite = data.currentActiveSite || null;
    const siteStartTime = data.currentStartTime || 0;
    const notifiedSites = data.notifiedSites || {};

    // No change in site
    if (activeSite === matchedSite) {
        return;
    }

    // Save time spent on previous site
    if (activeSite && siteStartTime > 0) {
        const timeSpent = Math.floor((Date.now() - siteStartTime) / 1000);
        if (timeSpent > 0) {
            siteTimes[activeSite] = (siteTimes[activeSite] || 0) + timeSpent;
        }
    }

    if (timerTimeout) {
        clearTimeout(timerTimeout);
        timerTimeout = null;
    }
    await chrome.alarms.clear(ALARM_NAME);

    if (matchedSite) {
        const now = Date.now();
        await chrome.storage.local.set({
            siteTimes: siteTimes,
            currentActiveSite: matchedSite,
            currentStartTime: now
        });
        console.log(`🟢 Tracking started for: ${matchedSite}`);

        // Calculate remaining seconds until the user-defined limit
        const limitSeconds = await getTimeLimitSeconds();
        const alreadySpent = siteTimes[matchedSite] || 0;
        const remainingSeconds = limitSeconds - alreadySpent;

        if (remainingSeconds <= 0) {
            // Already exceeded the limit, notify if not already done
            if (!notifiedSites[matchedSite]) {
                await sendNotification(matchedSite, alreadySpent);
                notifiedSites[matchedSite] = true;
                await chrome.storage.local.set({ notifiedSites });
            }
        } else {
            scheduleCheck(remainingSeconds);
        }
    } else {
        // Switched to a non-tracked site
        await chrome.storage.local.set({
            siteTimes: siteTimes,
            currentActiveSite: null,
            currentStartTime: null
        });
        console.log("⚪ Not on a tracked site, timer paused.");
    }
}

// Schedule notification check using alarms (for worker sleep) & timeout (for instant response)
function scheduleCheck(seconds) {
    if (timerTimeout) {
        clearTimeout(timerTimeout);
        timerTimeout = null;
    }

    // Alarm ensures wake-up even if service worker terminates
    chrome.alarms.create(ALARM_NAME, {
        when: Date.now() + (seconds * 1000)
    });

    // In-memory timeout as fast-path while service worker is still awake
    timerTimeout = setTimeout(async () => {
        await checkTimeLimit();
    }, seconds * 1000);
}

// Verify if time limit was reached and trigger notification
async function checkTimeLimit() {
    const data = await chrome.storage.local.get([
        "siteTimes",
        "currentActiveSite",
        "currentStartTime",
        "notifiedSites"
    ]);

    const activeSite = data.currentActiveSite;
    const siteStartTime = data.currentStartTime;
    const siteTimes = data.siteTimes || {};
    const notifiedSites = data.notifiedSites || {};

    if (!activeSite || !siteStartTime) {
        return;
    }

    const limitSeconds = await getTimeLimitSeconds();
    const liveTime = Math.floor((Date.now() - siteStartTime) / 1000);
    const totalSeconds = (siteTimes[activeSite] || 0) + liveTime;
    console.log(`⏱️ Live time on ${activeSite}: ${totalSeconds}s (threshold: ${limitSeconds}s)`);

    if (totalSeconds >= limitSeconds) {
        if (!notifiedSites[activeSite]) {
            console.log(`🚨 Limit reached on ${activeSite}! Triggering notification...`);
            await sendNotification(activeSite, totalSeconds);
            notifiedSites[activeSite] = true;
            await chrome.storage.local.set({ notifiedSites });
        }
    } else {
        // Still have some time remaining, reschedule
        const remaining = limitSeconds - totalSeconds;
        scheduleCheck(remaining);
    }
}

// Send system notification
async function sendNotification(site, totalSeconds) {
    const displayName = site.split(".")[0].charAt(0).toUpperCase() + site.split(".")[0].slice(1);
    const minutes = Math.floor(totalSeconds / 60) || 1;
    const timeText = `${minutes} minute${minutes > 1 ? "s" : ""}`;

    // Mark that the limit was exceeded today — streak evaluator reads this tomorrow.
    await chrome.storage.local.set({ limitExceededToday: true });
    console.log("📛 Daily limit exceeded — streak at risk.");

    await chrome.notifications.create(`driftless-${site}-${Date.now()}`, {
        type: "basic",
        iconUrl: "icons/icon-128.png",
        title: "Driftless - Focus Alert 🚨",
        message: `You've spent ${timeText} on ${displayName}! Time to refocus on your goals.`,
        priority: 2
    }, (id) => {
        if (chrome.runtime.lastError) {
            console.error("❌ Notification error:", chrome.runtime.lastError);
        } else {
            console.log("✅ Notification successfully sent:", id);
        }
    });
}


// ── Focus Mode / Site Blocker ─────────────────────────────────────────────────
// Uses declarativeNetRequest dynamic rules so no page reload is needed.

const FOCUS_RULE_BASE_ID = 100; // Rule IDs 100-103; well clear of any static rules.
const BLOCKED_SITES = ["youtube.com", "instagram.com", "facebook.com", "reddit.com"];

/**
 * Builds a declarativeNetRequest rule that blocks all requests to a given domain
 * and its www. subdomain.
 */
function buildBlockRule(id, domain) {
    return {
        id,
        priority: 1,
        action: { type: "block" },
        condition: {
            urlFilter: `||${domain}`,
            resourceTypes: ["main_frame", "sub_frame", "xmlhttprequest", "script", "image", "stylesheet", "font", "media", "websocket", "other"]
        }
    };
}

/**
 * Enables Focus Mode: adds dynamic blocking rules for all BLOCKED_SITES.
 */
async function enableFocusMode() {
    const rulesToAdd = BLOCKED_SITES.map((domain, i) =>
        buildBlockRule(FOCUS_RULE_BASE_ID + i, domain)
    );
    const ruleIdsToRemove = BLOCKED_SITES.map((_, i) => FOCUS_RULE_BASE_ID + i);

    await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: ruleIdsToRemove, // Remove first to avoid ID conflicts on re-enable
        addRules: rulesToAdd
    });
    console.log("🛡️ Driftless Focus Mode ON — blocking:", BLOCKED_SITES.join(", "));
}

/**
 * Disables Focus Mode: removes all dynamic blocking rules.
 */
async function disableFocusMode() {
    const ruleIdsToRemove = BLOCKED_SITES.map((_, i) => FOCUS_RULE_BASE_ID + i);
    await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: ruleIdsToRemove,
        addRules: []
    });
    console.log("✅ Driftless Focus Mode OFF — all sites unblocked.");
}

// 7. Listen for Focus Mode toggle messages from popup.js
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type === "SET_FOCUS_MODE") {
        const action = message.enabled ? enableFocusMode() : disableFocusMode();
        action
            .then(() => sendResponse({ success: true, focusModeActive: message.enabled }))
            .catch(err => {
                console.error("❌ Focus Mode error:", err);
                sendResponse({ success: false, error: err.message });
            });
        return true; // Keep the message channel open for the async response
    }
});