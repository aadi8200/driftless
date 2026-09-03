const TRACKED_SITES = ["youtube.com", "instagram.com", "facebook.com", "reddit.com"];
const TIME_LIMIT_SECONDS = 60; // 1 minute limit for notification
const ALARM_NAME = "driftless_time_check";

let timerTimeout = null;

// Synchronous top-level event listeners (Manifest V3 requirement)

// 1. Tab switch listener
chrome.tabs.onActivated.addListener(async (activeInfo) => {
    try {
        const tab = await chrome.tabs.get(activeInfo.tabId);
        await checkSite(tab?.url || "");
    } catch (err) {
        // Tab may have closed before info was fetched
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
                scheduleCheck(TIME_LIMIT_SECONDS);
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

        // Calculate remaining seconds until 1-minute limit
        const alreadySpent = siteTimes[matchedSite] || 0;
        const remainingSeconds = TIME_LIMIT_SECONDS - alreadySpent;

        if (remainingSeconds <= 0) {
            // Already hit 1 minute, notify if not already done
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

    const liveTime = Math.floor((Date.now() - siteStartTime) / 1000);
    const totalSeconds = (siteTimes[activeSite] || 0) + liveTime;

    if (totalSeconds >= TIME_LIMIT_SECONDS) {
        if (!notifiedSites[activeSite]) {
            await sendNotification(activeSite, totalSeconds);
            notifiedSites[activeSite] = true;
            await chrome.storage.local.set({ notifiedSites });
        }
    } else {
        // Still have some time remaining, reschedule
        const remaining = TIME_LIMIT_SECONDS - totalSeconds;
        scheduleCheck(remaining);
    }
}

// Send system notification
async function sendNotification(site, totalSeconds) {
    const displayName = site.split(".")[0].charAt(0).toUpperCase() + site.split(".")[0].slice(1);
    const minutes = Math.floor(totalSeconds / 60) || 1;
    const timeText = `${minutes} minute${minutes > 1 ? "s" : ""}`;

    await chrome.notifications.create(`driftless-${site}-${Date.now()}`, {
        type: "basic",
        iconUrl: "icons/icon-128.png",
        title: "Driftless - Focus Alert",
        message: `You've spent ${timeText} on ${displayName}! Time to refocus on your goals.`,
        priority: 2
    });
}