/**
 * auth.js — Login & Register page logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path.endsWith('login.html'))    initLogin();
  if (path.endsWith('register.html')) initRegister();
});

// ── Login ─────────────────────────────────────────────────────────────────────

function initLogin() {
  requireGuest();

  const form     = document.getElementById('login-form');
  const pwInput  = document.getElementById('password');
  const pwToggle = document.getElementById('pw-toggle');

  // Password visibility toggle
  pwToggle?.addEventListener('click', () => {
    const isText = pwInput.type === 'text';
    pwInput.type      = isText ? 'password' : 'text';
    pwToggle.textContent = isText ? '👁️' : '🙈';
  });

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    setLoading('login-btn', true);
    clearAlert('login-alert');

    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
      showAlert('login-alert', 'Please fill in all fields.');
      setLoading('login-btn', false, 'Sign In');
      return;
    }

    const { ok, data } = await API.login({ email, password });

    if (ok) {
      TokenStore.set(data.access_token, data.refresh_token, data.user);
      window.location.href = '/dashboard.html';
    } else {
      showAlert('login-alert', data?.error || 'Login failed. Please try again.');
      setLoading('login-btn', false, 'Sign In');
    }
  });
}

// ── Register ──────────────────────────────────────────────────────────────────

function initRegister() {
  requireGuest();

  const form     = document.getElementById('register-form');
  const pwInput  = document.getElementById('password');
  const pwToggle = document.getElementById('pw-toggle');
  const pwConf   = document.getElementById('confirm-password');
  const pwBar    = document.getElementById('pw-strength-bar');

  // Password visibility toggle
  pwToggle?.addEventListener('click', () => {
    const isText = pwInput.type === 'text';
    pwInput.type      = isText ? 'password' : 'text';
    pwToggle.textContent = isText ? '👁️' : '🙈';
  });

  // Password strength meter
  pwInput?.addEventListener('input', () => {
    const val = pwInput.value;
    let strength = 0;
    if (val.length >= 6)                    strength++;
    if (/[A-Z]/.test(val))                  strength++;
    if (/[0-9]/.test(val))                  strength++;
    if (/[^A-Za-z0-9]/.test(val))          strength++;

    const colors  = ['#ef4444','#f97316','#eab308','#10b981'];
    const widths  = ['25%','50%','75%','100%'];
    if (pwBar) {
      pwBar.style.width      = val.length ? widths[strength - 1] || '10%' : '0%';
      pwBar.style.background = colors[strength - 1] || '#ef4444';
    }
  });

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert('register-alert');

    const name     = document.getElementById('name').value.trim();
    const email    = document.getElementById('email').value.trim();
    const password = pwInput.value;
    const confirm  = pwConf.value;

    if (!name || !email || !password) {
      showAlert('register-alert', 'Please fill in all required fields.');
      return;
    }
    if (password.length < 6) {
      showAlert('register-alert', 'Password must be at least 6 characters.');
      return;
    }
    if (password !== confirm) {
      showAlert('register-alert', 'Passwords do not match.');
      return;
    }

    setLoading('register-btn', true);

    const { ok, data } = await API.register({ name, email, password });

    if (ok) {
      TokenStore.set(data.access_token, data.refresh_token, data.user);
      window.location.href = '/dashboard.html';
    } else {
      showAlert('register-alert', data?.error || 'Registration failed. Please try again.');
      setLoading('register-btn', false, 'Create Account');
    }
  });
}

// ── Helper ────────────────────────────────────────────────────────────────────

function clearAlert(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('show');
}
