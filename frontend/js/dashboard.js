/**
 * dashboard.js — Dashboard stats & recent predictions
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth()) return;
  populateSidebarUser();
  await loadStats();
  await loadRecentPredictions();
  animateCounters();
});

// ── Stats ─────────────────────────────────────────────────────────────────────

async function loadStats() {
  const res = await API.getStats();
  if (!res || !res.ok) return;

  const { total, positive, negative, last_prediction } = res.data;

  safeText('stat-total',    total    ?? 0);
  safeText('stat-positive', positive ?? 0);
  safeText('stat-negative', negative ?? 0);

  if (last_prediction) {
    safeText('stat-last-result', last_prediction.result);
    safeText('stat-last-date',   fmtDate(last_prediction.created_at));
    const el = document.getElementById('stat-last-result');
    if (el) {
      el.classList.add(last_prediction.result === 'Positive' ? 'text-positive' : 'text-negative');
    }
  } else {
    safeText('stat-last-result', '—');
    safeText('stat-last-date',   'No tests yet');
  }

  // Greet user
  const user = TokenStore.user;
  if (user) {
    const greeting = getGreeting();
    safeText('greeting-text', `${greeting}, ${user.name.split(' ')[0]}! 👋`);
  }
}

// ── Recent predictions table ──────────────────────────────────────────────────

async function loadRecentPredictions() {
  const res = await API.getHistory(1, 5);
  const container = document.getElementById('recent-list');
  if (!container) return;

  if (!res || !res.ok || res.data.predictions.length === 0) {
    container.innerHTML = `
      <tr><td colspan="4">
        <div class="empty-state" style="padding:2rem">
          <div class="empty-icon">🔬</div>
          <div class="empty-title">No predictions yet</div>
          <div class="empty-desc">Run your first PCOS detection test to see results here.</div>
        </div>
      </td></tr>`;
    return;
  }

  container.innerHTML = res.data.predictions.map(p => `
    <tr>
      <td>${fmtDate(p.created_at)}</td>
      <td>
        <span class="badge badge-${p.result === 'Positive' ? 'positive' : 'negative'}">
          ${p.result === 'Positive' ? '⚠️' : '✅'} ${p.result}
        </span>
      </td>
      <td>
        <div style="display:flex;align-items:center;gap:.5rem;">
          <div style="flex:1;height:5px;background:rgba(255,255,255,.1);border-radius:100px;overflow:hidden;">
            <div style="height:100%;width:${pct(p.confidence)};background:var(--gradient-main);border-radius:100px;"></div>
          </div>
          <span style="font-size:.8rem;color:var(--text-muted)">${pct(p.confidence)}</span>
        </div>
      </td>
      <td>
        <a href="/predict.html" class="btn btn-ghost btn-sm">Test Again</a>
      </td>
    </tr>
  `).join('');
}

// ── Animated number counters ──────────────────────────────────────────────────

function animateCounters() {
  document.querySelectorAll('[data-counter]').forEach(el => {
    const target = parseInt(el.textContent) || 0;
    let current  = 0;
    const step   = Math.max(1, Math.ceil(target / 30));
    const timer  = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(timer);
    }, 40);
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function safeText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}
