let incognitoAccessAllowed = false;

function initIncognitoGuard() {
  chrome.extension.isAllowedIncognitoAccess().then((allowed) => {
    incognitoAccessAllowed = allowed;
    console.log("Incognito access granted:", allowed);
  });
}