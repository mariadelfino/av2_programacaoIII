/* ── Biblioteca Digital ADS — Frontend JS ──────────────────────────────── */

const API = '';  // Flask serve na mesma origem

// ── Navegação ──────────────────────────────────────────────────────────────
function showPage(nome) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`page-${nome}`).classList.add('active');
  document.querySelectorAll('.nav-btn').forEach(b => {
    if (b.textContent.toLowerCase().includes(nome.replace('dashboard','dashboard').substring(0, 5))) {
      b.classList.add('active');
    }
  });
  // Carrega dados da página
  const loaders = {
    dashboard:   carregarDashboard,
    livros:      carregarLivros,
    categorias:  carregarCategorias,
    usuarios:    carregarUsuarios,
    emprestimos: carregarEmprestimos,
    rpa:         carregarLog,
  };
  loaders[nome]?.();
}

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast(msg, ms = 3000) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), ms);
}

// ── Modal ──────────────────────────────────────────────────────────────────
function abrirModal(id) { document.getElementById(id).classList.remove('hidden'); }
function fecharModal(id) { document.getElementById(id).classList.add('hidden'); }
function fecharModalOverlay(e, id) {
  if (e.target === document.getElementById(id)) fecharModal(id);
}

// ── API helper ─────────────────────────────────────────────────────────────
async function api(url, opts = {}) {
  const res = await fetch(API + url, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.erro || JSON.stringify(json));
  return json;
}

// ── Dashboard ──────────────────────────────────────────────────────────────
async function carregarDashboard() {
  try {
    const d = await api('/api/dashboard');
    document.getElementById('stat-livros').textContent       = d.total_livros;
    document.getElementById('stat-usuarios').textContent     = d.total_usuarios;
    document.getElementById('stat-categorias').textContent   = d.total_categorias;
    document.getElementById('stat-emprestimos').textContent  = d.emprestimos_ativos;
    document.getElementById('stat-atrasados').textContent    = d.emprestimos_atrasados;
    document.getElementById('stat-devolvidos').textContent   = d.emprestimos_devolvidos;
  } catch (e) { console.error(e); }
}

// ── Categorias ─────────────────────────────────────────────────────────────
let _categorias = [];

async function carregarCategorias() {
  _categorias = await api('/api/categorias');
  const grid = document.getElementById('grid-categorias');
  grid.innerHTML = _categorias.map(c => `
    <div class="dark-cat-card">
      <span class="dark-cat-count">${c.total_livros} livro(s)</span>
      <h3 class="dark-cat-name">${esc(c.nome)}</h3>
      <p class="dark-cat-desc">${esc(c.descricao || '—')}</p>
      <div class="dark-cat-footer">
        <button class="book-btn-icon" onclick="editarCategoria(${c.id})" title="Editar">✎</button>
        <button class="book-btn-icon danger" onclick="deletarCategoria(${c.id})" title="Remover">✕</button>
      </div>
    </div>
  `).join('') || '<div class="livros-empty">>> nenhuma categoria encontrada.</div>';
}

function abrirModal_categoria_limpo() {
  document.getElementById('modal-categoria-titulo').textContent = 'Nova Categoria';
  document.getElementById('categoria-id').value = '';
  document.getElementById('categoria-nome').value = '';
  document.getElementById('categoria-descricao').value = '';
  abrirModal('modal-categoria');
}

async function editarCategoria(id) {
  const c = _categorias.find(x => x.id === id);
  if (!c) return;
  document.getElementById('modal-categoria-titulo').textContent = 'Editar Categoria';
  document.getElementById('categoria-id').value = c.id;
  document.getElementById('categoria-nome').value = c.nome;
  document.getElementById('categoria-descricao').value = c.descricao || '';
  abrirModal('modal-categoria');
}

async function salvarCategoria(e) {
  e.preventDefault();
  const id = document.getElementById('categoria-id').value;
  const body = {
    nome: document.getElementById('categoria-nome').value,
    descricao: document.getElementById('categoria-descricao').value,
  };
  try {
    if (id) {
      await api(`/api/categorias/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      showToast('Categoria atualizada!');
    } else {
      await api('/api/categorias', { method: 'POST', body: JSON.stringify(body) });
      showToast('Categoria criada!');
    }
    fecharModal('modal-categoria');
    carregarCategorias();
  } catch (err) { showToast('Erro: ' + err.message); }
}

async function deletarCategoria(id) {
  if (!confirm('Remover esta categoria?')) return;
  try {
    await api(`/api/categorias/${id}`, { method: 'DELETE' });
    showToast('Categoria removida.');
    carregarCategorias();
  } catch (err) { showToast('Erro: ' + err.message); }
}

// Override do botão "Nova Categoria"
document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('[onclick="abrirModal(\'modal-categoria\')"]')
    ?.setAttribute('onclick', 'abrirModal_categoria_limpo()');
});

// ── Livros ─────────────────────────────────────────────────────────────────
async function carregarLivros() {
  const titulo    = document.getElementById('filtro-titulo')?.value || '';
  const autor     = document.getElementById('filtro-autor')?.value || '';
  const catId     = document.getElementById('filtro-categoria')?.value || '';
  const disponivel = document.getElementById('filtro-disponivel')?.checked || false;

  let url = `/api/livros?titulo=${encodeURIComponent(titulo)}&autor=${encodeURIComponent(autor)}`;
  if (catId) url += `&categoria_id=${catId}`;
  if (disponivel) url += '&disponivel=1';

  try {
    const livros = await api(url);
    const grid = document.getElementById('grid-livros');
    grid.innerHTML = livros.map(l => {
      const meta = `> ${esc((l.categoria || 'SEM CATEGORIA').toUpperCase())} | ${l.ano_publicacao || '—'}`;
      const dispText = `${l.disponivel}/${l.quantidade} DISPONÍVEL`;
      return `
        <div class="book-card">
          <span class="book-card-id">ID: ${String(l.id).padStart(3, '0')}</span>
          <span class="book-meta">${meta}</span>
          <span class="book-title">${esc(l.titulo)}</span>
          <span class="book-author">${esc(l.autor)}</span>
          <div class="book-footer">
            <span class="book-availability">${dispText}</span>
            <div class="book-actions">
              <button class="book-btn-icon" onclick="editarLivro(${l.id})" title="Editar">✎</button>
              <button class="book-btn-icon danger" onclick="deletarLivro(${l.id})" title="Remover">✕</button>
            </div>
          </div>
        </div>
      `;
    }).join('') || '<div class="livros-empty">>> nenhum livro encontrado.</div>';

    // Preenche filtro de categorias
    if (_categorias.length === 0) {
      _categorias = await api('/api/categorias');
    }
    popularSelectCategorias('filtro-categoria', catId);
    popularSelectCategorias('livro-categoria');
  } catch (err) { console.error(err); }
}

function popularSelectCategorias(selId, valorSelecionado) {
  const sel = document.getElementById(selId);
  if (!sel) return;
  const firstOpt = sel.id === 'filtro-categoria' ? '<option value="">Todas as categorias</option>' : '<option value="">Selecione...</option>';
  sel.innerHTML = firstOpt + _categorias.map(c =>
    `<option value="${c.id}" ${c.id == valorSelecionado ? 'selected' : ''}>${esc(c.nome)}</option>`
  ).join('');
}

async function editarLivro(id) {
  const l = await api(`/api/livros/${id}`);
  document.getElementById('modal-livro-titulo').textContent = 'Editar Livro';
  document.getElementById('livro-id').value = l.id;
  document.getElementById('livro-titulo').value = l.titulo;
  document.getElementById('livro-autor').value = l.autor;
  document.getElementById('livro-isbn').value = l.isbn || '';
  document.getElementById('livro-ano').value = l.ano_publicacao || '';
  document.getElementById('livro-quantidade').value = l.quantidade;
  if (_categorias.length === 0) _categorias = await api('/api/categorias');
  popularSelectCategorias('livro-categoria', l.categoria_id);
  abrirModal('modal-livro');
}

async function salvarLivro(e) {
  e.preventDefault();
  const id = document.getElementById('livro-id').value;
  const body = {
    titulo: document.getElementById('livro-titulo').value,
    autor: document.getElementById('livro-autor').value,
    isbn: document.getElementById('livro-isbn').value || null,
    ano_publicacao: parseInt(document.getElementById('livro-ano').value) || null,
    quantidade: parseInt(document.getElementById('livro-quantidade').value),
    categoria_id: parseInt(document.getElementById('livro-categoria').value),
  };
  try {
    if (id) {
      await api(`/api/livros/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      showToast('Livro atualizado!');
    } else {
      body.disponivel = body.quantidade;
      await api('/api/livros', { method: 'POST', body: JSON.stringify(body) });
      showToast('Livro cadastrado!');
    }
    fecharModal('modal-livro');
    carregarLivros();
  } catch (err) { showToast('Erro: ' + err.message); }
}

async function deletarLivro(id) {
  if (!confirm('Remover este livro?')) return;
  try {
    await api(`/api/livros/${id}`, { method: 'DELETE' });
    showToast('Livro removido.');
    carregarLivros();
  } catch (err) { showToast('Erro: ' + err.message); }
}

// Limpa form antes de abrir modal novo livro
document.addEventListener('DOMContentLoaded', () => {
  const btnNovoLivro = document.querySelector('[onclick="abrirModal(\'modal-livro\')"]');
  if (btnNovoLivro) {
    btnNovoLivro.addEventListener('click', async () => {
      document.getElementById('modal-livro-titulo').textContent = 'Novo Livro';
      document.getElementById('livro-id').value = '';
      document.getElementById('form-livro').reset();
      if (_categorias.length === 0) _categorias = await api('/api/categorias');
      popularSelectCategorias('livro-categoria');
    });
  }
});

// ── Usuários ───────────────────────────────────────────────────────────────
async function carregarUsuarios() {
  const nome = document.getElementById('filtro-usuario-nome')?.value || '';
  const usuarios = await api(`/api/usuarios?nome=${encodeURIComponent(nome)}`);
  document.getElementById('tbody-usuarios').innerHTML = usuarios.map(u => `
    <tr>
      <td>${u.id}</td>
      <td><strong>${esc(u.nome)}</strong></td>
      <td>${esc(u.email)}</td>
      <td>${esc(u.telefone || '—')}</td>
      <td><span class="badge badge-blue">${u.total_emprestimos}</span></td>
      <td>
        <div style="display:flex;gap:8px;align-items:center">
          <button class="book-btn-icon" onclick="editarUsuario(${u.id})" title="Editar">✎</button>
          <button class="book-btn-icon danger" onclick="deletarUsuario(${u.id})" title="Remover">✕</button>
        </div>
      </td>
    </tr>
  `).join('') || '<tr><td colspan="6" class="dark-table-empty">>> nenhum usuário encontrado.</td></tr>';
}

async function editarUsuario(id) {
  const u = await api(`/api/usuarios/${id}`);
  document.getElementById('modal-usuario-titulo').textContent = 'Editar Usuário';
  document.getElementById('usuario-id').value = u.id;
  document.getElementById('usuario-nome').value = u.nome;
  document.getElementById('usuario-email').value = u.email;
  document.getElementById('usuario-telefone').value = u.telefone || '';
  abrirModal('modal-usuario');
}

async function salvarUsuario(e) {
  e.preventDefault();
  const id = document.getElementById('usuario-id').value;
  const body = {
    nome: document.getElementById('usuario-nome').value,
    email: document.getElementById('usuario-email').value,
    telefone: document.getElementById('usuario-telefone').value || null,
  };
  try {
    if (id) {
      await api(`/api/usuarios/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      showToast('Usuário atualizado!');
    } else {
      await api('/api/usuarios', { method: 'POST', body: JSON.stringify(body) });
      showToast('Usuário cadastrado!');
    }
    fecharModal('modal-usuario');
    carregarUsuarios();
  } catch (err) { showToast('Erro: ' + err.message); }
}

async function deletarUsuario(id) {
  if (!confirm('Remover este usuário?')) return;
  try {
    await api(`/api/usuarios/${id}`, { method: 'DELETE' });
    showToast('Usuário removido.');
    carregarUsuarios();
  } catch (err) { showToast('Erro: ' + err.message); }
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.querySelector('[onclick="abrirModal(\'modal-usuario\')"]');
  if (btn) btn.addEventListener('click', () => {
    document.getElementById('modal-usuario-titulo').textContent = 'Novo Usuário';
    document.getElementById('usuario-id').value = '';
    document.getElementById('form-usuario').reset();
  });
});

// ── Empréstimos ────────────────────────────────────────────────────────────
async function carregarEmprestimos() {
  const status = document.getElementById('filtro-status')?.value || '';
  const emps = await api(`/api/emprestimos?status=${status}`);
  document.getElementById('tbody-emprestimos').innerHTML = emps.map(e => {
    const badges = { ativo: 'badge-blue', devolvido: 'badge-gray', atrasado: 'badge-red' };
    const hoje = new Date().toISOString().slice(0, 10);
    const atrasado = e.status === 'ativo' && e.data_devolucao_prevista < hoje;
    return `
      <tr>
        <td>${e.id}</td>
        <td>${esc(e.livro || '—')}</td>
        <td>${esc(e.usuario || '—')}</td>
        <td>${e.data_emprestimo || '—'}</td>
        <td style="${atrasado ? 'color:#ff7b71;font-weight:600' : ''}">${e.data_devolucao_prevista || '—'}</td>
        <td><span class="badge ${badges[e.status] || 'badge-gray'}">${e.status}</span></td>
        <td>
          <div style="display:flex;gap:8px;align-items:center">
            ${e.status === 'ativo' ? `<button class="tbl-action-btn" onclick="devolverLivro(${e.id})">devolver</button>` : ''}
            <button class="book-btn-icon danger" onclick="deletarEmprestimo(${e.id})" title="Remover">✕</button>
          </div>
        </td>
      </tr>
    `;
  }).join('') || '<tr><td colspan="7" class="dark-table-empty">>> nenhum empréstimo encontrado.</td></tr>';
}

async function abrirModalEmprestimo() {
  // Popula selects
  const [livros, usuarios] = await Promise.all([
    api('/api/livros?disponivel=1'),
    api('/api/usuarios'),
  ]);
  const selLivro = document.getElementById('emp-livro');
  selLivro.innerHTML = '<option value="">Selecione o livro...</option>' +
    livros.map(l => `<option value="${l.id}">${esc(l.titulo)} — ${esc(l.autor)} (${l.disponivel} disp.)</option>`).join('');
  const selUsuario = document.getElementById('emp-usuario');
  selUsuario.innerHTML = '<option value="">Selecione o usuário...</option>' +
    usuarios.map(u => `<option value="${u.id}">${esc(u.nome)} (${esc(u.email)})</option>`).join('');

  // Data mínima: amanhã
  const amanha = new Date();
  amanha.setDate(amanha.getDate() + 1);
  document.getElementById('emp-devolucao').min = amanha.toISOString().slice(0, 10);
  document.getElementById('emp-devolucao').value = '';

  abrirModal('modal-emprestimo');
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.querySelector('[onclick="abrirModal(\'modal-emprestimo\')"]');
  if (btn) { btn.removeAttribute('onclick'); btn.addEventListener('click', abrirModalEmprestimo); }
});

async function salvarEmprestimo(e) {
  e.preventDefault();
  const body = {
    livro_id: parseInt(document.getElementById('emp-livro').value),
    usuario_id: parseInt(document.getElementById('emp-usuario').value),
    data_devolucao_prevista: document.getElementById('emp-devolucao').value,
  };
  try {
    await api('/api/emprestimos', { method: 'POST', body: JSON.stringify(body) });
    showToast('Empréstimo registrado!');
    fecharModal('modal-emprestimo');
    carregarEmprestimos();
    carregarDashboard();
  } catch (err) { showToast('Erro: ' + err.message); }
}

async function devolverLivro(id) {
  if (!confirm('Confirmar devolução deste livro?')) return;
  try {
    await api(`/api/emprestimos/${id}/devolver`, { method: 'PUT' });
    showToast('Livro devolvido com sucesso!');
    carregarEmprestimos();
    carregarDashboard();
  } catch (err) { showToast('Erro: ' + err.message); }
}

async function deletarEmprestimo(id) {
  if (!confirm('Remover este registro de empréstimo?')) return;
  try {
    await api(`/api/emprestimos/${id}`, { method: 'DELETE' });
    showToast('Empréstimo removido.');
    carregarEmprestimos();
    carregarDashboard();
  } catch (err) { showToast('Erro: ' + err.message); }
}

// ── RPA ────────────────────────────────────────────────────────────────────
async function enviarEmail() {
  const id   = document.getElementById('rpa-email-id').value;
  const dest = document.getElementById('rpa-email-dest').value;
  const div  = document.getElementById('rpa-email-resultado');
  div.className = 'resultado';
  if (!id) { div.className = 'resultado erro'; div.textContent = 'Informe o ID do empréstimo.'; return; }
  try {
    const r = await api('/api/rpa/notificar-email', {
      method: 'POST',
      body: JSON.stringify({ emprestimo_id: parseInt(id), destinatario: dest || undefined }),
    });
    div.className = 'resultado ' + (r.sucesso ? 'ok' : 'erro');
    div.textContent = r.mensagem;
  } catch (err) {
    div.className = 'resultado erro';
    div.textContent = err.message;
  }
}

async function enviarWhatsApp() {
  const id  = document.getElementById('rpa-wpp-id').value;
  const tel = document.getElementById('rpa-wpp-tel').value;
  const div = document.getElementById('rpa-wpp-resultado');
  div.className = 'resultado';
  if (!id || !tel) { div.className = 'resultado erro'; div.textContent = 'Informe ID e telefone.'; return; }
  try {
    const r = await api('/api/rpa/notificar-whatsapp', {
      method: 'POST',
      body: JSON.stringify({ emprestimo_id: parseInt(id), telefone: tel }),
    });
    div.className = 'resultado ' + (r.sucesso ? 'ok' : 'erro');
    div.textContent = r.mensagem;
  } catch (err) {
    div.className = 'resultado erro';
    div.textContent = err.message;
  }
}

async function carregarLog() {
  try {
    const r = await fetch('/api/rpa/log');
    const txt = r.ok ? await r.text() : 'Log não disponível.';
    document.getElementById('rpa-log').textContent = txt || '(log vazio)';
  } catch {
    document.getElementById('rpa-log').textContent = 'Não foi possível carregar o log.';
  }
}

// ── Chatbot ────────────────────────────────────────────────────────────────
let chatOpen = false;

function toggleChat() {
  chatOpen = !chatOpen;
  document.getElementById('chatbot-box').classList.toggle('hidden', !chatOpen);
  if (chatOpen && document.getElementById('chatbot-messages').children.length === 0) {
    addBotMsg('👋 Olá! Sou o assistente da Biblioteca Digital.\nDigite **ajuda** para ver o que posso fazer por você!');
  }
}

function addBotMsg(txt) {
  const div = document.createElement('div');
  div.className = 'msg msg-bot';
  div.innerHTML = txt.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
  document.getElementById('chatbot-messages').appendChild(div);
  div.scrollIntoView({ behavior: 'smooth' });
}

function addUserMsg(txt) {
  const div = document.createElement('div');
  div.className = 'msg msg-user';
  div.textContent = txt;
  document.getElementById('chatbot-messages').appendChild(div);
  div.scrollIntoView({ behavior: 'smooth' });
}

async function enviarMensagem() {
  const input = document.getElementById('chatbot-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  addUserMsg(msg);
  try {
    const r = await api('/api/chatbot', { method: 'POST', body: JSON.stringify({ mensagem: msg }) });
    addBotMsg(r.resposta);
  } catch {
    addBotMsg('⚠️ Serviço temporariamente indisponível.');
  }
}

// ── Utilitários ────────────────────────────────────────────────────────────
function esc(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  carregarDashboard();
  // Carrega categorias em background para os selects
  api('/api/categorias').then(c => { _categorias = c; }).catch(() => {});
});
