# -*- coding: utf-8 -*-
"""Testa todos os endpoints da API + chatbot + e-mail RPA."""
import sys, json, urllib.request as ur, time, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:5000'
PASS = 0; FAIL = 0

def ok(msg):  global PASS;  PASS += 1;  print(f'  [OK]  {msg}')
def err(msg): global FAIL;  FAIL += 1;  print(f'  [FALHA] {msg}')

def get(path):
    with ur.urlopen(f'{BASE}{path}') as r:
        return json.loads(r.read()), r.status

def post(path, data):
    req = ur.Request(f'{BASE}{path}', json.dumps(data).encode(),
                     {'Content-Type':'application/json'})
    with ur.urlopen(req) as r:
        return json.loads(r.read()), r.status

def put(path, data=None):
    req = ur.Request(f'{BASE}{path}', json.dumps(data or {}).encode(),
                     {'Content-Type':'application/json'}, method='PUT')
    with ur.urlopen(req) as r:
        return json.loads(r.read()), r.status

def delete(path):
    req = ur.Request(f'{BASE}{path}', method='DELETE')
    with ur.urlopen(req) as r:
        return json.loads(r.read()), r.status

print('\n' + '='*55)
print('  TESTE COMPLETO — Biblioteca Digital ADS')
print('='*55 + '\n')

# ── 1. Dashboard ──────────────────────────────────────────────
print('[1] Dashboard')
d, s = get('/api/dashboard')
if s == 200 and 'total_livros' in d:
    ok(f'GET /api/dashboard → 7 livros, {d["total_usuarios"]} usuarios')
else:
    err(f'Falhou: {d}')

# ── 2. Categorias CRUD ────────────────────────────────────────
print('\n[2] Categorias')
cats, s = get('/api/categorias')
ok(f'GET /api/categorias → {len(cats)} categorias') if s==200 else err(str(cats))

nova, s = post('/api/categorias', {'nome':'Autoajuda','descricao':'Desenvolvimento pessoal'})
ok(f'POST /api/categorias → id={nova["id"]} nome={nova["nome"]}') if s==201 else err(str(nova))
cat_id = nova['id']

upd, s = put(f'/api/categorias/{cat_id}', {'descricao':'Crescimento pessoal e profissional'})
ok('PUT /api/categorias/<id>') if s==200 else err(str(upd))

d, s = delete(f'/api/categorias/{cat_id}')
ok('DELETE /api/categorias/<id>') if s==200 else err(str(d))

# ── 3. Livros CRUD ────────────────────────────────────────────
print('\n[3] Livros')
livros, s = get('/api/livros')
ok(f'GET /api/livros → {len(livros)} livros') if s==200 else err(str(livros))

# Filtro por título
fl, s = get('/api/livros?titulo=duna')
ok(f'GET /api/livros?titulo=duna → {len(fl)} resultado(s)') if s==200 and len(fl)>=1 else err('Filtro falhou')

# Filtro por autor
fl, s = get('/api/livros?autor=asimov')
ok(f'GET /api/livros?autor=asimov → {len(fl)} resultado(s)') if s==200 and len(fl)>=1 else err('Filtro autor falhou')

novo_livro, s = post('/api/livros', {
    'titulo':'O Senhor dos Anéis', 'autor':'J.R.R. Tolkien',
    'categoria_id':1, 'quantidade':2, 'ano_publicacao':1954
})
ok(f'POST /api/livros → id={novo_livro["id"]}') if s==201 else err(str(novo_livro))
livro_id = novo_livro['id']

upd, s = put(f'/api/livros/{livro_id}', {'quantidade':3})
ok('PUT /api/livros/<id>') if s==200 else err(str(upd))

d, s = delete(f'/api/livros/{livro_id}')
ok('DELETE /api/livros/<id>') if s==200 else err(str(d))

# ── 4. Usuários CRUD ──────────────────────────────────────────
print('\n[4] Usuários')
users, s = get('/api/usuarios')
ok(f'GET /api/usuarios → {len(users)} usuários') if s==200 else err(str(users))

novo_user, s = post('/api/usuarios', {
    'nome':'Rafael Teste', 'email':'rafael.teste@ads.edu.br', 'telefone':'5511988880001'
})
ok(f'POST /api/usuarios → id={novo_user["id"]}') if s==201 else err(str(novo_user))
user_id = novo_user['id']

upd, s = put(f'/api/usuarios/{user_id}', {'telefone':'5511977770001'})
ok('PUT /api/usuarios/<id>') if s==200 else err(str(upd))

# ── 5. Empréstimos CRUD ───────────────────────────────────────
print('\n[5] Empréstimos')
emp, s = post('/api/emprestimos', {
    'livro_id':1, 'usuario_id':user_id, 'data_devolucao_prevista':'2026-06-22'
})
ok(f'POST /api/emprestimos → id={emp["id"]} livro={emp["livro"]} status={emp["status"]}') if s==201 else err(str(emp))
emp_id = emp['id']

emps, s = get('/api/emprestimos?status=ativo')
ok(f'GET /api/emprestimos?status=ativo → {len(emps)} ativo(s)') if s==200 else err(str(emps))

dev, s = put(f'/api/emprestimos/{emp_id}/devolver')
ok(f'PUT /emprestimos/{emp_id}/devolver → status={dev["status"]} data={dev["data_devolucao_real"]}') if s==200 else err(str(dev))

# ── 6. Chatbot ────────────────────────────────────────────────
print('\n[6] Chatbot')
for msg, esperado_min in [
    ('oi', 'bem-vindo'),
    ('buscar livro Duna', 'Duna'),
    ('quais categorias?', 'Ficção'),
    ('como empresto um livro?', 'mpréstimo'),
    ('qual o prazo de devolucao?', 'prazo'),
    ('qual o PIB do Brasil?', 'entendi'),
]:
    try:
        r, _ = post('/api/chatbot', {'mensagem': msg})
        resp = r['resposta']
        if esperado_min.lower() in resp.lower():
            ok(f'chatbot("{msg[:30]}") → contém "{esperado_min}"')
        else:
            err(f'chatbot("{msg[:30]}") → esperava "{esperado_min}" mas got: {resp[:60]}')
    except Exception as e:
        err(f'chatbot("{msg[:30]}") → exceção: {e}')

# ── 7. RPA E-mail ─────────────────────────────────────────────
print('\n[7] RPA — E-mail')
try:
    r, s = post('/api/rpa/notificar-email', {
        'emprestimo_id': emp_id,
        'destinatario': 'maria.delfino115@gmail.com'
    })
    if r.get('sucesso'):
        ok(f'E-mail enviado: {r["mensagem"]}')
    else:
        err(f'E-mail falhou: {r["mensagem"]}')
except Exception as e:
    err(f'Exceção RPA email: {e}')

# ── 8. Cleanup ────────────────────────────────────────────────
delete(f'/api/usuarios/{user_id}')

# ── Resultado final ───────────────────────────────────────────
print('\n' + '='*55)
print(f'  RESULTADO: {PASS} passou | {FAIL} falhou')
print('='*55)
