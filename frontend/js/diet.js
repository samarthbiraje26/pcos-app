document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    populateSidebarUser();
    loadDietPlan();
  
    document.getElementById('regenerate-btn')?.addEventListener('click', regeneratePlan);
  });
  
  async function loadDietPlan() {
    setLoading('regenerate-btn', true);
    const res = await API.getDietPlan();
    setLoading('regenerate-btn', false, 'Regenerate Plan');
  
    if (res && res.ok && res.data && res.data.data) {
      renderDietPlan(res.data.data);
    } else {
      showAlert('diet-alert', 'Failed to load diet plan. Please try again later.', 'error');
    }
  }
  
  async function regeneratePlan() {
    setLoading('regenerate-btn', true);
    const res = await API.regenerateDietPlan();
    setLoading('regenerate-btn', false, 'Regenerate Plan');
  
    if (res && res.ok && res.data && res.data.data) {
      renderDietPlan(res.data.data);
    } else {
      showAlert('diet-alert', 'Failed to regenerate diet plan.', 'error');
    }
  }
  
  function renderDietPlan(plan) {
    const contentBody = document.getElementById('diet-content');
    contentBody.innerHTML = `
      <div class="diet-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
        
        <!-- Today's Meal Plan -->
        <div class="card">
          <h2 class="step-title" style="margin-bottom: 1rem;">🍽️ Today's Plan</h2>
          <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div><strong style="color:var(--primary)">Breakfast:</strong> <span style="color:var(--text-muted)">${plan.today.breakfast}</span></div>
            <div><strong style="color:var(--primary)">Lunch:</strong> <span style="color:var(--text-muted)">${plan.today.lunch}</span></div>
            <div><strong style="color:var(--primary)">Snacks:</strong> <span style="color:var(--text-muted)">${plan.today.snacks}</span></div>
            <div><strong style="color:var(--primary)">Dinner:</strong> <span style="color:var(--text-muted)">${plan.today.dinner}</span></div>
          </div>
        </div>
  
        <!-- Macros -->
        <div class="card">
          <h2 class="step-title" style="margin-bottom: 1rem;">📊 Daily Targets</h2>
          <div style="display: flex; flex-direction: column; gap: .75rem;">
            <div style="display:flex; justify-content:space-between; padding:.5rem; background:var(--bg-hover); border-radius:6px;">
              <span>Calories</span><strong>${plan.macros.calories} kcal</strong>
            </div>
            <div style="display:flex; justify-content:space-between; padding:.5rem; background:var(--bg-hover); border-radius:6px;">
              <span>Protein</span><strong>${plan.macros.protein}g</strong>
            </div>
            <div style="display:flex; justify-content:space-between; padding:.5rem; background:var(--bg-hover); border-radius:6px;">
              <span>Carbohydrates</span><strong>${plan.macros.carb}g</strong>
            </div>
            <div style="display:flex; justify-content:space-between; padding:.5rem; background:var(--bg-hover); border-radius:6px;">
              <span>Fat</span><strong>${plan.macros.fat}g</strong>
            </div>
          </div>
        </div>
  
      </div>
  
      <div class="diet-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 1.5rem;">
        
        <!-- Foods to Avoid vs Recommended -->
         <div class="card">
          <h2 class="step-title" style="margin-bottom: 1rem; color: #10b981;">✅ Recommended</h2>
          <ul style="padding-left:1.5rem; color:var(--text-muted); line-height: 1.8;">
            ${plan.recommended.map(f => `<li>${f}</li>`).join('')}
          </ul>
        </div>
  
        <div class="card" style="border-top: 4px solid #ef4444;">
          <h2 class="step-title" style="margin-bottom: 1rem; color: #ef4444;">🚫 Foods to Avoid</h2>
          <ul style="padding-left:1.5rem; color:var(--text-muted); line-height: 1.8;">
            ${plan.avoid.map(f => `<li>${f}</li>`).join('')}
          </ul>
        </div>
  
      </div>
  
      <div class="card" style="margin-top: 1.5rem; border-color: var(--border); background: var(--bg-hover);">
        <h2 class="step-title" style="margin-bottom: 1rem;">📅 Weekly Overview</h2>
        <p style="color:var(--text); line-height:1.6;">${plan.weekly_overview}</p>
      </div>
    `;
  }
