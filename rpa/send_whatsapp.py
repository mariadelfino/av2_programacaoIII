"""
RPA - Envio de WhatsApp via pywhatkit
Envia notificações de empréstimo e devolução via WhatsApp Web.
"""

import logging
import time
from datetime import datetime

logging.basicConfig(
    filename='rpa/rpa_log.txt',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)


def _formatar_mensagem_emprestimo(dados: dict) -> str:
    return (
        f"📚 *Biblioteca Digital ADS*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Empréstimo Confirmado!*\n\n"
        f"👤 Usuário: {dados.get('usuario', '-')}\n"
        f"📖 Livro: {dados.get('livro', '-')}\n"
        f"✍️ Autor: {dados.get('autor', '-')}\n"
        f"📅 Empréstimo: {dados.get('data_emprestimo', '-')}\n"
        f"🔴 Devolução até: *{dados.get('data_devolucao_prevista', '-')}*\n\n"
        f"Boa leitura! 😊\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Mensagem automática — não responda_"
    )


def _formatar_mensagem_atraso(dados: dict) -> str:
    return (
        f"⚠️ *Biblioteca Digital ADS*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*AVISO DE ATRASO NA DEVOLUÇÃO*\n\n"
        f"Olá, {dados.get('usuario', 'usuário')}!\n"
        f"O livro *\"{dados.get('livro')}\"* deveria ter sido\n"
        f"devolvido em {dados.get('data_devolucao_prevista')}.\n\n"
        f"Por favor, realize a devolução o quanto antes.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Mensagem automática — não responda_"
    )


def enviar_whatsapp_emprestimo(dados: dict, telefone: str = None) -> dict:
    """
    Envia mensagem WhatsApp confirmando empréstimo.
    Telefone no formato internacional sem + (ex: 5511999990001).
    """
    numero = telefone or dados.get('telefone_usuario', '')
    if not numero:
        msg = 'Número de telefone não informado.'
        logging.error(f'FALHA | WhatsApp | {msg}')
        return {'sucesso': False, 'mensagem': msg}

    # Limpa formatação
    numero = ''.join(filter(str.isdigit, str(numero)))

    mensagem = _formatar_mensagem_emprestimo(dados)

    try:
        import pywhatkit as kit

        agora = datetime.now()
        hora = agora.hour
        minuto = agora.minute + 2  # envia em 2 minutos
        if minuto >= 60:
            hora += 1
            minuto -= 60

        kit.sendwhatmsg(f'+{numero}', mensagem, hora, minuto,
                        wait_time=20, tab_close=True, close_time=5)

        log_msg = f'SUCESSO | WhatsApp enviado para +{numero} | Livro: {dados.get("livro")}'
        logging.info(log_msg)
        return {
            'sucesso': True,
            'mensagem': f'WhatsApp agendado para +{numero} às {hora:02d}:{minuto:02d}',
            'log': log_msg
        }

    except ImportError:
        log_msg = 'FALHA | pywhatkit não instalado. Execute: pip install pywhatkit'
        logging.error(log_msg)
        return {'sucesso': False, 'mensagem': log_msg}
    except Exception as e:
        log_msg = f'FALHA | WhatsApp | {type(e).__name__}: {e}'
        logging.error(log_msg)
        return {'sucesso': False, 'mensagem': str(e), 'log': log_msg}


def enviar_whatsapp_atraso(dados: dict, telefone: str) -> dict:
    """Envia aviso de atraso via WhatsApp."""
    numero = ''.join(filter(str.isdigit, str(telefone)))
    mensagem = _formatar_mensagem_atraso(dados)

    try:
        import pywhatkit as kit
        agora = datetime.now()
        hora = agora.hour
        minuto = agora.minute + 2
        if minuto >= 60:
            hora += 1
            minuto -= 60

        kit.sendwhatmsg(f'+{numero}', mensagem, hora, minuto,
                        wait_time=20, tab_close=True, close_time=5)

        logging.info(f'SUCESSO | WhatsApp atraso enviado para +{numero}')
        return {'sucesso': True, 'mensagem': f'Aviso enviado para +{numero}'}
    except Exception as e:
        logging.error(f'FALHA | WhatsApp atraso | {e}')
        return {'sucesso': False, 'mensagem': str(e)}
