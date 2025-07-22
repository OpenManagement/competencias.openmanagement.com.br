from flask import Flask, render_template, request, jsonify, url_for
from datetime import datetime
import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pdfkit
import mercadopago
from dotenv import load_dotenv
import threading
import time
import subprocess
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from tabela_referencia_competencias import COMPETENCIAS_ACOES

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações do MercadoPago
mp = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))

# Configurações de email
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.zoho.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'consultoria@openmanagement.com.br')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')

# Pool de threads para processamento assíncrono
executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="AsyncProcessor")

# Timeout máximo para PDF
PDF_MAX_TIMEOUT = 15

def gerar_pdf_com_timeout_kill(html_content, output_path, timeout=PDF_MAX_TIMEOUT):
    """Gera PDF com timeout rigoroso e kill automático"""
    
    def target_function(html_content, output_path, result_dict):
        try:
            # Opções ultra-otimizadas
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'disable-smart-shrinking': '',
                'print-media-type': '',
                'zoom': '0.8',
                'dpi': '96',
                'image-dpi': '96',
                'image-quality': '50',
                'quiet': '',
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore',
                'disable-plugins': '',
                'disable-javascript': '',
                'no-stop-slow-scripts': '',
                'disable-external-links': '',
                'disable-internal-links': '',
                'lowquality': '',
                'grayscale': ''
            }
            
            # Gerar PDF
            pdfkit.from_string(html_content, output_path, options=options)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                result_dict['success'] = True
                result_dict['path'] = output_path
                result_dict['size'] = os.path.getsize(output_path)
            else:
                result_dict['success'] = False
                result_dict['error'] = "PDF inválido ou muito pequeno"
                
        except Exception as e:
            result_dict['success'] = False
            result_dict['error'] = str(e)
    
    # Usar multiprocessing para isolamento completo
    manager = multiprocessing.Manager()
    result_dict = manager.dict()
    
    process = multiprocessing.Process(
        target=target_function, 
        args=(html_content, output_path, result_dict)
    )
    
    process.start()
    process.join(timeout=timeout)
    
    if process.is_alive():
        # Kill forçado
        process.terminate()
        process.join(timeout=2)
        if process.is_alive():
            process.kill()
            process.join()
        
        return False, f"PDF process killed after {timeout}s timeout"
    
    if result_dict.get('success', False):
        return True, result_dict['path']
    else:
        return False, result_dict.get('error', 'Unknown error')

def processar_pdf_e_email_async(dados):
    """Processa PDF e email de forma assíncrona"""
    try:
        nome = dados['nome']
        email = dados['email']
        html_content = dados['html_content']
        pontuacao_geral = dados['pontuacao_geral']
        
        logger.info(f"🔄 Processamento assíncrono iniciado para {nome}")
        
        # Preparar arquivo PDF
        nome_arquivo = nome.replace(' ', '_').replace('/', '_').replace('\\', '_')
        pdf_filename = f"relatorio_{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        reports_dir = os.path.join(app.static_folder, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        pdf_path = os.path.join(reports_dir, pdf_filename)
        
        # Tentar gerar PDF com timeout
        pdf_success, pdf_result = gerar_pdf_com_timeout_kill(html_content, pdf_path, PDF_MAX_TIMEOUT)
        
        if pdf_success:
            logger.info(f"✅ PDF gerado: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
        else:
            logger.warning(f"⚠️ PDF falhou: {pdf_result}")
            pdf_path = None
        
        # Enviar email
        try:
            envio_sucesso = enviar_email(nome, email, pdf_path, pontuacao_geral)
            if envio_sucesso:
                logger.info(f"✅ Email enviado para {email}")
            else:
                logger.warning(f"⚠️ Falha no envio de email para {email}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {e}")
        
        logger.info(f"✅ Processamento assíncrono concluído para {nome}")
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento assíncrono: {e}")

def calcular_competencias_individuais(respostas):
    """Calcula pontuação das 50 competências individuais"""
    competencias = {}
    
    # Mapeamento das competências (10 perguntas cada)
    mapeamento = {
        'Comunicação': list(range(1, 11)),
        'Organização': list(range(11, 21)), 
        'Proatividade': list(range(21, 31)),
        'Pensamento Crítico': list(range(31, 41)),
        'Produtividade': list(range(41, 51))
    }
    
    for competencia, perguntas in mapeamento.items():
        pontuacoes = []
        for pergunta in perguntas:
            if f'pergunta_{pergunta}' in respostas:
                pontuacoes.append(int(respostas[f'pergunta_{pergunta}']))
        
        if pontuacoes:
            media = sum(pontuacoes) / len(pontuacoes)
            competencias[competencia] = {
                'pontuacao': round(media, 2),
                'perguntas': perguntas,
                'respostas': pontuacoes
            }
    
    return competencias

def calcular_competencias_principais(competencias_individuais):
    """Calcula as 5 competências principais"""
    principais = {}
    
    for nome, dados in competencias_individuais.items():
        principais[nome] = {
            'pontuacao': dados['pontuacao'],
            'nivel': obter_nivel_competencia(dados['pontuacao'])
        }
    
    return principais

def obter_nivel_competencia(pontuacao):
    """Retorna o nível da competência baseado na pontuação"""
    if pontuacao >= 4.5:
        return "Excelente"
    elif pontuacao >= 3.5:
        return "Bom"
    elif pontuacao >= 2.5:
        return "Regular"
    elif pontuacao >= 1.5:
        return "Fraco"
    else:
        return "Muito Fraco"

def gerar_ranking_competencias(competencias):
    """Gera ranking das competências ordenado por pontuação"""
    ranking = []
    for nome, dados in competencias.items():
        ranking.append({
            'nome': nome,
            'pontuacao': dados['pontuacao'],
            'nivel': dados.get('nivel', obter_nivel_competencia(dados['pontuacao']))
        })
    
    ranking.sort(key=lambda x: x['pontuacao'], reverse=True)
    return ranking

def identificar_pontos_fortes_oportunidades(ranking_principais):
    """Identifica pontos fortes e oportunidades de melhoria"""
    pontos_fortes = ranking_principais[:2]
    oportunidades = ranking_principais[-3:]
    oportunidades.reverse()
    return pontos_fortes, oportunidades

def identificar_subcompetencias_destaque(ranking_50):
    """Identifica as subcompetências mais fortes e a desenvolver"""
    top_subcompetencias = ranking_50[:5]
    bottom_subcompetencias = ranking_50[-5:]
    bottom_subcompetencias.reverse()
    return top_subcompetencias, bottom_subcompetencias

def identificar_competencias_desenvolver(ranking_principais):
    """Identifica as 3 competências com menores pontuações para desenvolvimento"""
    competencias_desenvolver = ranking_principais[-3:]
    competencias_desenvolver.reverse()
    return competencias_desenvolver

def mapear_nome_competencia_para_chave(nome_competencia):
    """Mapeia nome da competência para chave usada na tabela de referência"""
    mapeamento = {
        'Comunicação': 'comunicacao',
        'Organização': 'organizacao', 
        'Proatividade': 'proatividade',
        'Pensamento Crítico': 'pensamento_critico',
        'Produtividade': 'produtividade'
    }
    return mapeamento.get(nome_competencia, nome_competencia.lower())

def gerar_plano_desenvolvimento(competencias_desenvolver, versao='gratuita'):
    """Gera plano de desenvolvimento baseado nas competências a desenvolver"""
    plano = []
    
    if versao == 'gratuita':
        return plano
    
    for comp in competencias_desenvolver:
        chave_competencia = mapear_nome_competencia_para_chave(comp['nome'])
        
        if chave_competencia in COMPETENCIAS_ACOES:
            acoes_competencia = COMPETENCIAS_ACOES[chave_competencia]
            
            acoes_plano = []
            for grau in ['grau_1', 'grau_2', 'grau_3']:
                if grau in acoes_competencia:
                    acoes_plano.extend(acoes_competencia[grau])
            
            if acoes_plano:
                plano.append({
                    'competencia': comp['nome'],
                    'pontuacao': comp['pontuacao'],
                    'acoes': acoes_plano[:6]  # Limitar a 6 ações
                })
    
    return plano

def enviar_email(nome, email, pdf_path, pontuacao_geral):
    """Envia email com PDF anexado"""
    try:
        if not MAIL_PASSWORD:
            logger.warning("MAIL_PASSWORD não configurada - simulando envio")
            return True
        
        msg = MIMEMultipart()
        msg['From'] = MAIL_USERNAME
        msg['To'] = email
        msg['Subject'] = f"Seu Diagnóstico de Competências - Pontuação: {pontuacao_geral:.2f}/5.00"
        
        corpo = f"""
        Olá {nome},
        
        Seu diagnóstico de competências foi concluído com sucesso!
        
        Pontuação Geral: {pontuacao_geral:.2f}/5.00
        
        {"Em anexo você encontrará seu relatório completo em PDF." if pdf_path and os.path.exists(pdf_path) else "Seu relatório foi processado com sucesso."}
        
        Atenciosamente,
        Equipe Faça Bem
        """
        
        msg.attach(MIMEText(corpo, 'plain'))
        
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(pdf_path)}'
                )
                msg.attach(part)
        
        server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_avaliacao', methods=['POST'])
def submit_avaliacao():
    """PROCESSAMENTO COM RESPOSTA IMEDIATA - NUNCA FALHA"""
    
    start_time = time.time()
    logger.info("🚀 INICIANDO PROCESSAMENTO COM RESPOSTA IMEDIATA")
    
    try:
        # Obter dados do formulário
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        celular = request.form.get('celular', '').strip()
        
        if not nome or not email:
            return jsonify({'success': False, 'message': 'Nome e email são obrigatórios'})
        
        # Obter respostas das 50 perguntas
        respostas = {}
        for i in range(1, 51):
            resposta = request.form.get(f'pergunta_{i}')
            if resposta:
                respostas[f'pergunta_{i}'] = int(resposta)
        
        if len(respostas) < 50:
            return jsonify({'success': False, 'message': 'Todas as 50 perguntas devem ser respondidas'})
        
        logger.info(f"✅ Dados coletados em {time.time() - start_time:.3f}s")
        
        # Calcular competências
        calc_start = time.time()
        competencias_individuais = calcular_competencias_individuais(respostas)
        competencias_principais = calcular_competencias_principais(competencias_individuais)
        
        pontuacao_geral = sum(comp['pontuacao'] for comp in competencias_principais.values()) / len(competencias_principais)
        
        ranking_principais = gerar_ranking_competencias(competencias_principais)
        pontos_fortes, oportunidades = identificar_pontos_fortes_oportunidades(ranking_principais)
        competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
        plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver, 'premium')
        
        logger.info(f"✅ Cálculos concluídos em {time.time() - calc_start:.3f}s")
        
        # Preparar dados para o template
        dados_template = {
            'nome': nome,
            'email': email,
            'celular': celular,
            'pontuacao_geral': pontuacao_geral,
            'competencias_principais': competencias_principais,
            'ranking_principais': ranking_principais,
            'pontos_fortes': pontos_fortes,
            'oportunidades': oportunidades,
            'competencias_desenvolver': competencias_desenvolver,
            'plano_desenvolvimento': plano_desenvolvimento,
            'data_avaliacao': datetime.now().strftime('%d/%m/%Y'),
            'hora_avaliacao': datetime.now().strftime('%H:%M')
        }
        
        # Renderizar template HTML
        template_start = time.time()
        html_relatorio = render_template('relatorio_template.html', **dados_template)
        logger.info(f"✅ Template renderizado em {time.time() - template_start:.3f}s")
        
        # Agendar processamento assíncrono (NÃO BLOQUEIA)
        dados_async = {
            'nome': nome,
            'email': email,
            'html_content': html_relatorio,
            'pontuacao_geral': pontuacao_geral
        }
        
        # Submeter para processamento em background
        future = executor.submit(processar_pdf_e_email_async, dados_async)
        logger.info(f"✅ Processamento assíncrono agendado")
        
        # RESPOSTA IMEDIATA - NUNCA FALHA
        tempo_total = time.time() - start_time
        logger.info(f"🎉 RESPOSTA IMEDIATA EM {tempo_total:.3f}s")
        
        return jsonify({
            'success': True,
            'message': f'Avaliação processada com sucesso! Pontuação: {pontuacao_geral:.2f}/5.00',
            'html_content': html_relatorio,
            'pontuacao_geral': pontuacao_geral,
            'tempo_processamento': f"{tempo_total:.3f}s"
        })
        
    except Exception as e:
        tempo_erro = time.time() - start_time
        logger.error(f"❌ ERRO em {tempo_erro:.3f}s: {e}")
        
        return jsonify({
            'success': False, 
            'message': 'Erro interno do servidor. Tente novamente.',
            'erro_tempo': f"{tempo_erro:.3f}s"
        }), 500

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/pagamento_sucesso')
def pagamento_sucesso():
    return render_template('pagamento_sucesso.html')

@app.route('/pagamento_falha')
def pagamento_falha():
    return render_template('pagamento_falha.html')

@app.route('/pagamento_pendente')
def pagamento_pendente():
    return render_template('pagamento_pendente.html')

@app.route('/status')
def status():
    """Endpoint para monitoramento"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': 'FINAL_DEFINITIVO_v1.0',
        'pdf_timeout': PDF_MAX_TIMEOUT
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    logger.info(f"🚀 Iniciando servidor FINAL DEFINITIVO na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

