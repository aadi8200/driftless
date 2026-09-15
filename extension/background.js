// background.js — main orchestrator. Feature logic lives in separate files.

importScripts("incognito-guard.js", "break_counter.js", "storage.js");

initIncognitoGuard();
initBreakCounter();

chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);

    if (tab.incognito) {
      isFocusModeActive((active) => {
        if (active) {
          // Focus Mode is ON — incognito is not allowed to bypass it
          console.warn("Incognito Tab Detected during Focus Mode! Closing...");
          chrome.tabs.remove(tab.id);
          chrome.notifications.create({
            type: "basic",
            iconUrl: "icon.png", // ok if this doesn't exist yet, Chrome just skips the icon
            title: "Driftless Enforcement",
            message: "Incognito is disabled during your focus session.",
            priority: 2
          });
        } else {
          // Focus Mode is OFF — privacy-first, just skip tracking silently
          console.log("Incognito tab — skipping tracking (privacy, not in focus mode).");
        }
      });
      return; // stop here either way — never log incognito tab details below
    }

    // Normal Tab Tracking Logs
    const currentTime = new Date().toLocaleTimeString();
    console.log("--------------------------------------------");
    console.log("You just switched to:", tab.title || "New Tab");
    console.log("The URL is:", tab.url || "about:blank");
    console.log("Switched at:", currentTime);
    console.log("--------------------------------------------");

  } catch (error) {
    console.error("Tab tracking error:", error);
  }
});

// Extra safety: if a new incognito window opens, only close it if Focus Mode is active
chrome.windows.onCreated.addListener((window) => {
  if (window.incognito) {
    isFocusModeActive((active) => {
      if (active) {
        console.warn("Incognito Window Detected during Focus Mode! Closing...");
        chrome.windows.remove(window.id);
      }
      // if Focus Mode is off, do nothing — let the window stay open
    });
  }
});