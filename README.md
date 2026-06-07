# 📚 Biblioteca Digital ADS

Sistema de gestão de acervo bibliográfico desenvolvido para a **AV2 — Linguagem de Programação III**.

## Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ · Flask 3.0 · Flask-SQLAlchemy |
| Banco de dados | SQLite (via SQLAlchemy ORM) |
| Frontend | HTML5 · CSS3 · JavaScript (Vanilla) |
| RPA — E-mail | smtplib · Gmail SMTP |
| RPA — WhatsApp | pywhatkit · WhatsApp Web |
| Agendamento | schedule |
| Relatórios | openpyxl |
| Notificação Desktop | plyer |
| Chatbot | Lógica de intenção (Python puro) |

## Entidades do Banco de Dados

- **Categoria** — gênero literário (nome, descrição)
- **Livro** — título, autor, ISBN, ano, quantidade disponível, FK → Categoria
- **Usuário** — nome, e-mail, telefone
- **Empréstimo** — FK → Livro + Usuário, datas, status (ativo/devolvido/atrasado)

## Passo a Passo para Rodar o Projeto

### 1. Pré-requisitos
- Python 3.11 ou superior instalado
- Git (opcional)

### 2. Instalar dependências

```bash
pip install flask flask-sqlalchemy flask-cors python-dotenv pywhatkit schedule plyer openpyxl requests
```

### 3. Configurar credenciais de e-mail (opcional para testar RPA)

```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite .env com seu Gmail e senha de app do Google
# Acesse: https://myaccount.google.com/apppasswords
```

### 4. Iniciar o servidor Flask

```bash
python app.py
```

O sistema abrirá em: **http://localhost:5000**

### 5. (Opcional) Iniciar o agendador RPA

```bash
python rpa/automation.py
```

O agendador verifica atrasos às 08h e gera relatório Excel toda sexta às 17h.

## Endpoints da API REST

### Categorias
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/categorias` | Lista todas |
| POST | `/api/categorias` | Cria nova |
| PUT | `/api/categorias/<id>` | Atualiza |
| DELETE | `/api/categorias/<id>` | Remove |

### Livros
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/livros` | Lista (filtros: titulo, autor, categoria_id, disponivel) |
| GET | `/api/livros/<id>` | Detalhe |
| POST | `/api/livros` | Cria |
| PUT | `/api/livros/<id>` | Atualiza |
| DELETE | `/api/livros/<id>` | Remove |

### Usuários
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/usuarios` | Lista (filtro: nome) |
| GET | `/api/usuarios/<id>` | Detalhe |
| POST | `/api/usuarios` | Cria |
| PUT | `/api/usuarios/<id>` | Atualiza |
| DELETE | `/api/usuarios/<id>` | Remove |

### Empréstimos
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/emprestimos` | Lista (filtros: status, usuario_id) |
| POST | `/api/emprestimos` | Registra empréstimo |
| PUT | `/api/emprestimos/<id>/devolver` | Registra devolução |
| DELETE | `/api/emprestimos/<id>` | Remove |

### RPA e Chatbot
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/chatbot` | Envia mensagem ao chatbot |
| GET | `/api/dashboard` | Estatísticas gerais |
| POST | `/api/rpa/notificar-email` | Envia e-mail de empréstimo |
| POST | `/api/rpa/notificar-whatsapp` | Envia WhatsApp de empréstimo |
| GET | `/api/rpa/log` | Consulta log de automações |

## Funcionalidades

- ✅ CRUD completo para Categorias, Livros, Usuários e Empréstimos
- ✅ Filtros por título, autor, categoria e disponibilidade
- ✅ Controle automático de disponibilidade ao emprestar/devolver
- ✅ Chatbot com reconhecimento de intenção
- ✅ Envio de e-mail HTML personalizado via Gmail SMTP
- ✅ Envio de WhatsApp via pywhatkit (WhatsApp Web)
- ✅ Agendamento de verificações de atraso com `schedule`
- ✅ Exportação de relatório Excel com `openpyxl`
- ✅ Notificações desktop com `plyer`
- ✅ Log de todas as automações em arquivo `rpa/rpa_log.txt`

## Grupo
- Rafael (ADS — Linguagem de Programação III — AV2)
