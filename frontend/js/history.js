/**
 * history.js — Prediction history table with pagination, search, and CSV export
 */

let allPredictions = [];
let currentPage    = 1;
const PER_PAGE     = 10;

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth()) return;
  populateSidebarUser();
  await loadHistory();
  initSearch();
  initExport();
});

// ── Load & Render ─────────────────────────────────────────────────────────────

async function loadHistory(page = 1) {
  currentPage = page;
  const tableBody = document.getElementById('history-body');
  const paginEl   = document.getElementById('pagination');

  if (tableBody) tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--text-muted)">Loading…</td></tr>';

  const res = await API.getHistory(page, PER_PAGE);

  if (!res || !res.ok) {
    if (tableBody) tableBody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-title">Failed to load history</div></div></td></tr>';
    return;
  }

  allPredictions = res.data.predictions;
  renderTable(allPredictions);
  renderPagination(res.data.total, res.data.pages, page);
}

function renderTable(predictions) {
  const tableBody = document.getElementById('history-body');
  const totalEl   = document.getElementById('total-count');
  if (!tableBody) return;

  if (totalEl) totalEl.textContent = `${predictions.length} record${predictions.length !== 1 ? 's' : ''}`;

  if (predictions.length === 0) {
    tableBody.innerHTML = `
      <tr><td colspan="6">
        <div class="empty-state">
          <div class="empty-icon">🔬</div>
          <div class="empty-title">No predictions found</div>
          <div class="empty-desc">Tests you run will appear here.</div>
          <a href="/predict.html" class="btn btn-primary btn-sm" style="margin-top:1rem">Run First Test</a>
        </div>
      </td></tr>`;
    return;
  }

  tableBody.innerHTML = predictions.map((p, idx) => {
    const inputs = p.inputs;
    const bmi    = inputs.bmi ? parseFloat(inputs.bmi).toFixed(1) : '—';
    const age    = inputs.age ?? '—';

    return `
      <tr>
        <td style="color:var(--text-muted);font-size:.8rem">#${p.id}</td>
        <td style="font-size:.82rem">${fmtDate(p.created_at)}</td>
        <td>Age ${age} | BMI ${bmi}</td>
        <td>
          <span class="badge badge-${p.result === 'Positive' ? 'positive' : 'negative'}">
            ${p.result === 'Positive' ? '⚠️' : '✅'} ${p.result}
          </span>
        </td>
        <td>
          <div style="display:flex;align-items:center;gap:.5rem;min-width:100px">
            <div style="flex:1;height:5px;background:rgba(255,255,255,.1);border-radius:100px;overflow:hidden;">
              <div style="height:100%;width:${pct(p.confidence)};background:var(--gradient-main);border-radius:100px;"></div>
            </div>
            <span style="font-size:.78rem;color:var(--text-muted)">${pct(p.confidence)}</span>
          </div>
        </td>
        <td>
          <button class="btn btn-danger btn-sm" onclick="confirmDelete(${p.id}, this)">🗑 Delete</button>
        </td>
      </tr>`;
  }).join('');
}

// ── Pagination ────────────────────────────────────────────────────────────────

function renderPagination(total, pages, current) {
  const el = document.getElementById('pagination');
  if (!el || pages <= 1) { if (el) el.innerHTML = ''; return; }

  let html = `<button class="page-btn" onclick="loadHistory(${current - 1})" ${current === 1 ? 'disabled' : ''}>‹</button>`;
  for (let i = 1; i <= pages; i++) {
    html += `<button class="page-btn ${i === current ? 'active' : ''}" onclick="loadHistory(${i})">${i}</button>`;
  }
  html += `<button class="page-btn" onclick="loadHistory(${current + 1})" ${current === pages ? 'disabled' : ''}>›</button>`;
  el.innerHTML = html;
}

// ── Delete ────────────────────────────────────────────────────────────────────

async function confirmDelete(id, btn) {
  if (!confirm('Delete this prediction record?')) return;
  btn.disabled    = true;
  btn.textContent = '…';

  const res = await API.deleteHistory(id);
  if (res?.ok) {
    await loadHistory(currentPage);
  } else {
    btn.disabled    = false;
    btn.textContent = '🗑 Delete';
    alert('Failed to delete. Please try again.');
  }
}

// ── Search / filter ───────────────────────────────────────────────────────────

function initSearch() {
  const searchEl  = document.getElementById('search-input');
  const filterEl  = document.getElementById('filter-result');

  function applyFilter() {
    const query  = searchEl?.value.toLowerCase() || '';
    const filter = filterEl?.value || 'all';

    const filtered = allPredictions.filter(p => {
      const matchFilter = filter === 'all' || p.result.toLowerCase() === filter;
      const matchQuery  = !query
        || fmtDate(p.created_at).toLowerCase().includes(query)
        || p.result.toLowerCase().includes(query)
        || String(p.id).includes(query);
      return matchFilter && matchQuery;
    });

    renderTable(filtered);
  }

  searchEl?.addEventListener('input', applyFilter);
  filterEl?.addEventListener('change', applyFilter);
}

// ── CSV Export ────────────────────────────────────────────────────────────────

function initExport() {
  document.getElementById('export-btn')?.addEventListener('click', () => {
    if (allPredictions.length === 0) { alert('No data to export.'); return; }

    const headers = [
      'ID','Date','Age','Weight(kg)','Height(cm)','BMI','Blood Group','Pulse Rate',
      'Cycle Type','Cycle Length(days)','Marriage Years','Pregnant','Vitamin D3',
      'Skin Darkening','Pimples','Weight Gain','Hair Growth','Hair Loss','Fast Food','Reg Exercise',
      'Follicles(L)','Follicles(R)','Avg F-Size(L) mm','Avg F-Size(R) mm',
      'Result','Confidence'
    ];
    const rows    = allPredictions.map(p => {
      const d = p.inputs;
      const cycleLabel = d.cycle_type == 4 ? 'Irregular' : 'Regular';
      return [
        p.id, fmtDate(p.created_at),
        d.age, d.weight, d.height, d.bmi, d.blood_group, d.pulse_rate,
        cycleLabel, d.cycle_length, d.marriage_years,
        d.pregnant    == 1 ? 'Yes' : 'No',
        d.vitamin_d3,
        d.skin_darkening == 1 ? 'Yes' : 'No',
        d.pimples        == 1 ? 'Yes' : 'No',
        d.weight_gain    == 1 ? 'Yes' : 'No',
        d.hair_growth    == 1 ? 'Yes' : 'No',
        d.hair_loss      == 1 ? 'Yes' : 'No',
        d.fast_food      == 1 ? 'Yes' : 'No',
        d.reg_exercise   == 1 ? 'Yes' : 'No',
        d.follicle_left, d.follicle_right,
        d.avg_fsize_left, d.avg_fsize_right,
        p.result, pct(p.confidence),
      ].map(v => `"${v ?? ''}"`).join(',');
    });

    const csv  = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: 'pcos_history.csv' });
    a.click();
    URL.revokeObjectURL(url);
  });
}
