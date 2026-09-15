// storage.js
function saveBreakCount(count) {
  chrome.storage.local.set({ breakCount: count });
}

function getBreakCount(callback) {
  chrome.storage.local.get(["breakCount"], (result) => {
    callback(result.breakCount || 0);
  });
}