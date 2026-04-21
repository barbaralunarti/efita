import { fetchApi } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('inscricao-form');
  const cpfInput = document.getElementById('cpf');
  const categoriaSelect = document.getElementById('categoria');
  const instituicaoInput = document.getElementById('instituicao');
  const matriculaGroup = document.getElementById('matricula-group');
  const temPosterCheck = document.getElementById('tem_poster');
  const posterSection = document.getElementById('poster-section');
  const formError = document.getElementById('form-error');
  const submitBtn = document.getElementById('submit-btn');

  // Máscara de CPF
  cpfInput.addEventListener('input', function (e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 11) value = value.slice(0, 11);
    
    if (value.length > 9) {
      value = value.replace(/^(\d{3})(\d{3})(\d{3})(\d{2}).*/, '$1.$2.$3-$4');
    } else if (value.length > 6) {
      value = value.replace(/^(\d{3})(\d{3})(\d{3}).*/, '$1.$2.$3');
    } else if (value.length > 3) {
      value = value.replace(/^(\d{3})(\d{3}).*/, '$1.$2');
    }
    
    e.target.value = value;
    e.target.classList.remove('is-invalid');
  });

  // Mostrar/Esconder campo de matrícula
  function checkMatriculaVisibility() {
    const isIta = instituicaoInput.value.trim().toUpperCase() === 'ITA';
    const precisaMatricula = ['graduacao', 'pos_graduacao'].includes(categoriaSelect.value);
    
    if (isIta && precisaMatricula) {
      matriculaGroup.classList.remove('hidden');
      document.getElementById('matricula_ita').required = true;
    } else {
      matriculaGroup.classList.add('hidden');
      document.getElementById('matricula_ita').required = false;
      document.getElementById('matricula_ita').value = '';
    }
  }

  instituicaoInput.addEventListener('input', checkMatriculaVisibility);
  categoriaSelect.addEventListener('change', checkMatriculaVisibility);

  // Mostrar/Esconder Pôster
  temPosterCheck.addEventListener('change', (e) => {
    if (e.target.checked) {
      posterSection.style.display = 'block';
      document.getElementById('titulo_poster').required = true;
      document.getElementById('resumo').required = true;
      document.getElementById('palavras_chave').required = true;
    } else {
      posterSection.style.display = 'none';
      document.getElementById('titulo_poster').required = false;
      document.getElementById('resumo').required = false;
      document.getElementById('palavras_chave').required = false;
    }
  });

  // Submit
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    formError.style.display = 'none';
    formError.innerText = '';
    
    // Validar CPF tamanho numérico
    const cpfDigits = cpfInput.value.replace(/\D/g, '');
    if (cpfDigits.length !== 11) {
      cpfInput.classList.add('is-invalid');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerText = 'Processando...';

    const payload = {
      cpf: cpfDigits,
      nome: document.getElementById('nome').value,
      email: document.getElementById('email').value,
      instituicao: document.getElementById('instituicao').value,
      categoria: categoriaSelect.value,
    };

    const matricula = document.getElementById('matricula_ita').value;
    if (matricula) {
      payload.matricula_ita = matricula;
    }

    if (temPosterCheck.checked) {
      payload.poster = {
        titulo: document.getElementById('titulo_poster').value,
        resumo: document.getElementById('resumo').value,
        palavras_chave: document.getElementById('palavras_chave').value
      };
    }

    try {
      const response = await fetchApi('/inscricao', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      // Sucesso
      document.getElementById('form-card').classList.add('hidden');
      const successScreen = document.getElementById('success-screen');
      successScreen.classList.remove('hidden');
      
      document.getElementById('success-protocolo').innerText = response.protocolo;
      document.getElementById('success-email').innerText = response.email;

    } catch (err) {
      formError.style.display = 'block';
      formError.innerText = err.message;
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerText = 'Finalizar Inscrição';
    }
  });
});
