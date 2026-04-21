import { fetchApi } from '../api.js';

document.addEventListener('DOMContentLoaded', () => {
  const btnDispararLote = document.getElementById('btn-disparar-lote');
  const tbody = document.querySelector('#emails-table tbody');

  // Adicionando listener dinâmico na tab, caso queiramos recarregar sempre que abrir
  document.querySelector('.nav-link[data-tab="emails"]').addEventListener('click', loadEmails);

  async function loadEmails() {
    try {
      const data = await fetchApi('/admin/emails/log');
      tbody.innerHTML = '';
      
      data.forEach(log => {
        const tr = document.createElement('tr');
        
        const badgeStatus = {
          'enviado': 'badge-success',
          'falha': 'badge-danger'
        };

        tr.innerHTML = `
          <td><strong>${log.destinatario}</strong></td>
          <td style="text-transform: capitalize;">${log.tipo}</td>
          <td>
            <span class="badge ${badgeStatus[log.status] || 'badge-pending'}">${log.status}</span>
            ${log.erro ? `<br><small style="color:var(--danger)">${log.erro}</small>` : ''}
          </td>
          <td>${new Date(log.enviado_em).toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch(e) {
      console.error(e);
    }
  }

  btnDispararLote.addEventListener('click', async () => {
    if(!confirm('Deseja iniciar o disparo em lote de e-mails para os aprovados?')) return;
    
    btnDispararLote.disabled = true;
    btnDispararLote.innerText = 'Iniciando...';
    
    try {
      const res = await fetchApi('/admin/emails/disparar-lote', { method: 'POST' });
      alert(res.mensagem || 'E-mails enfileirados com sucesso!');
      loadEmails();
    } catch(e) {
      alert(e.message);
    } finally {
      btnDispararLote.disabled = false;
      btnDispararLote.innerText = 'Iniciar Disparo em Lote';
    }
  });

});
