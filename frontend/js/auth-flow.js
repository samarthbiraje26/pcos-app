/**
 * auth-flow.js - Login, register, forgot-password, and reset-password page logic.
 */

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path.endsWith('login.html')) initLogin();
  if (path.endsWith('register.html')) initRegister();
  if (path.endsWith('forgot-password.html')) initForgotPassword();
  if (path.endsWith('reset-password.html')) initResetPassword();
});

function initLogin() {
  requireGuest();

  const form = document.getElementById('login-form');
  const pwInput = document.getElementById('password');
  const pwToggle = document.getElementById('pw-toggle');

  bindPasswordToggle(pwInput, pwToggle);

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    setLoading('login-btn', true);
    clearAlert('login-alert');

    const email = document.getElementById('email').value.trim();
    const password = pwInput.value;

    if (!email || !password) {
      showAlert('login-alert', 'Please fill in all fields.');
      setLoading('login-btn', false, 'Sign In');
      return;
    }

    const { ok, data } = await API.login({ email, password });

    if (ok) {
      TokenStore.set(data.access_token, data.refresh_token, data.user);
      window.location.href = '/dashboard.html';
      return;
    }

    showAlert('login-alert', data?.error || 'Login failed. Please try again.');
    setLoading('login-btn', false, 'Sign In');
  });
}

function initRegister() {
  requireGuest();

  const form = document.getElementById('register-form');
  const pwInput = document.getElementById('password');
  const pwToggle = document.getElementById('pw-toggle');
  const pwConf = document.getElementById('confirm-password');
  const pwBar = document.getElementById('pw-strength-bar');

  bindPasswordToggle(pwInput, pwToggle);

  pwInput?.addEventListener('input', () => {
    const val = pwInput.value;
    let strength = 0;
    if (val.length >= 6) strength++;
    if (/[A-Z]/.test(val)) strength++;
    if (/[0-9]/.test(val)) strength++;
    if (/[^A-Za-z0-9]/.test(val)) strength++;

    const colors = ['#ef4444', '#f97316', '#eab308', '#10b981'];
    const widths = ['25%', '50%', '75%', '100%'];
    if (pwBar) {
      pwBar.style.width = val.length ? widths[strength - 1] || '10%' : '0%';
      pwBar.style.background = colors[strength - 1] || '#ef4444';
    }
  });

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert('register-alert');

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = pwInput.value;
    const confirm = pwConf.value;

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
      return;
    }

    showAlert('register-alert', data?.error || 'Registration failed. Please try again.');
    setLoading('register-btn', false, 'Sign Up');
  });
}

function initForgotPassword() {
  requireGuest();

  const form = document.getElementById('forgot-password-form');

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert('forgot-password-alert');
    setLoading('forgot-password-btn', true);

    const email = document.getElementById('email').value.trim();
    if (!email) {
      showAlert('forgot-password-alert', 'Please enter your email address.');
      setLoading('forgot-password-btn', false, 'Send Reset Link');
      return;
    }

    const { ok, data } = await API.forgotPassword({ email });
    if (ok) {
      showAlert(
        'forgot-password-alert',
        data?.message || 'If an account exists for this email, a reset link has been sent.',
        'success'
      );
      form.reset();
    } else {
      showAlert('forgot-password-alert', data?.error || 'Unable to send reset email.');
    }

    setLoading('forgot-password-btn', false, 'Send Reset Link');
  });
}

function initResetPassword() {
  requireGuest();

  const form = document.getElementById('reset-password-form');
  const pwInput = document.getElementById('password');
  const pwToggle = document.getElementById('pw-toggle');
  const pwConf = document.getElementById('confirm-password');
  const submitBtn = document.getElementById('reset-password-btn');
  const token = new URLSearchParams(window.location.search).get('token');

  bindPasswordToggle(pwInput, pwToggle);

  if (!token) {
    showAlert('reset-password-alert', 'This password reset link is invalid.');
    if (submitBtn) submitBtn.disabled = true;
    return;
  }

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert('reset-password-alert');
    setLoading('reset-password-btn', true);

    const password = pwInput.value;
    const confirm = pwConf.value;

    if (!password || !confirm) {
      showAlert('reset-password-alert', 'Please fill in both password fields.');
      setLoading('reset-password-btn', false, 'Update Password');
      return;
    }
    if (password.length < 6) {
      showAlert('reset-password-alert', 'Password must be at least 6 characters.');
      setLoading('reset-password-btn', false, 'Update Password');
      return;
    }
    if (password !== confirm) {
      showAlert('reset-password-alert', 'Passwords do not match.');
      setLoading('reset-password-btn', false, 'Update Password');
      return;
    }

    const { ok, data } = await API.resetPassword({ token, password });
    if (ok) {
      showAlert('reset-password-alert', data?.message || 'Password updated successfully.', 'success');
      form.reset();
      setTimeout(() => {
        window.location.href = '/login.html';
      }, 1500);
      return;
    }

    showAlert('reset-password-alert', data?.error || 'Unable to reset password.');
    setLoading('reset-password-btn', false, 'Update Password');
  });
}

function bindPasswordToggle(input, toggle) {
  toggle?.addEventListener('click', () => {
    const isText = input.type === 'text';
    input.type = isText ? 'password' : 'text';
    toggle.textContent = isText ? 'Show' : 'Hide';
  });
}

function clearAlert(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('show');
}
