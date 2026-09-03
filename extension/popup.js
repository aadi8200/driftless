function updateTime() {
    // Ab hum siteTimes ke sath-sath current chalne wali site bhi mangwa rahe hain
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
            
            displayHTML += `<p><strong>${displayName}:</strong> ${formattedTime}</p>`;
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