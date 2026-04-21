import { fetchApi } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('consulta-form');
  const cpfInput = document.getElementById('cpf');
  const formError = document.getElementById('form-error');
  const submitBtn = document.getElementById('submit-btn');
  const resultCard = document.getElementById('result-card');

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
  });

  const translateStatus = (status) => {
    const dict = {
      'pendente': 'Pendente',
      'aprovado': 'Aprovado',
      'recusado': 'Recusado',
      'nao_aplicavel': 'Não Aplicável (Isento)',
      'pago': 'Pago'
    };
    return dict[status] || status;
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    formError.style.display = 'none';
    resultCard.classList.add('hidden');
    
    const cpfDigits = cpfInput.value.replace(/\D/g, '');
    if (cpfDigits.length !== 11) {
      formError.style.display = 'block';
      formError.innerText = 'CPF inválido';
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerText = 'Buscando...';

    try {
      const data = await fetchApi(`/inscricao/${cpfDigits}`);
      
      document.getElementById('res-nome').innerText = data.nome;
      document.getElementById('res-protocolo').innerText = data.protocolo;
      document.getElementById('res-status-inscricao').innerText = translateStatus(data.status_inscricao);
      document.getElementById('res-status-pagamento').innerText = translateStatus(data.status_pagamento);
      document.getElementById('res-poster').innerText = data.tem_poster ? 'Sim' : 'Não';
      
      const posterStatusContainer = document.getElementById('poster-status-container');
      if (data.tem_poster && data.status_poster) {
        document.getElementById('res-status-poster').innerText = translateStatus(data.status_poster);
        posterStatusContainer.classList.remove('hidden');
      } else {
        posterStatusContainer.classList.add('hidden');
      }
      
      resultCard.classList.remove('hidden');
    } catch (err) {
      formError.style.display = 'block';
      formError.innerText = err.message || 'Inscrição não encontrada.';
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerText = 'Consultar';
    }
  });
});
