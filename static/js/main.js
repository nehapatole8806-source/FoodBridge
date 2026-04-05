/**
 * main.js
 * -------
 * Client-side interactivity for FoodBridge:
 * - Mobile nav toggle
 * - Flash auto-dismiss
 * - Donation card expiry countdown
 * - Form validation helpers
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Mobile Nav Toggle ─────────────────────────────────────
  const navToggle = document.getElementById('navToggle');
  const navLinks  = document.getElementById('navLinks');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('open');
      }
    });
  }

  // ── Auto-dismiss Flash Messages ──────────────────────────
  document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
      flash.style.opacity = '0';
      flash.style.transform = 'translateX(20px)';
      flash.style.transition = 'all 0.4s ease';
      setTimeout(() => flash.remove(), 400);
    }, 5000);
  });

  // ── Live Expiry Countdown on Donation Cards ───────────────
  function formatCountdown(ms) {
    if (ms <= 0) return 'Expired';
    const h = Math.floor(ms / 3600000);
    const m = Math.floor((ms % 3600000) / 60000);
    if (h > 48) return `${Math.floor(h/24)}d ${h%24}h left`;
    if (h > 0)  return `${h}h ${m}m left`;
    return `${m}m left`;
  }

  document.querySelectorAll('[data-expiry]').forEach(el => {
    const expiry = new Date(el.dataset.expiry);
    function tick() {
      const diff = expiry - Date.now();
      el.textContent = formatCountdown(diff);
      if (diff <= 0) {
        el.style.color = 'var(--amber-dark)';
        el.style.fontWeight = '600';
      } else if (diff < 3600000) {
        el.style.color = 'var(--amber-dark)'; // < 1 hour
      }
    }
    tick();
    setInterval(tick, 60000);
  });

  // ── Table Sort (admin / dashboard tables) ─────────────────
  document.querySelectorAll('.data-table th[data-sort]').forEach(th => {
    th.style.cursor = 'pointer';
    th.title = 'Click to sort';
    th.addEventListener('click', () => {
      const table = th.closest('table');
      const tbody = table.querySelector('tbody');
      const col   = Array.from(th.parentElement.children).indexOf(th);
      const asc   = th.dataset.sortDir !== 'asc';
      th.dataset.sortDir = asc ? 'asc' : 'desc';

      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {
        const aText = a.cells[col]?.textContent.trim() || '';
        const bText = b.cells[col]?.textContent.trim() || '';
        return asc ? aText.localeCompare(bText) : bText.localeCompare(aText);
      });
      rows.forEach(r => tbody.appendChild(r));
    });
  });

  // ── Confirm Dangerous Forms ───────────────────────────────
  // Backup for any forms with data-confirm that don't inline confirm
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!confirm(form.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  // ── Dashboard Section Smooth-scroll via sidebar links ─────
  document.querySelectorAll('.dash-nav-item[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        document.querySelectorAll('.dash-nav-item').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
      }
    });
  });

  // ── Character counter for textareas ──────────────────────
  document.querySelectorAll('textarea[maxlength]').forEach(ta => {
    const counter = document.createElement('small');
    counter.className = 'text-muted';
    ta.parentElement.appendChild(counter);
    function updateCounter() {
      const remaining = ta.maxLength - ta.value.length;
      counter.textContent = `${remaining} characters remaining`;
    }
    ta.addEventListener('input', updateCounter);
    updateCounter();
  });

});
