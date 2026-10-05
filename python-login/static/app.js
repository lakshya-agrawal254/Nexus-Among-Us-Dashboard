const form = document.querySelector('#login-form');
const loginView = document.querySelector('#login-view');
const welcomeView = document.querySelector('#welcome-view');
const error = document.querySelector('#error');
const submit = document.querySelector('#submit');

function welcome(user, focus = true) {
  document.querySelector('#crew-name').textContent = user.name;
  document.querySelector('#crew-id').textContent = user.registration;
  loginView.hidden = true;
  welcomeView.hidden = false;
  document.querySelector('.login-card').setAttribute('aria-labelledby', 'welcome-title');
  document.querySelector('.card-code').textContent = '02 / ON BOARD';
  form.reset();
  if (focus) document.querySelector('#welcome-title').focus();
}

document.querySelector('#demo').addEventListener('click', () => {
  form.elements.registration.value = 'CREW001';
  form.elements.phone.value = '9876543210';
  error.hidden = true;
  submit.focus();
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  error.hidden = true;
  submit.disabled = true;
  submit.firstElementChild.textContent = 'Checking crew records…';
  try {
    const response = await fetch('/api/login', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({registration: form.elements.registration.value, phone: form.elements.phone.value})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not sign in. Please try again.');
    welcome(data);
  } catch (issue) {
    error.textContent = issue instanceof TypeError ? 'Connection lost. Check that the Python server is running and try again.' : issue.message;
    error.hidden = false;
  } finally {
    submit.disabled = false;
    submit.firstElementChild.textContent = 'Let me in';
  }
});

document.querySelector('#logout').addEventListener('click', async () => {
  const button = document.querySelector('#logout');
  const notice = document.querySelector('#logout-error');
  button.disabled = true;
  notice.hidden = true;
  try {
    const response = await fetch('/api/logout', {method: 'POST'});
    if (!response.ok) throw new Error('Could not sign out. Please try again.');
    welcomeView.hidden = true;
    loginView.hidden = false;
    error.hidden = true;
    document.querySelector('.login-card').setAttribute('aria-labelledby', 'form-title');
    document.querySelector('.card-code').textContent = '01 / CHECK IN';
    form.elements.registration.focus();
  } catch (issue) {
    notice.textContent = 'Could not sign out. Check your connection and try again.';
    notice.hidden = false;
  } finally { button.disabled = false; }
});

fetch('/api/me').then(async response => {
  if (response.ok) welcome(await response.json(), false);
}).catch(() => {});
