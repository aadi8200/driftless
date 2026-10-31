// DRIFTLESS — Active Tab Heartbeat & Precision Timer Content Script (Manifest V3)
(function() {
  // Only run on standard web pages
  if (!window.location.protocol.startsWith('http')) return;

  const rawDomain = window.location.hostname;
  if (!rawDomain) return;

  let heartbeatInterval = null;
  let isTabActive = !document.hidden && document.hasFocus();

  function isPageActiveAndFocused() {
    return !document.hidden && document.hasFocus();
  }

  function sendTick() {
    if (!isPageActiveAndFocused()) return;

    try {
      chrome.runtime.sendMessage({
        type: 'PAGE_HEARTBEAT_TICK',
        domain: rawDomain,
        url: window.location.href,
        timestamp: Date.now()
      }, response => {
        if (chrome.runtime.lastError) {
          // Extension reloaded or context invalidated
          stopHeartbeat();
          return;
        }

        if (response && response.blocked) {
          // Site limit reached or blocked by focus mode -> redirect immediately
          stopHeartbeat();
          const targetUrl = chrome.runtime.getURL(`blocked.html?site=${encodeURIComponent(response.domain || rawDomain)}`);
          if (window.location.href !== targetUrl) {
            window.location.replace(targetUrl);
          }
        }
      });
    } catch (e) {
      stopHeartbeat();
    }
  }

  function startHeartbeat() {
    if (heartbeatInterval) return;
    sendTick();
    heartbeatInterval = setInterval(() => {
      if (isPageActiveAndFocused()) {
        sendTick();
      } else {
        stopHeartbeat();
      }
    }, 1000);
  }

  function stopHeartbeat() {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
  }

  function handleStateChange() {
    const activeNow = isPageActiveAndFocused();
    if (activeNow) {
      startHeartbeat();
    } else {
      stopHeartbeat();
      try {
        chrome.runtime.sendMessage({
          type: 'PAGE_HEARTBEAT_PAUSE',
          domain: rawDomain,
          timestamp: Date.now()
        }, () => {
          if (chrome.runtime.lastError) {}
        });
      } catch (e) {}
    }
  }

  document.addEventListener('visibilitychange', handleStateChange);
  window.addEventListener('focus', handleStateChange);
  window.addEventListener('blur', handleStateChange);

  // Initial startup check
  if (isPageActiveAndFocused()) {
    startHeartbeat();
  }
})();

