document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  populateSidebarUser();
  loadAwareness();

  document.getElementById('refresh-tips-btn')?.addEventListener('click', refreshTips);
});

async function loadAwareness() {
  const content = document.getElementById('awareness-content');
  content.innerHTML = `<div style="text-align:center;padding:4rem;color:var(--text-muted)">Loading awareness content...</div>`;

  const res = await API.getAwareness();

  if (res && res.ok && res.data && res.data.data) {
    renderAwareness(res.data.data);
  } else {
    content.innerHTML = `<div class="card" style="text-align:center;padding:3rem;color:var(--text-muted)">
      <p>Unable to load awareness content. Please try again later.</p>
    </div>`;
  }
}

async function refreshTips() {
  const btn = document.getElementById('refresh-tips-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>'; }

  const res = await API.refreshAwarenessTips();

  if (btn) { btn.disabled = false; btn.textContent = '🔄 Refresh Tips'; }

  if (res && res.ok && res.data && res.data.data) {
    renderTipsSection(res.data.data.lifestyle_tips);
  }
}

function renderAwareness(data) {
  const content = document.getElementById('awareness-content');

  content.innerHTML = `
    <!-- What is PCOS -->
    <div class="awareness-hero-card card" id="section-what-is">
      <div class="awareness-hero-accent"></div>
      <h2 class="awareness-section-title">💜 ${data.what_is_pcos.title}</h2>
      <p class="awareness-hero-desc">${data.what_is_pcos.description}</p>
      <div class="awareness-stats-row">
        ${data.what_is_pcos.key_stats.map(s => `
          <div class="awareness-stat-chip">
            <span class="awareness-stat-dot"></span>
            <span>${s}</span>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Symptoms -->
    <div id="section-symptoms" style="margin-top:2rem;">
      <h2 class="awareness-section-title" style="margin-bottom:1rem;">🩺 Common Symptoms</h2>
      <div class="awareness-grid symptoms-grid">
        ${data.symptoms.map(s => `
          <div class="awareness-symptom-card card">
            <div class="symptom-icon">${s.icon}</div>
            <div>
              <div class="symptom-name">${s.name}</div>
              <div class="symptom-desc">${s.desc}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Causes -->
    <div id="section-causes" style="margin-top:2rem;">
      <h2 class="awareness-section-title" style="margin-bottom:1rem;">🔬 Causes & Risk Factors</h2>
      <div class="card">
        <div class="causes-list">
          ${data.causes.map((c, i) => `
            <div class="cause-item">
              <div class="cause-number">${i + 1}</div>
              <div>
                <div class="cause-title">${c.title}</div>
                <div class="cause-desc">${c.desc}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>

    <!-- Myths vs Facts -->
    <div id="section-myths" style="margin-top:2rem;">
      <h2 class="awareness-section-title" style="margin-bottom:1rem;">🧠 Myths vs Facts</h2>
      <div class="myths-container">
        ${data.myths_vs_facts.map((mf, i) => `
          <div class="myth-fact-row card ${i % 2 === 0 ? 'mf-even' : 'mf-odd'}">
            <div class="mf-side myth-side">
              <span class="mf-badge myth-badge">❌ Myth</span>
              <p>${mf.myth}</p>
            </div>
            <div class="mf-divider"></div>
            <div class="mf-side fact-side">
              <span class="mf-badge fact-badge">✅ Fact</span>
              <p>${mf.fact}</p>
            </div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Lifestyle Tips (dynamic) -->
    <div id="section-tips" style="margin-top:2rem;">
      <div class="flex-between" style="margin-bottom:1rem;flex-wrap:wrap;gap:.5rem;">
        <h2 class="awareness-section-title">🌿 Personalized Lifestyle Tips</h2>
        <button id="refresh-tips-btn" class="btn btn-outline btn-sm">🔄 Refresh Tips</button>
      </div>
      <div id="tips-content"></div>
    </div>

    <!-- When to See a Doctor -->
    <div id="section-doctor" style="margin-top:2rem;">
      <h2 class="awareness-section-title" style="margin-bottom:1rem;">🏥 When to See a Doctor</h2>
      <div class="card doctor-card">
        <p class="doctor-intro">Consult a healthcare professional if you experience any of the following:</p>
        <div class="doctor-signs">
          ${data.when_to_see_doctor.map(sign => `
            <div class="doctor-sign-item">
              <span class="doctor-sign-icon">⚠️</span>
              <span>${sign}</span>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  // Render tips
  renderTipsSection(data.lifestyle_tips);

  // Re-bind refresh button after render
  document.getElementById('refresh-tips-btn')?.addEventListener('click', refreshTips);
}

function renderTipsSection(tips) {
  const container = document.getElementById('tips-content');
  if (!container) return;

  container.innerHTML = `
    <div class="card tips-card">
      <div class="tips-grid">
        ${tips.map((tip, i) => `
          <div class="tip-item" style="animation-delay: ${i * 0.08}s">
            <div class="tip-number">${i + 1}</div>
            <p class="tip-text">${tip}</p>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
