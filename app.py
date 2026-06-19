from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biblioteca.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'biblioteca-av2-2025'
CORS(app)

db = SQLAlchemy(app)

# ─── MODELS ───────────────────────────────────────────────────────────────────

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    livros = db.relationship('Livro', backref='categoria', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'nome': self.nome, 'descricao': self.descricao,
                'total_livros': len(self.livros)}


class Livro(db.Model):
    __tablename__ = 'livros'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    ano_publicacao = db.Column(db.Integer)
    quantidade = db.Column(db.Integer, default=1)
    disponivel = db.Column(db.Integer, default=1)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    emprestimos = db.relationship('Emprestimo', backref='livro', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'titulo': self.titulo, 'autor': self.autor,
            'isbn': self.isbn, 'ano_publicacao': self.ano_publicacao,
            'quantidade': self.quantidade, 'disponivel': self.disponivel,
            'categoria_id': self.categoria_id,
            'categoria': self.categoria.nome if self.categoria else None
        }


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    telefone = db.Column(db.String(20))
    data_cadastro = db.Column(db.Date, default=date.today)
    emprestimos = db.relationship('Emprestimo', backref='usuario', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'nome': self.nome, 'email': self.email,
            'telefone': self.telefone,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'total_emprestimos': len(self.emprestimos)
        }


class Emprestimo(db.Model):
    __tablename__ = 'emprestimos'
    id = db.Column(db.Integer, primary_key=True)
    livro_id = db.Column(db.Integer, db.ForeignKey('livros.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_emprestimo = db.Column(db.Date, default=date.today)
    data_devolucao_prevista = db.Column(db.Date, nullable=False)
    data_devolucao_real = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='ativo')  # ativo, devolvido, atrasado

    def to_dict(self):
        return {
            'id': self.id,
            'livro_id': self.livro_id,
            'livro': self.livro.titulo if self.livro else None,
            'autor': self.livro.autor if self.livro else None,
            'usuario_id': self.usuario_id,
            'usuario': self.usuario.nome if self.usuario else None,
            'email_usuario': self.usuario.email if self.usuario else None,
            'data_emprestimo': self.data_emprestimo.isoformat() if self.data_emprestimo else None,
            'data_devolucao_prevista': self.data_devolucao_prevista.isoformat() if self.data_devolucao_prevista else None,
            'data_devolucao_real': self.data_devolucao_real.isoformat() if self.data_devolucao_real else None,
            'status': self.status
        }


# ─── FRONTEND ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ─── API: CATEGORIAS ──────────────────────────────────────────────────────────

@app.route('/api/categorias', methods=['GET'])
def listar_categorias():
    categorias = Categoria.query.all()
    return jsonify([c.to_dict() for c in categorias]), 200


@app.route('/api/categorias', methods=['POST'])
def criar_categoria():
    data = request.get_json()
    if not data or not data.get('nome'):
        return jsonify({'erro': 'Campo nome é obrigatório'}), 400
    if Categoria.query.filter_by(nome=data['nome']).first():
        return jsonify({'erro': 'Categoria já existe'}), 400
    cat = Categoria(nome=data['nome'], descricao=data.get('descricao', ''))
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@app.route('/api/categorias/<int:id>', methods=['PUT'])
def atualizar_categoria(id):
    cat = Categoria.query.get_or_404(id)
    data = request.get_json()
    if data.get('nome'):
        cat.nome = data['nome']
    if 'descricao' in data:
        cat.descricao = data['descricao']
    db.session.commit()
    return jsonify(cat.to_dict()), 200


@app.route('/api/categorias/<int:id>', methods=['DELETE'])
def deletar_categoria(id):
    cat = Categoria.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'mensagem': 'Categoria removida'}), 200


# ─── API: LIVROS ──────────────────────────────────────────────────────────────

@app.route('/api/livros', methods=['GET'])
def listar_livros():
    titulo = request.args.get('titulo', '')
    autor = request.args.get('autor', '')
    categoria_id = request.args.get('categoria_id')
    disponivel = request.args.get('disponivel')

    query = Livro.query
    if titulo:
        query = query.filter(Livro.titulo.ilike(f'%{titulo}%'))
    if autor:
        query = query.filter(Livro.autor.ilike(f'%{autor}%'))
    if categoria_id:
        query = query.filter_by(categoria_id=int(categoria_id))
    if disponivel is not None:
        query = query.filter(Livro.disponivel > 0)

    livros = query.all()
    return jsonify([l.to_dict() for l in livros]), 200


@app.route('/api/livros/<int:id>', methods=['GET'])
def obter_livro(id):
    livro = Livro.query.get_or_404(id)
    return jsonify(livro.to_dict()), 200


@app.route('/api/livros', methods=['POST'])
def criar_livro():
    data = request.get_json()
    campos = ['titulo', 'autor', 'categoria_id']
    for c in campos:
        if not data.get(c):
            return jsonify({'erro': f'Campo {c} é obrigatório'}), 400
    if not Categoria.query.get(data['categoria_id']):
        return jsonify({'erro': 'Categoria não encontrada'}), 404
    livro = Livro(
        titulo=data['titulo'], autor=data['autor'],
        isbn=data.get('isbn'), ano_publicacao=data.get('ano_publicacao'),
        quantidade=data.get('quantidade', 1),
        disponivel=data.get('quantidade', 1),
        categoria_id=data['categoria_id']
    )
    db.session.add(livro)
    db.session.commit()
    return jsonify(livro.to_dict()), 201


@app.route('/api/livros/<int:id>', methods=['PUT'])
def atualizar_livro(id):
    livro = Livro.query.get_or_404(id)
    data = request.get_json()
    for campo in ['titulo', 'autor', 'isbn', 'ano_publicacao', 'quantidade', 'disponivel', 'categoria_id']:
        if campo in data:
            setattr(livro, campo, data[campo])
    db.session.commit()
    return jsonify(livro.to_dict()), 200


@app.route('/api/livros/<int:id>', methods=['DELETE'])
def deletar_livro(id):
    livro = Livro.query.get_or_404(id)
    db.session.delete(livro)
    db.session.commit()
    return jsonify({'mensagem': 'Livro removido'}), 200


# ─── API: USUARIOS ────────────────────────────────────────────────────────────

@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    nome = request.args.get('nome', '')
    query = Usuario.query
    if nome:
        query = query.filter(Usuario.nome.ilike(f'%{nome}%'))
    return jsonify([u.to_dict() for u in query.all()]), 200


@app.route('/api/usuarios/<int:id>', methods=['GET'])
def obter_usuario(id):
    return jsonify(Usuario.query.get_or_404(id).to_dict()), 200


@app.route('/api/usuarios', methods=['POST'])
def criar_usuario():
    data = request.get_json()
    if not data.get('nome') or not data.get('email'):
        return jsonify({'erro': 'Nome e email são obrigatórios'}), 400
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({'erro': 'E-mail já cadastrado'}), 400
    u = Usuario(nome=data['nome'], email=data['email'], telefone=data.get('telefone'))
    db.session.add(u)
    db.session.commit()
    return jsonify(u.to_dict()), 201


@app.route('/api/usuarios/<int:id>', methods=['PUT'])
def atualizar_usuario(id):
    u = Usuario.query.get_or_404(id)
    data = request.get_json()
    for campo in ['nome', 'email', 'telefone']:
        if campo in data:
            setattr(u, campo, data[campo])
    db.session.commit()
    return jsonify(u.to_dict()), 200


@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    u = Usuario.query.get_or_404(id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'mensagem': 'Usuário removido'}), 200


# ─── API: EMPRESTIMOS ─────────────────────────────────────────────────────────

@app.route('/api/emprestimos', methods=['GET'])
def listar_emprestimos():
    status = request.args.get('status')
    usuario_id = request.args.get('usuario_id')
    query = Emprestimo.query
    if status:
        query = query.filter_by(status=status)
    if usuario_id:
        query = query.filter_by(usuario_id=int(usuario_id))
    return jsonify([e.to_dict() for e in query.all()]), 200


@app.route('/api/emprestimos', methods=['POST'])
def criar_emprestimo():
    data = request.get_json()
    if not data.get('livro_id') or not data.get('usuario_id') or not data.get('data_devolucao_prevista'):
        return jsonify({'erro': 'livro_id, usuario_id e data_devolucao_prevista são obrigatórios'}), 400
    livro = Livro.query.get(data['livro_id'])
    if not livro:
        return jsonify({'erro': 'Livro não encontrado'}), 404
    if livro.disponivel < 1:
        return jsonify({'erro': 'Livro indisponível para empréstimo'}), 400
    if not Usuario.query.get(data['usuario_id']):
        return jsonify({'erro': 'Usuário não encontrado'}), 404

    emp = Emprestimo(
        livro_id=data['livro_id'],
        usuario_id=data['usuario_id'],
        data_devolucao_prevista=datetime.strptime(data['data_devolucao_prevista'], '%Y-%m-%d').date()
    )
    livro.disponivel -= 1
    db.session.add(emp)
    db.session.commit()
    return jsonify(emp.to_dict()), 201


@app.route('/api/emprestimos/<int:id>/devolver', methods=['PUT'])
def devolver_livro(id):
    emp = Emprestimo.query.get_or_404(id)
    if emp.status == 'devolvido':
        return jsonify({'erro': 'Livro já devolvido'}), 400
    emp.data_devolucao_real = date.today()
    emp.status = 'devolvido'
    emp.livro.disponivel += 1
    db.session.commit()
    return jsonify(emp.to_dict()), 200


@app.route('/api/emprestimos/<int:id>', methods=['DELETE'])
def deletar_emprestimo(id):
    emp = Emprestimo.query.get_or_404(id)
    if emp.status == 'ativo':
        emp.livro.disponivel += 1
    db.session.delete(emp)
    db.session.commit()
    return jsonify({'mensagem': 'Empréstimo removido'}), 200


# ─── API: CHATBOT ─────────────────────────────────────────────────────────────

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    from chatbot.bot import processar_mensagem
    data = request.get_json()
    mensagem = data.get('mensagem', '').strip()
    if not mensagem:
        return jsonify({'resposta': 'Por favor, digite uma mensagem.'}), 400
    resposta = processar_mensagem(mensagem)
    return jsonify({'resposta': resposta}), 200


# ─── API: DASHBOARD ───────────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    total_livros = Livro.query.count()
    total_usuarios = Usuario.query.count()
    total_categorias = Categoria.query.count()
    emprestimos_ativos = Emprestimo.query.filter_by(status='ativo').count()
    emprestimos_atrasados = Emprestimo.query.filter(
        Emprestimo.status == 'ativo',
        Emprestimo.data_devolucao_prevista < date.today()
    ).count()
    emprestimos_devolvidos = Emprestimo.query.filter_by(status='devolvido').count()
    return jsonify({
        'total_livros': total_livros,
        'total_usuarios': total_usuarios,
        'total_categorias': total_categorias,
        'emprestimos_ativos': emprestimos_ativos,
        'emprestimos_atrasados': emprestimos_atrasados,
        'emprestimos_devolvidos': emprestimos_devolvidos,
    }), 200


# ─── API: RPA ─────────────────────────────────────────────────────────────────

@app.route('/api/rpa/notificar-email', methods=['POST'])
def notificar_email():
    from rpa.send_email import enviar_email_emprestimo
    data = request.get_json()
    emprestimo_id = data.get('emprestimo_id')
    emp = Emprestimo.query.get(emprestimo_id)
    if not emp:
        return jsonify({'erro': 'Empréstimo não encontrado'}), 404
    destinatario = data.get('destinatario') or None
    resultado = enviar_email_emprestimo(emp.to_dict(), destinatario)
    return jsonify(resultado), 200


@app.route('/api/rpa/log', methods=['GET'])
def rpa_log():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(base_dir, 'rpa', 'rpa_log.txt')
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
        return (conteudo or 'Log ainda vazio — nenhuma automação executada.'), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except (FileNotFoundError, OSError):
        return 'Log ainda vazio — nenhuma automação executada.', 200, {'Content-Type': 'text/plain'}


@app.route('/api/rpa/notificar-whatsapp', methods=['POST'])
def notificar_whatsapp():
    from rpa.send_whatsapp import enviar_whatsapp_emprestimo
    data = request.get_json()
    emprestimo_id = data.get('emprestimo_id')
    telefone = data.get('telefone')
    emp = Emprestimo.query.get(emprestimo_id)
    if not emp:
        return jsonify({'erro': 'Empréstimo não encontrado'}), 404
    resultado = enviar_whatsapp_emprestimo(emp.to_dict(), telefone)
    return jsonify(resultado), 200


# ─── INIT ──────────────────────────────────────────────────────────────────────

def seed_dados():
    if Categoria.query.count() == 0:
        cats = [
            Categoria(nome='Ficção Científica', descricao='Obras de ficção baseadas em ciência'),
            Categoria(nome='Romance', descricao='Histórias de amor e relacionamentos'),
            Categoria(nome='Tecnologia', descricao='Livros sobre programação e tecnologia'),
            Categoria(nome='História', descricao='Livros históricos e biografias'),
        ]
        db.session.add_all(cats)
        db.session.commit()

        livros = [
            Livro(titulo='Duna', autor='Frank Herbert', isbn='978-0441013593', ano_publicacao=1965, quantidade=3, disponivel=3, categoria_id=1),
            Livro(titulo='Fundação', autor='Isaac Asimov', isbn='978-0553803716', ano_publicacao=1951, quantidade=2, disponivel=2, categoria_id=1),
            Livro(titulo='Neuromancer', autor='William Gibson', isbn='978-0441569595', ano_publicacao=1984, quantidade=2, disponivel=2, categoria_id=1),
            Livro(titulo='Dom Casmurro', autor='Machado de Assis', isbn='978-8535910087', ano_publicacao=1899, quantidade=4, disponivel=4, categoria_id=2),
            Livro(titulo='Clean Code', autor='Robert C. Martin', isbn='978-0132350884', ano_publicacao=2008, quantidade=3, disponivel=3, categoria_id=3),
            Livro(titulo='Python Fluente', autor='Luciano Ramalho', isbn='978-8575228326', ano_publicacao=2015, quantidade=2, disponivel=2, categoria_id=3),
            Livro(titulo='Sapiens', autor='Yuval Noah Harari', isbn='978-0062316097', ano_publicacao=2011, quantidade=3, disponivel=3, categoria_id=4),
        ]
        db.session.add_all(livros)

        usuarios = [
            Usuario(nome='Ana Silva', email='ana.silva@email.com', telefone='5511999990001'),
            Usuario(nome='Bruno Costa', email='bruno.costa@email.com', telefone='5511999990002'),
            Usuario(nome='Carla Mendes', email='carla.mendes@email.com', telefone='5511999990003'),
        ]
        db.session.add_all(usuarios)
        db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_dados()
    app.run(debug=True, port=5000)
