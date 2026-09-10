let incognitoAccessAllowed = false;

// 1. Check incognito permissions on startup
chrome.extension.isAllowedIncognitoAccess().then((allowed) => {
  incognitoAccessAllowed = allowed;
  console.log("Incognito access granted:", allowed);
});

// 2. Active Tab Tracking + Incognito Enforcement
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);

    // Agar tab incognito hai, toh usko turant kill karo
    if (tab.incognito) {
      console.warn("⚠️ Incognito Tab Detected! Terminating session...");

      // Remove the tab immediately
      chrome.tabs.remove(tab.id);

      // Trigger warning notification
      chrome.notifications.create({
        type: "basic",
        iconUrl: "icon.png", // Agar image na ho toh ignore karein
        title: "Driftless Enforcement",
        message: "Incognito mode is disabled during focus sessions!",
        priority: 2
      });
      return;
    }

    // Normal Tab Tracking Logs
    const currentTime = new Date().toLocaleTimeString();
    console.log("-----------------------------------------");
    console.log("You just switched to:", tab.title || "New Tab");
    console.log("The URL is:", tab.url || "about:blank");
    console.log("Switched at:", currentTime);
    console.log("-----------------------------------------");

  } catch (error) {
    console.error("Tab tracking error:", error);
  }
});

// 3. Extra Safety: Agar user naya Incognito Window khole toh turant window close karo
chrome.windows.onCreated.addListener((window) => {
  if (window.incognito) {
    console.warn("⚠️ Incognito Window Detected! Closing window...");
    chrome.windows.remove(window.id);
  }
});