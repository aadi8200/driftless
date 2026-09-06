chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        console.log("You just switched to:", tab.title);
        console.log("The URL is:", tab.url);
        console.log("-----------------------");
    });
});