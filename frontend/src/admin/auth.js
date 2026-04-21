import { fetchApi } from '../api.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  const formError = document.getElementById('form-error');
  const submitBtn = document.getElementById('submit-btn');

  // Redirecionar se já estiver logado
  if (sessionStorage.getItem('admin_token')) {
    window.location.href = '/admin/dashboard.html';
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    formError.style.display = 'none';
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    submitBtn.disabled = true;
    submitBtn.innerText = 'Entrando...';

    try {
      // Usando URLSearchParams pois auth route no FastAPI normalmente espera Form data (OAuth2PasswordRequestForm)
      const body = new URLSearchParams();
      body.append('username', username);
      body.append('password', password);

      const response = await fetch('/api/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: body
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Credenciais inválidas');
      }

      sessionStorage.setItem('admin_token', data.access_token);
      window.location.href = '/admin/dashboard.html';
      
    } catch (err) {
      formError.style.display = 'block';
      formError.innerText = err.message;
      submitBtn.disabled = false;
      submitBtn.innerText = 'Entrar';
    }
  });
});
