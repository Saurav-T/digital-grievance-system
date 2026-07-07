// Shared JavaScript for login and signup pages

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function setError(input, message) {
  const formGroup = input.closest('.form-group');
  if (!formGroup) return;

  const errorText = formGroup.querySelector('.error-message');
  if (errorText) {
    errorText.textContent = message;
  }

  input.classList.add('input-error');
}

function clearError(input) {
  const formGroup = input.closest('.form-group');
  if (!formGroup) return;

  const errorText = formGroup.querySelector('.error-message');
  if (errorText) {
    errorText.textContent = '';
  }

  input.classList.remove('input-error');
}

function showFormMessage(form, message, isSuccess = true) {
  const messageBox = form.querySelector('.form-message');
  if (!messageBox) return;

  messageBox.textContent = message;
  messageBox.style.color = isSuccess ? '#1f8a55' : '#c0392b';
}

function shakeForm(form) {
  const card = form.closest('.auth-card');
  if (!card) return;

  card.classList.remove('shake');
  void card.offsetWidth;
  card.classList.add('shake');
}

function updatePasswordStrength(passwordInput) {
  const strengthBar = document.getElementById('strengthBar');
  const strengthText = document.getElementById('strengthText');
  if (!strengthBar || !strengthText) return;

  const value = passwordInput.value;
  let score = 0;

  if (value.length >= 8) score += 35;
  if (/[A-Z]/.test(value)) score += 20;
  if (/[0-9]/.test(value)) score += 20;
  if (/[^A-Za-z0-9]/.test(value)) score += 25;

  const percent = Math.min(score, 100);
  strengthBar.style.width = `${percent}%`;

  if (percent < 35) {
    strengthBar.style.background = '#c0392b';
    strengthText.textContent = 'Weak password';
  } else if (percent < 70) {
    strengthBar.style.background = '#f5a623';
    strengthText.textContent = 'Fair password';
  } else {
    strengthBar.style.background = '#1f8a55';
    strengthText.textContent = 'Strong password';
  }
}

// Toggle password visibility for both login and signup forms
const passwordToggles = document.querySelectorAll('.toggle-password');
passwordToggles.forEach((button) => {
  button.addEventListener('click', () => {
    const inputId = button.getAttribute('data-toggle-password');
    const input = document.getElementById(inputId);
    if (!input) return;

    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    button.textContent = isPassword ? 'Hide' : 'Show';
  });
});

// Login form validation
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const emailInput = document.getElementById('loginEmail');
    const passwordInput = document.getElementById('loginPassword');

    const emailValue = emailInput.value.trim();
    const passwordValue = passwordInput.value.trim();

    let hasError = false;

    [emailInput, passwordInput].forEach(clearError);

    if (!emailValue) {
      setError(emailInput, 'Email is required.');
      hasError = true;
    } else if (!emailPattern.test(emailValue)) {
      setError(emailInput, 'Please enter a valid email address.');
      hasError = true;
    }

    if (!passwordValue) {
      setError(passwordInput, 'Password is required.');
      hasError = true;
    }

    if (hasError) {
      shakeForm(loginForm);
      showFormMessage(loginForm, 'Please correct the highlighted fields.', false);
      return;
    }

    showFormMessage(loginForm, 'Login details look good.');
  });

  loginForm.querySelectorAll('input').forEach((input) => {
    input.addEventListener('input', () => clearError(input));
  });
}

// Signup form validation
const signupForm = document.getElementById('signupForm');
if (signupForm) {
  const passwordInput = document.getElementById('signupPassword');
  const confirmInput = document.getElementById('confirmPassword');

  passwordInput.addEventListener('input', () => {
    updatePasswordStrength(passwordInput);
    clearError(passwordInput);
  });

  signupForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const firstNameInput = document.getElementById('firstName');
    const lastNameInput = document.getElementById('lastName');
    const emailInput = document.getElementById('signupEmail');
    const passwordValue = passwordInput.value.trim();
    const confirmValue = confirmInput.value.trim();

    let hasError = false;

    [firstNameInput, lastNameInput, emailInput, passwordInput, confirmInput].forEach(clearError);

    if (!firstNameInput.value.trim()) {
      setError(firstNameInput, 'First name is required.');
      hasError = true;
    }

    if (!lastNameInput.value.trim()) {
      setError(lastNameInput, 'Last name is required.');
      hasError = true;
    }

    if (!emailInput.value.trim()) {
      setError(emailInput, 'Email is required.');
      hasError = true;
    } else if (!emailPattern.test(emailInput.value.trim())) {
      setError(emailInput, 'Please enter a valid email address.');
      hasError = true;
    }

    if (passwordValue.length < 8) {
      setError(passwordInput, 'Password must be at least 8 characters.');
      hasError = true;
    }

    if (!confirmValue) {
      setError(confirmInput, 'Please confirm your password.');
      hasError = true;
    } else if (confirmValue !== passwordValue) {
      setError(confirmInput, 'Passwords do not match.');
      hasError = true;
    }

    if (hasError) {
      shakeForm(signupForm);
      showFormMessage(signupForm, 'Please complete every field correctly.', false);
      return;
    }

    showFormMessage(signupForm, 'Account created successfully.');
  });

  signupForm.querySelectorAll('input').forEach((input) => {
    input.addEventListener('input', () => clearError(input));
  });
}
