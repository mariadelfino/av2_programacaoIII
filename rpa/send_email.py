"""
RPA - Envio de E-mail via Gmail SMTP
Notifica usuários sobre empréstimos e devoluções.
"""

import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logging.basicConfig(
    filename='rpa/rpa_log.txt',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# Configurações — altere para credenciais reais ou use .env
EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE', 'biblioteca.ads2025@gmail.com')
EMAIL_SENHA = os.getenv('EMAIL_SENHA', 'sua_senha_app_aqui')
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587


def _construir_html_emprestimo(dados: dict) -> str:
    return f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
      <div style="max-width:600px;margin:auto;border:1px solid #ddd;border-radius:8px;overflow:hidden;">
        <div style="background:#1a73e8;padding:20px;text-align:center;">
          <h1 style="color:white;margin:0;">📚 Biblioteca Digital ADS</h1>
        </div>
        <div style="padding:24px;">
          <h2>Confirmação de Empréstimo</h2>
          <p>Olá, <strong>{dados.get('usuario', 'Usuário')}</strong>!</p>
          <p>Seu empréstimo foi registrado com sucesso:</p>
          <table style="width:100%;border-collapse:collapse;margin:16px 0;">
            <tr style="background:#f5f5f5;">
              <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">Livro</td>
              <td style="padding:10px;border:1px solid #ddd;">{dados.get('livro', '-')}</td>
            </tr>
            <tr>
              <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">Autor</td>
              <td style="padding:10px;border:1px solid #ddd;">{dados.get('autor', '-')}</td>
            </tr>
            <tr style="background:#f5f5f5;">
              <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">Data do Empréstimo</td>
              <td style="padding:10px;border:1px solid #ddd;">{dados.get('data_emprestimo', '-')}</td>
            </tr>
            <tr>
              <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">Devolução Prevista</td>
              <td style="padding:10px;border:1px solid #ddd;color:#e53935;font-weight:bold;">{dados.get('data_devolucao_prevista', '-')}</td>
            </tr>
          </table>
          <p style="background:#fff3e0;padding:12px;border-radius:4px;border-left:4px solid #ff9800;">
            ⚠️ Lembre-se: devoluções em atraso bloqueiam novos empréstimos.
          </p>
          <p style="color:#666;font-size:13px;">
            Em caso de dúvidas, entre em contato: biblioteca@sistema.edu.br
          </p>
        </div>
        <div style="background:#f5f5f5;padding:12px;text-align:center;font-size:12px;color:#666;">
          Biblioteca Digital ADS — Sistema Automático de Notificações
        </div>
      </div>
    </body></html>
    """


def enviar_email_emprestimo(dados: dict, destinatario: str = None) -> dict:
    """Envia e-mail de confirmação de empréstimo."""
    para = destinatario or dados.get('email_usuario', '')
    if not para:
        msg = 'E-mail do destinatário não informado.'
        logging.error(f'FALHA | {msg}')
        return {'sucesso': False, 'mensagem': msg}

    assunto = f"📚 Empréstimo confirmado: {dados.get('livro', 'Livro')}"
    corpo_html = _construir_html_emprestimo(dados)

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = para
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo_html, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
            servidor.sendmail(EMAIL_REMETENTE, para, msg.as_string())

        log_msg = f'SUCESSO | E-mail enviado para {para} | Livro: {dados.get("livro")}'
        logging.info(log_msg)
        return {'sucesso': True, 'mensagem': f'E-mail enviado com sucesso para {para}', 'log': log_msg}

    except smtplib.SMTPAuthenticationError:
        log_msg = 'FALHA | Erro de autenticação SMTP — verifique EMAIL_REMETENTE e EMAIL_SENHA'
        logging.error(log_msg)
        return {'sucesso': False, 'mensagem': 'Erro de autenticação. Configure as credenciais no .env', 'log': log_msg}
    except Exception as e:
        log_msg = f'FALHA | {type(e).__name__}: {e}'
        logging.error(log_msg)
        return {'sucesso': False, 'mensagem': str(e), 'log': log_msg}


def enviar_email_atraso(dados: dict) -> dict:
    """Envia e-mail de aviso de atraso."""
    para = dados.get('email_usuario', '')
    if not para:
        return {'sucesso': False, 'mensagem': 'E-mail não informado'}

    assunto = f"⚠️ ATRASO na devolução: {dados.get('livro', 'Livro')}"
    corpo = f"""
    <html><body style="font-family:Arial;color:#333;">
      <div style="max-width:600px;margin:auto;border:2px solid #e53935;border-radius:8px;overflow:hidden;">
        <div style="background:#e53935;padding:20px;text-align:center;">
          <h1 style="color:white;margin:0;">⚠️ Aviso de Atraso</h1>
        </div>
        <div style="padding:24px;">
          <p>Olá, <strong>{dados.get('usuario')}</strong>!</p>
          <p>O livro <strong>"{dados.get('livro')}"</strong> deveria ter sido devolvido em
          <strong>{dados.get('data_devolucao_prevista')}</strong>.</p>
          <p>Por favor, realize a devolução o quanto antes para evitar bloqueio do seu cadastro.</p>
        </div>
      </div>
    </body></html>
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = para
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
            servidor.sendmail(EMAIL_REMETENTE, para, msg.as_string())

        logging.info(f'SUCESSO | Aviso de atraso enviado para {para}')
        return {'sucesso': True, 'mensagem': f'Aviso enviado para {para}'}
    except Exception as e:
        logging.error(f'FALHA | Aviso atraso | {e}')
        return {'sucesso': False, 'mensagem': str(e)}
