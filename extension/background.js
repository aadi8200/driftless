console.log("🚀 DRIFTLESS DIMAAG ZINDA HAI! WATCHMAN DUTY PAR HAI.");

let activeSite = null;
let siteStartTime = 0;
const trackedSites = ["youtube.com", "instagram.com", "facebook.com", "reddit.com"];
const TIME_LIMIT = 60; // 60 Seconds
let notifiedSites = {};

chrome.tabs.onActivated.addListener(async (activeInfo) => {
    let tab = await chrome.tabs.get(activeInfo.tabId);
    checkSite(tab.url);
});

// 🔥 NAYA UPDATE: Ab Refresh karne par bhi pakad lega 🔥
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (tab.active && tab.url && changeInfo.status === 'complete') {
        checkSite(tab.url);
    }
});

chrome.tabs.onRemoved.addListener(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        if (tabs.length > 0) checkSite(tabs[0].url);
        else checkSite(""); 
    });
});

chrome.alarms.create("watchman", { periodInMinutes: 1 });

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "watchman") {
        console.log("🕵️‍♂️ Watchman jaag gaya aur check kar raha hai...");
        
        if (activeSite && siteStartTime) {
            let liveTimeSpent = Math.floor((Date.now() - siteStartTime) / 1000);
            chrome.storage.local.get(['siteTimes'], function(result) {
                let times = result.siteTimes || {};
                let totalTime = (times[activeSite] || 0) + liveTimeSpent;
                
                console.log(`⏱️ ${activeSite} par time ho gaya: ${totalTime} seconds`);
                
                if (totalTime < TIME_LIMIT) notifiedSites[activeSite] = false;
                
                if (totalTime >= TIME_LIMIT && !notifiedSites[activeSite]) {
                    notifiedSites[activeSite] = true;
                    console.log("🚨 Time over! Notification bhej raha hoon!");
                    
                    chrome.notifications.create("time_alert_" + Date.now(), {
                        type: 'basic',
                        iconUrl: 'icon.png', 
                        title: 'Driftless - Time Alert! 🚨',
                        message: `Bhai, ${activeSite} par time over ho gaya! Ab padhai karo!`,
                        priority: 2
                    }, function(id) {
                        if (chrome.runtime.lastError) console.error("❌ Notification Error:", chrome.runtime.lastError);
                        else console.log("✅ Notification successfully sent to Windows!");
                    });
                }
            });
        }
    }
});

function checkSite(url) {
    if (!url) url = "";
    let matchedSite = trackedSites.find(site => url.includes(site));

    if (activeSite !== matchedSite) {
        if (activeSite) {
            let timeSpent = Math.floor((Date.now() - siteStartTime) / 1000);
            let siteToSave = activeSite;
            chrome.storage.local.get(['siteTimes'], function(result) {
                let times = result.siteTimes || {};
                times[siteToSave] = (times[siteToSave] || 0) + timeSpent;
                chrome.storage.local.set({ siteTimes: times, currentActiveSite: null, currentStartTime: null });
            });
        }

        if (matchedSite) {
            activeSite = matchedSite;
            siteStartTime = Date.now();
            chrome.storage.local.set({ currentActiveSite: activeSite, currentStartTime: siteStartTime });
            console.log(`🟢 Started tracking: ${activeSite}`);
        } else {
            activeSite = null;
            chrome.storage.local.set({ currentActiveSite: null, currentStartTime: null });
        }
    }
}