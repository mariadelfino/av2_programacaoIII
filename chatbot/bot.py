"""
Chatbot da Biblioteca Digital
Reconhecimento de intenção via palavras-chave + consultas à base de dados.
"""

import re
from datetime import date


SAUDACOES = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'hello']
DESPEDIDAS = ['tchau', 'até logo', 'adeus', 'até mais', 'bye']
AJUDA = ['ajuda', 'help', 'o que você faz', 'o que voce faz', 'menu', 'opções', 'opcoes']

# Ordem importa: mais específicas primeiro
INTENCOES = [
    ('emprestimo_info', ['emprestar', 'empresto', 'pegar livro', 'retirar', 'empréstimo', 'emprestimo']),
    ('devolucao_info',  ['devolução', 'devolucao', 'devolver', 'prazo', 'atraso']),
    ('listar_categorias', ['categoria', 'categorias', 'gênero', 'genero', 'tipos de livro']),
    ('horario_info',    ['horário', 'horario', 'funciona', 'aberto', 'fechado', 'quando abre']),
    ('contato_info',    ['contato', 'telefone', 'falar com']),
    ('sobre',           ['o que é', 'o que e', 'sobre o sistema']),
    ('buscar_livro',    ['livro', 'livros', 'buscar', 'procurar', 'disponível', 'disponivel', 'acervo']),
]

RESPOSTAS_FIXAS = {
    'emprestimo_info': (
        "📚 Para realizar um empréstimo:\n"
        "1. Acesse a aba **Empréstimos** no menu\n"
        "2. Selecione o livro desejado\n"
        "3. Informe seu cadastro de usuário\n"
        "4. Defina a data de devolução (máx. 15 dias)\n\n"
        "O livro deve estar disponível no acervo."
    ),
    'devolucao_info': (
        "📅 Informações sobre devolução:\n"
        "• O prazo padrão é de **15 dias** a partir do empréstimo\n"
        "• Devoluções em atraso geram notificação automática por e-mail\n"
        "• Para devolver, acesse **Empréstimos → Devolver**\n"
        "• Livros podem ser renovados se não houver reserva"
    ),
    'horario_info': (
        "🕐 Horário de funcionamento da Biblioteca Digital:\n"
        "• Sistema online: 24 horas por dia, 7 dias por semana\n"
        "• Suporte presencial: Seg–Sex, das 8h às 18h\n"
        "• Sábado: 8h às 12h"
    ),
    'contato_info': (
        "📞 Contato da Biblioteca:\n"
        "• E-mail: biblioteca@sistema.edu.br\n"
        "• Telefone: (11) 3000-0000\n"
        "• WhatsApp: (11) 99999-0000\n"
        "• Balcão: Bloco A, Sala 101"
    ),
    'sobre': (
        "🏛️ **Biblioteca Digital ADS**\n"
        "Sistema de gestão de acervo desenvolvido para a disciplina Linguagem de Programação III.\n\n"
        "Funcionalidades:\n"
        "• Cadastro e busca de livros por título, autor e categoria\n"
        "• Controle de empréstimos e devoluções\n"
        "• Notificações automáticas por WhatsApp e e-mail\n"
        "• Chatbot de atendimento (você está usando agora!)"
    ),
}

MENU_AJUDA = (
    "🤖 Olá! Sou o assistente da Biblioteca Digital. Posso te ajudar com:\n\n"
    "📖 **Livros** — buscar, verificar disponibilidade\n"
    "🗂️ **Categorias** — ver gêneros disponíveis\n"
    "📋 **Empréstimos** — como emprestar um livro\n"
    "🔄 **Devoluções** — prazos e como devolver\n"
    "🕐 **Horário** — quando o sistema funciona\n"
    "📞 **Contato** — como falar conosco\n\n"
    "Digite sua dúvida ou uma das palavras acima!"
)


def normalizar(texto: str) -> str:
    return texto.lower().strip()


def detectar_intencao(texto: str) -> str | None:
    t = normalizar(texto)
    for intencao, palavras in INTENCOES:
        for p in palavras:
            if p in t:
                return intencao
    return None


def _get_db():
    """Retorna conexão direta ao SQLite sem depender do contexto Flask."""
    import sqlite3, os
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base, 'instance', 'biblioteca.db')
    return sqlite3.connect(db_path)


def buscar_livros_db(titulo: str) -> str:
    try:
        conn = _get_db()
        cur = conn.cursor()
        cur.execute(
            '''SELECT l.titulo, l.autor, l.ano_publicacao, l.disponivel, l.quantidade
               FROM livros l WHERE l.titulo LIKE ? OR l.autor LIKE ? LIMIT 5''',
            (f'%{titulo}%', f'%{titulo}%')
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return f'Não encontrei livros com "{titulo}" no acervo. Tente outro título ou autor.'
        resposta = f'📚 Encontrei {len(rows)} livro(s):\n'
        for titulo_l, autor, ano, disp, qtd in rows:
            status = '✅ Disponível' if disp > 0 else '❌ Indisponível'
            resposta += f'\n• **{titulo_l}** — {autor} ({ano or "S/D"})\n  {status} | {disp}/{qtd} cópias'
        return resposta
    except Exception as e:
        return f'Não consegui consultar o acervo agora. Tente pela aba Livros no menu. ({e})'


def listar_categorias_db() -> str:
    try:
        conn = _get_db()
        cur = conn.cursor()
        cur.execute(
            '''SELECT c.nome, COUNT(l.id) as total
               FROM categorias c LEFT JOIN livros l ON l.categoria_id = c.id
               GROUP BY c.id''')
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return 'Nenhuma categoria cadastrada ainda.'
        resposta = '🗂️ Categorias disponíveis no acervo:\n'
        for nome, total in rows:
            resposta += f'\n• **{nome}** — {total} livro(s)'
        return resposta
    except Exception as e:
        return f'Não consegui listar as categorias agora. ({e})'


def processar_mensagem(mensagem: str) -> str:
    t = normalizar(mensagem)

    # Saudação
    if any(s in t for s in SAUDACOES):
        return (
            "👋 Olá! Seja bem-vindo(a) à Biblioteca Digital!\n"
            "Como posso te ajudar hoje? Digite **ajuda** para ver as opções disponíveis."
        )

    # Despedida
    if any(d in t for d in DESPEDIDAS):
        return "👋 Até logo! Volte sempre à Biblioteca Digital. 📚"

    # Ajuda / Menu
    if any(a in t for a in AJUDA):
        return MENU_AJUDA

    # Intenções fixas
    intencao = detectar_intencao(t)

    if intencao == 'buscar_livro':
        # Remove palavras-chave de comando para extrair só o título
        titulo_raw = re.sub(r'\b(buscar|procurar|tem o?|livro|livros|disponivel|disponível|acervo)\b', '', t).strip()
        titulo_raw = re.sub(r'\s+', ' ', titulo_raw).strip()
        if titulo_raw:
            return buscar_livros_db(titulo_raw)
        return (
            "🔍 Qual livro você está procurando?\n"
            "Me diga o título ou autor. Ex: *buscar livro Duna*"
        )

    if intencao == 'listar_categorias':
        return listar_categorias_db()

    if intencao in RESPOSTAS_FIXAS:
        return RESPOSTAS_FIXAS[intencao]

    # Fallback com IA simples baseada em regras
    if any(w in t for w in ['obrigado', 'obrigada', 'valeu', 'grato']):
        return "😊 De nada! Estou aqui para ajudar. Algo mais?"

    if any(w in t for w in ['problema', 'erro', 'bug', 'não funciona', 'nao funciona']):
        return (
            "⚠️ Encontrou um problema? Por favor:\n"
            "1. Descreva o que aconteceu\n"
            "2. Entre em contato pelo e-mail: biblioteca@sistema.edu.br\n"
            "3. Ou pelo balcão de atendimento (Bloco A, Sala 101)"
        )

    return (
        "🤔 Não entendi sua pergunta. Posso te ajudar com:\n"
        "• **livros** — buscar no acervo\n"
        "• **empréstimo** — como emprestar\n"
        "• **devolução** — prazos e regras\n"
        "• **categorias** — gêneros disponíveis\n\n"
        "Ou digite **ajuda** para ver todas as opções."
    )
