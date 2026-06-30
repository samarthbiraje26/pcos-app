/**
 * predict.js — Multi-step PCOS prediction form logic (22-feature model)
 */

let currentStep = 1;
const TOTAL_STEPS = 4;

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  populateSidebarUser();
  initBMICalc();
  initStepNavigation();
});

// ── BMI auto-calculator ───────────────────────────────────────────────────────

function initBMICalc() {
  const heightEl = document.getElementById('height');
  const weightEl = document.getElementById('weight');
  const bmiEl = document.getElementById('bmi');
  const bmiDisp = document.getElementById('bmi-display');

  function calcBMI() {
    const h = parseFloat(heightEl?.value);
    const w = parseFloat(weightEl?.value);
    if (h > 0 && w > 0) {
      const bmi = (w / ((h / 100) ** 2)).toFixed(1);
      if (bmiEl) bmiEl.value = bmi;
      if (bmiDisp) {
        bmiDisp.textContent = `BMI: ${bmi} — ${getBMICategory(bmi)}`;
        bmiDisp.style.color = getBMIColor(bmi);
      }
    }
  }

  heightEl?.addEventListener('input', calcBMI);
  weightEl?.addEventListener('input', calcBMI);
}

function getBMICategory(bmi) {
  if (bmi < 18.5) return 'Underweight';
  if (bmi < 25) return 'Normal';
  if (bmi < 30) return 'Overweight';
  return 'Obese';
}

function getBMIColor(bmi) {
  if (bmi < 18.5) return '#06b6d4';
  if (bmi < 25) return '#10b981';
  if (bmi < 30) return '#f97316';
  return '#ef4444';
}

// ── Step navigation ───────────────────────────────────────────────────────────

function initStepNavigation() {
  updateStepUI();

  document.getElementById('btn-next-1')?.addEventListener('click', () => {
    if (validateStep(1)) goToStep(2);
  });
  document.getElementById('btn-next-2')?.addEventListener('click', () => {
    if (validateStep(2)) goToStep(3);
  });
  document.getElementById('btn-next-3')?.addEventListener('click', () => {
    if (validateStep(3)) goToStep(4);
  });

  document.getElementById('btn-back-2')?.addEventListener('click', () => goToStep(1));
  document.getElementById('btn-back-3')?.addEventListener('click', () => goToStep(2));
  document.getElementById('btn-back-4')?.addEventListener('click', () => goToStep(3));

  document.getElementById('predict-form')?.addEventListener('submit', handleSubmit);
}

function goToStep(step) {
  currentStep = step;
  updateStepUI();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateStepUI() {
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    const section = document.getElementById(`step-${i}`);
    if (section) section.classList.toggle('active', i === currentStep);
  }
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    const dot = document.getElementById(`dot-${i}`);
    if (!dot) continue;
    dot.classList.remove('active', 'done');
    if (i < currentStep) dot.classList.add('done');
    if (i === currentStep) dot.classList.add('active');
  }
  for (let i = 1; i < TOTAL_STEPS; i++) {
    const conn = document.getElementById(`conn-${i}`);
    if (conn) conn.classList.toggle('done', i < currentStep);
  }
}

// ── Validation ────────────────────────────────────────────────────────────────

function validateStep(step) {
  clearAlert('predict-alert');

  if (step === 1) {
    const age = parseFloat(document.getElementById('age')?.value);
    const height = parseFloat(document.getElementById('height')?.value);
    const weight = parseFloat(document.getElementById('weight')?.value);
    const pulse = parseFloat(document.getElementById('pulse_rate')?.value);
    const bloodGroup = document.getElementById('blood_group')?.value;

    if (!age || age < 14 || age > 50)
      return alertAndReturn('Please enter a valid age (14–50).');
    if (!height || height < 100 || height > 220)
      return alertAndReturn('Please enter a valid height in cm (100–220).');
    if (!weight || weight < 25 || weight > 200)
      return alertAndReturn('Please enter a valid weight in kg (25–200).');
    if (!pulse || pulse < 40 || pulse > 140)
      return alertAndReturn('Please enter a valid pulse rate (40–140 bpm).');
    if (!bloodGroup)
      return alertAndReturn('Please select your blood group.');
  }

  if (step === 2) {
    const cycle = parseFloat(document.getElementById('cycle_length')?.value);
    const cycleType = document.querySelector('input[name="cycle_type"]:checked');
    const pregnant = document.querySelector('input[name="pregnant"]:checked');
    const vitD3Str = document.getElementById('vitamin_d3')?.value;

    if (!cycleType)
      return alertAndReturn('Please select your menstrual cycle type.');
    if (!cycle || cycle < 15 || cycle > 90)
      return alertAndReturn('Please enter a valid cycle length (15–90 days).');
    if (!pregnant)
      return alertAndReturn('Please indicate whether you are currently pregnant.');
    if (vitD3Str && (isNaN(parseFloat(vitD3Str)) || parseFloat(vitD3Str) < 0 || parseFloat(vitD3Str) > 150))
      return alertAndReturn('Please enter a valid Vitamin D3 level (0-150 ng/mL).');
  }

  if (step === 3) {
    const symptoms = ['skin_darkening', 'pimples', 'weight_gain', 'hair_growth', 'hair_loss', 'fast_food', 'reg_exercise'];
    for (const name of symptoms) {
      if (!document.querySelector(`input[name="${name}"]:checked`))
        return alertAndReturn('Please answer all symptom questions.');
    }
  }

  if (step === 4) {
    const fLeftStr = document.getElementById('follicle_left')?.value;
    const fRightStr = document.getElementById('follicle_right')?.value;
    const fsLeftStr = document.getElementById('avg_fsize_left')?.value;
    const fsRightStr = document.getElementById('avg_fsize_right')?.value;

    if (fLeftStr && (isNaN(parseFloat(fLeftStr)) || parseFloat(fLeftStr) < 0 || parseFloat(fLeftStr) > 50))
      return alertAndReturn('Please enter a valid number for Follicle (Left).');
    if (fRightStr && (isNaN(parseFloat(fRightStr)) || parseFloat(fRightStr) < 0 || parseFloat(fRightStr) > 50))
      return alertAndReturn('Please enter a valid number for Follicle (Right).');
    if (fsLeftStr && (isNaN(parseFloat(fsLeftStr)) || parseFloat(fsLeftStr) < 0 || parseFloat(fsLeftStr) > 50))
      return alertAndReturn('Please enter a valid size for Avg Follicle Size (Left).');
    if (fsRightStr && (isNaN(parseFloat(fsRightStr)) || parseFloat(fsRightStr) < 0 || parseFloat(fsRightStr) > 50))
      return alertAndReturn('Please enter a valid size for Avg Follicle Size (Right).');
  }

  return true;
}

function alertAndReturn(msg) {
  showAlert('predict-alert', msg, 'error');
  return false;
}

function clearAlert(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('show');
}

// ── Form submission ───────────────────────────────────────────────────────────

async function handleSubmit(e) {
  e.preventDefault();
  if (!validateStep(4)) return;

  setLoading('submit-btn', true);
  clearAlert('predict-alert');

  const payload = collectFormData();
  const res = await API.predict(payload);

  setLoading('submit-btn', false, '🔬 Get My Result');

  if (!res || !res.ok) {
    showAlert('predict-alert', res?.data?.error || 'Prediction failed. Please try again.', 'error');
    return;
  }

  showResult(res.data);
}

// ── Collect all 22 form fields ────────────────────────────────────────────────

function collectFormData() {
  const getNum = (id) => parseFloat(document.getElementById(id)?.value) || 0;
  const getOpt = (id) => {
    const val = document.getElementById(id)?.value;
    return (val === '' || val == null) ? null : parseFloat(val);
  };
  const getRadio = (name) => {
    const el = document.querySelector(`input[name="${name}"]:checked`);
    return el ? parseFloat(el.value) : 0;
  };

  return {
    // Step 1 — Personal metrics
    age: getNum('age'),
    weight: getNum('weight'),
    height: getNum('height'),
    bmi: getNum('bmi'),
    blood_group: getNum('blood_group'),
    pulse_rate: getNum('pulse_rate'),

    // Step 2 — Cycle & history
    cycle_type: getRadio('cycle_type'),     // 2=Regular, 4=Irregular
    cycle_length: getNum('cycle_length'),
    marriage_years: getNum('marriage_years'),
    pregnant: getRadio('pregnant'),        // 0 or 1
    vitamin_d3: getOpt('vitamin_d3'),
    follicle_left: getOpt('follicle_left'),
    follicle_right: getOpt('follicle_right'),
    avg_fsize_left: getOpt('avg_fsize_left'),
    avg_fsize_right: getOpt('avg_fsize_right'),

    // Step 3 — Symptoms (0 or 1)
    skin_darkening: getRadio('skin_darkening'),
    pimples: getRadio('pimples'),
    weight_gain: getRadio('weight_gain'),
    hair_growth: getRadio('hair_growth'),
    hair_loss: getRadio('hair_loss'),
    fast_food: getRadio('fast_food'),
    reg_exercise: getRadio('reg_exercise'),
  };
}

// ── Result display ────────────────────────────────────────────────────────────

function showResult(data) {
  document.getElementById(`step-${currentStep}`)?.classList.remove('active');

  const resultEl = document.getElementById('result-section');
  if (!resultEl) return;

  const isPositive = data.result === 'Positive';
  const conf = Math.round(data.confidence * 100);

  // Risk label based on confidence bands (matching notebook: ≤35% Low, ≤65% Moderate, >65% High)
  let riskLabel = 'Low Risk';
  let riskColor = '#10b981';
  if (isPositive) {
    if (conf >= 65) { riskLabel = 'High Risk'; riskColor = '#ef4444'; }
    else { riskLabel = 'Moderate Risk'; riskColor = '#f97316'; }
  }

  resultEl.innerHTML = `
    <div class="result-reveal result-${isPositive ? 'positive' : 'negative'} show">
      <div class="result-icon">${isPositive ? '⚠️' : '✅'}</div>
      <div class="result-label">${data.result}</div>
      <div style="font-size:.9rem;font-weight:700;color:${riskColor};margin:.25rem 0 .75rem">${riskLabel}</div>
      <p class="result-sub">
        ${isPositive
      ? 'Indicators suggest PCOS may be present. Please consult a gynaecologist for a clinical diagnosis.'
      : 'No strong PCOS indicators detected. Maintain healthy habits and consult a doctor if symptoms arise.'}
      </p>
      <div class="conf-label">Model Confidence</div>
      <div class="conf-bar"><div class="conf-fill" id="conf-fill"></div></div>
      <div class="conf-pct">${conf}%</div>
      <div style="margin-top:2rem;display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;">
        <button id="btn-new-test" class="btn btn-outline">🔄 New Test</button>
        <a href="/history.html" class="btn btn-ghost">📋 View History</a>
      </div>
    </div>`;

  resultEl.style.display = 'block';

  setTimeout(() => {
    const fill = document.getElementById('conf-fill');
    if (fill) fill.style.width = `${conf}%`;
  }, 200);

  document.getElementById('btn-new-test')?.addEventListener('click', resetForm);
  resultEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ── Reset ─────────────────────────────────────────────────────────────────────

function resetForm() {
  document.getElementById('predict-form')?.reset();
  const bmiEl = document.getElementById('bmi');
  const bmiDisp = document.getElementById('bmi-display');
  if (bmiEl) bmiEl.value = '';
  if (bmiDisp) bmiDisp.textContent = '';

  const resultEl = document.getElementById('result-section');
  if (resultEl) resultEl.style.display = 'none';

  currentStep = 1;
  updateStepUI();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
