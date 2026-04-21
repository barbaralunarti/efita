import { fetchApi } from '../api.js';

// Verificar Auth
if (!sessionStorage.getItem('admin_token')) {
  window.location.href = '/admin/login.html';
}

document.addEventListener('DOMContentLoaded', () => {
  const navLinks = document.querySelectorAll('.nav-link');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const participantesTableBody = document.querySelector('#participantes-table tbody');
  
  let postersData = []; // Armazena dados dos posteres para o modal

  // Logout
  document.getElementById('logout-btn').addEventListener('click', () => {
    sessionStorage.removeItem('admin_token');
    window.location.href = '/admin/login.html';
  });

  // Tabs
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      navLinks.forEach(l => l.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      
      link.classList.add('active');
      const tabId = `tab-${link.dataset.tab}`;
      const tabElement = document.getElementById(tabId);
      if (tabElement) {
        tabElement.classList.add('active');
        loadTabData(link.dataset.tab);
      }
    });
  });

  // Export CSV
  document.getElementById('export-btn').addEventListener('click', async () => {
    try {
      const response = await fetch('/api/admin/export/csv', {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('admin_token')}` }
      });
      if (!response.ok) throw new Error('Erro ao exportar CSV');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `efita-participantes-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch(e) {
      alert(e.message);
    }
  });

  // Event Delegation for Table Buttons
  participantesTableBody.addEventListener('click', async (e) => {
    const target = e.target.closest('.btn-action');
    if (!target) return;

    const id = target.dataset.id;
    const action = target.dataset.action;

    console.log(`Action triggered: ${action} for id: ${id}`);

    if (action === 'aprovar') {
      // confirm() removido temporariamente para facilitar testes automatizados
      try {
        target.disabled = true;
        target.innerText = '...';
        await fetchApi(`/admin/participantes/${id}/status`, {
          method: 'PATCH',
          body: JSON.stringify({ status_inscricao: 'aprovado' })
        });
        await loadParticipantes();
      } catch(err) { 
        alert(err.message); 
        target.disabled = false;
        target.innerText = 'Aprovar';
      }
    } else if (action === 'pago') {
      try {
        target.disabled = true;
        target.innerText = '...';
        await fetchApi(`/admin/participantes/${id}/pagamento`, {
          method: 'PATCH',
          body: JSON.stringify({ status_pagamento: 'pago' })
        });
        await loadParticipantes();
      } catch(err) { 
        alert(err.message); 
        target.disabled = false;
        target.innerText = 'Pago';
      }
    }
  });

  // Load Data Route
  function loadTabData(tab) {
    if (tab === 'overview') loadOverview();
    else if (tab === 'participantes') loadParticipantes();
    else if (tab === 'posters') loadPosters();
  }

  async function loadOverview() {
    try {
      const data = await fetchApi('/admin/dashboard');
      const elements = {
        'stat-total': data.total_inscritos,
        'stat-aprovados': data.aprovados,
        'stat-pendentes': data.pendentes,
        'stat-pagamentos': data.pagamentos_confirmados
      };
      for (const [id, val] of Object.entries(elements)) {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
      }
    } catch(e) {
      if(e.message.includes('401')) window.location.href = '/admin/login.html';
      console.error(e);
    }
  }

  async function loadParticipantes() {
    try {
      const data = await fetchApi('/admin/participantes');
      if (!participantesTableBody) return;
      participantesTableBody.innerHTML = '';
      
      data.forEach(p => {
        const tr = document.createElement('tr');
        
        const badgeStatus = {
          'pendente': 'badge-pending',
          'aprovado': 'badge-success',
          'recusado': 'badge-danger'
        };
        
        const badgePagamento = {
          'pendente': 'badge-pending',
          'pago': 'badge-success',
          'nao_aplicavel': 'badge-success'
        };

        tr.innerHTML = `
          <td>EFITA-${String(p.id).padStart(5, '0')}</td>
          <td>
            <strong>${p.nome}</strong><br>
            <small style="color: var(--text-muted)">${p.email} | ${p.is_ita ? 'ITA' : 'Externo'}</small>
          </td>
          <td style="text-transform: capitalize;">${p.categoria.replace('_', ' ')}</td>
          <td><span class="badge ${badgeStatus[p.status_inscricao]}">${p.status_inscricao}</span></td>
          <td><span class="badge ${badgePagamento[p.status_pagamento]}">${p.status_pagamento.replace('_', ' ')}</span></td>
          <td>
            <button class="btn btn-outline btn-action" data-id="${p.id}" data-action="aprovar" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" ${p.status_inscricao === 'aprovado' ? 'disabled' : ''}>Aprovar</button>
            <button class="btn btn-outline btn-action" data-id="${p.id}" data-action="pago" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" ${p.status_pagamento === 'pago' ? 'disabled' : ''}>Pago</button>
          </td>
        `;
        participantesTableBody.appendChild(tr);
      });
    } catch(e) {
      console.error(e);
    }
  }

  async function loadPosters() {
    try {
      const data = await fetchApi('/admin/posters');
      postersData = data; // Salva para o modal
      const tbody = document.querySelector('#posters-table tbody');
      if (!tbody) return;
      tbody.innerHTML = '';
      
      const badgeStatus = {
        'pendente': 'badge-pending',
        'aprovado': 'badge-success',
        'recusado': 'badge-danger'
      };

      data.forEach((p, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${p.participante_nome}</strong><br><small class="text-muted">ID #${p.participante_id}</small></td>
          <td><strong>${p.titulo}</strong></td>
          <td>${new Date(p.created_at).toLocaleDateString()}</td>
          <td><span class="badge ${badgeStatus[p.status]}">${p.status}</span></td>
          <td>
            <button class="btn btn-outline poster-action-resumo" data-index="${index}" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; margin-right: 4px;">Ver Resumo</button>
            <button class="btn btn-outline btn-action poster-action-aprovar" data-id="${p.id}" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; margin-right: 4px;" ${p.status === 'aprovado' ? 'disabled' : ''}>Aprovar</button>
            <button class="btn btn-outline btn-action poster-action-recusar" data-id="${p.id}" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" ${p.status === 'recusado' ? 'disabled' : ''}>Recusar</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch(e) {
      console.error(e);
    }
  }

  // Poster Actions (Event Delegation)
  const postersTableBody = document.querySelector('#posters-table tbody');
  if (postersTableBody) {
    postersTableBody.addEventListener('click', async (e) => {
      // Abrir modal de resumo
      if (e.target.closest('.poster-action-resumo')) {
        const btn = e.target.closest('.poster-action-resumo');
        const p = postersData[btn.dataset.index];
        if (p) {
          document.getElementById('modal-poster-titulo').innerText = p.titulo;
          document.getElementById('modal-poster-autor').innerText = `Autor: ${p.participante_nome} (ID #${p.participante_id})`;
          document.getElementById('modal-poster-keywords').innerText = p.palavras_chave;
          document.getElementById('modal-poster-resumo').innerText = p.resumo;
          document.getElementById('poster-modal').style.display = 'flex';
        }
      }

      // Aprovar ou Recusar
      if (e.target.closest('.poster-action-aprovar') || e.target.closest('.poster-action-recusar')) {
        const btn = e.target.closest('button');
        const id = btn.dataset.id;
        const status = btn.classList.contains('poster-action-aprovar') ? 'aprovado' : 'recusado';
        
        try {
          btn.disabled = true;
          btn.innerText = '...';
          await fetchApi(`/admin/posters/${id}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status: status })
          });
          await loadPosters(); // Recarrega a tabela
        } catch(err) {
          alert(err.message);
          btn.disabled = false;
          btn.innerText = status === 'aprovado' ? 'Aprovar' : 'Recusar';
        }
      }
    });
  }

  // Fechar Modal
  document.getElementById('modal-poster-close')?.addEventListener('click', () => {
    document.getElementById('poster-modal').style.display = 'none';
  });
  document.getElementById('poster-modal')?.addEventListener('click', (e) => {
    if (e.target === document.getElementById('poster-modal')) {
      document.getElementById('poster-modal').style.display = 'none';
    }
  });

  // Search filter
  document.getElementById('search-input')?.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const rows = participantesTableBody.querySelectorAll('tr');
    rows.forEach(row => {
      const text = row.innerText.toLowerCase();
      row.style.display = text.includes(term) ? '' : 'none';
    });
  });

  // Inicializa primeira aba
  loadOverview();
});
