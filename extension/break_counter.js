// break-counter.js
let breakCount = 0;
let lastActiveTabId = null;

function initBreakCounter() {
  chrome.idle.setDetectionInterval(15); // seconds of inactivity before "idle"

  chrome.idle.onStateChanged.addListener((newState) => {
    if (newState === "idle" || newState === "locked") {
      breakCount++;
      console.log("Break detected. Total breaks this session:", breakCount);
      saveBreakCount(breakCount); // from storage.js
    }
  });

  chrome.tabs.onActivated.addListener((activeInfo) => {
    if (lastActiveTabId !== null && lastActiveTabId !== activeInfo.tabId) {
      console.log("Switched tabs — from", lastActiveTabId, "to", activeInfo.tabId);
    }
    lastActiveTabId = activeInfo.tabId;
  });
}