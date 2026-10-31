// Apply saved theme immediately
(function() {
  const t = localStorage.getItem('driftless-theme') || 'light';
  document.documentElement.setAttribute('data-theme', t);
})();

document.addEventListener('DOMContentLoaded', () => {
  // Extract blocked domain from URL params if present
  const params = new URLSearchParams(window.location.search);
  const domain = params.get('site');
  const reason = params.get('reason');

  if (domain) {
    const siteLabel = document.getElementById('siteLabel');
    if (siteLabel) {
      siteLabel.textContent = domain;
    }
    document.title = `Driftless — ${domain} Blocked`;
  }

  if (reason === 'shorts_reels') {
    const heading = document.querySelector('h1');
    if (heading) {
      heading.textContent = 'Shorts & Reels Blocked!';
    }
    const desc = document.querySelector('p');
    if (desc) {
      desc.textContent = 'Short-form video feed blocking is active. Driftless is keeping your focus protected.';
    }
  }

  const backToWorkBtn = document.getElementById('backToWorkBtn');
  if (backToWorkBtn) {
    backToWorkBtn.addEventListener('click', () => {
      // Direct user to a productive workspace or close tab
      window.location.href = 'https://github.com';
    });
  }
});

