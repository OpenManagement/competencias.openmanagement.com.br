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
import subprocess
import signal
import threading
import time
import base64

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

# Timeout para geração de PDF (em segundos)
PDF_TIMEOUT = 15  # Timeout agressivo de 15 segundos

# Tabela de referência das competências (importada do arquivo original)
from tabela_referencia_competencias import COMPETENCIAS_ACOES

# Função para timeout de processo
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operação excedeu o tempo limite")

def gerar_pdf_com_timeout(html_content, pdf_path, timeout=PDF_TIMEOUT):
    """Gera PDF com timeout agressivo e fallback"""
    
    def gerar_pdf_thread(html_content, pdf_path, result_container):
        try:
            # Opções ultra-otimizadas para velocidade máxima
            options = {
                'page-size': 'A4',
                'margin-top': '0.5in',
                'margin-right': '0.5in', 
                'margin-bottom': '0.5in',
                'margin-left': '0.5in',
                'encoding': "UTF-8",
                'no-outline': None,
                'disable-smart-shrinking': '',
                'print-media-type': '',
                'zoom': '0.8',  # Reduzido para acelerar
                'dpi': '96',    # DPI mínimo para velocidade
                'image-dpi': '96',
                'image-quality': '50',  # Qualidade mínima para velocidade
                'quiet': '',
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore',
                'disable-plugins': '',
                'disable-javascript': '',
                'no-stop-slow-scripts': '',
                'disable-external-links': '',
                'disable-internal-links': '',
                'disable-forms': '',
                'no-images': '',  # Desabilitar imagens para acelerar
                'grayscale': '',  # Escala de cinza para acelerar
                'lowquality': '', # Baixa qualidade para acelerar
                'disable-local-file-access': '',
                'enable-local-file-access': None
            }
            
            # Gerar PDF
            pdfkit.from_string(html_content, pdf_path, options=options)
            result_container['success'] = True
            result_container['path'] = pdf_path
            
        except Exception as e:
            result_container['success'] = False
            result_container['error'] = str(e)
    
    # Container para resultado da thread
    result_container = {'success': False, 'error': None, 'path': None}
    
    # Criar e iniciar thread
    thread = threading.Thread(target=gerar_pdf_thread, args=(html_content, pdf_path, result_container))
    thread.daemon = True
    thread.start()
    
    # Aguardar com timeout
    thread.join(timeout)
    
    if thread.is_alive():
        # Thread ainda está rodando - timeout
        logger.warning(f"Timeout na geração de PDF após {timeout} segundos")
        return False, "Timeout na geração de PDF"
    
    if result_container['success']:
        # Verificar se arquivo foi criado
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:  # Pelo menos 1KB
            return True, pdf_path
        else:
            return False, "PDF gerado mas arquivo inválido"
    else:
        return False, result_container.get('error', 'Erro desconhecido')

def simplificar_html_para_pdf(html_content):
    """Simplifica HTML removendo elementos que podem causar lentidão"""
    
    # Remover scripts e elementos interativos
    html_simplificado = html_content
    
    # Substituir imagens por placeholders ou remover
    html_simplificado = html_simplificado.replace('<img', '<!-- img removida para velocidade --><img style="display:none;"')
    
    # Remover CSS complexo e manter apenas básico
    css_basico = """
    <style>
    body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
    h1, h2, h3 { color: #2c3e50; margin: 10px 0; }
    .competencia { margin: 15px 0; padding: 10px; border-left: 4px solid #3498db; }
    .pontuacao { font-weight: bold; color: #e74c3c; }
    .ranking { margin: 10px 0; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
    th { background-color: #f2f2f2; }
    .progress-bar { width: 100%; height: 20px; background-color: #ecf0f1; border-radius: 10px; overflow: hidden; }
    .progress-fill { height: 100%; background-color: #3498db; }
    </style>
    """
    
    # Inserir CSS básico no início do HTML
    if '<head>' in html_simplificado:
        html_simplificado = html_simplificado.replace('<head>', f'<head>{css_basico}')
    else:
        html_simplificado = f'<html><head>{css_basico}</head><body>{html_simplificado}</body></html>'
    
    return html_simplificado

# Importar funções de cálculo do arquivo original
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
    
    # Ordenar por pontuação (maior para menor)
    ranking.sort(key=lambda x: x['pontuacao'], reverse=True)
    return ranking

def identificar_pontos_fortes_oportunidades(ranking_principais):
    """Identifica pontos fortes e oportunidades de melhoria"""
    pontos_fortes = ranking_principais[:2]  # Top 2
    oportunidades = ranking_principais[-3:]  # Bottom 3 (invertido)
    oportunidades.reverse()  # Para mostrar do menor para o maior
    
    return pontos_fortes, oportunidades

def identificar_competencias_desenvolver(ranking_principais):
    """Identifica as 3 competências com menores pontuações para desenvolvimento"""
    competencias_desenvolver = ranking_principais[-3:]
    competencias_desenvolver.reverse()  # Do menor para o maior
    return competencias_desenvolver

def gerar_plano_desenvolvimento(competencias_desenvolver, versao='premium'):
    """Gera plano de desenvolvimento simplificado"""
    plano = []
    
    acoes_genericas = {
        'Comunicação': [
            'Pratique escuta ativa em conversas diárias',
            'Solicite feedback sobre sua comunicação',
            'Participe de grupos de discussão ou debates'
        ],
        'Organização': [
            'Use uma agenda ou aplicativo de tarefas',
            'Defina prioridades claras para cada dia',
            'Organize seu espaço de trabalho regularmente'
        ],
        'Proatividade': [
            'Identifique problemas antes que se tornem urgentes',
            'Tome iniciativa em projetos e atividades',
            'Busque oportunidades de melhoria contínua'
        ],
        'Pensamento Crítico': [
            'Questione informações antes de aceitar como verdade',
            'Analise diferentes perspectivas antes de decidir',
            'Reflita sobre suas decisões e aprenda com erros'
        ],
        'Produtividade': [
            'Elimine distrações durante o trabalho',
            'Use técnicas de gestão de tempo (Pomodoro)',
            'Foque em uma tarefa por vez'
        ]
    }
    
    for comp in competencias_desenvolver:
        nome_comp = comp['nome']
        if nome_comp in acoes_genericas:
            plano.append({
                'competencia': nome_comp,
                'pontuacao': comp['pontuacao'],
                'acoes': acoes_genericas[nome_comp]
            })
    
    return plano

def enviar_email(nome, email, pdf_path, pontuacao_geral):
    """Envia email com PDF anexado"""
    try:
        if not MAIL_PASSWORD:
            logger.warning("MAIL_PASSWORD não configurada - simulando envio de email")
            return True
        
        # Configurar email
        msg = MIMEMultipart()
        msg['From'] = MAIL_USERNAME
        msg['To'] = email
        msg['Subject'] = f"Seu Diagnóstico de Competências - Pontuação: {pontuacao_geral:.2f}/5.00"
        
        # Corpo do email
        corpo = f"""
        Olá {nome},
        
        Seu diagnóstico de competências foi concluído com sucesso!
        
        Pontuação Geral: {pontuacao_geral:.2f}/5.00
        
        Em anexo você encontrará seu relatório completo em PDF com:
        - Análise detalhada das 5 competências
        - Seus pontos fortes e oportunidades de melhoria
        - Plano de desenvolvimento personalizado
        
        Atenciosamente,
        Equipe Faça Bem
        """
        
        msg.attach(MIMEText(corpo, 'plain'))
        
        # Anexar PDF se existir
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
        
        # Enviar email
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
    try:
        timestamp_inicio = time.time()
        logger.info(f"Iniciando processamento da avaliação...")
        
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
        
        logger.info(f"Dados coletados em {time.time() - timestamp_inicio:.2f}s")
        
        # Calcular competências
        timestamp_calculo = time.time()
        competencias_individuais = calcular_competencias_individuais(respostas)
        competencias_principais = calcular_competencias_principais(competencias_individuais)
        
        # Calcular pontuação geral
        pontuacao_geral = sum(comp['pontuacao'] for comp in competencias_principais.values()) / len(competencias_principais)
        
        # Gerar rankings
        ranking_principais = gerar_ranking_competencias(competencias_principais)
        pontos_fortes, oportunidades = identificar_pontos_fortes_oportunidades(ranking_principais)
        competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
        plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver)
        
        logger.info(f"Cálculos concluídos em {time.time() - timestamp_calculo:.2f}s")
        
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
        timestamp_template = time.time()
        html_relatorio = render_template('relatorio_template.html', **dados_template)
        logger.info(f"Template renderizado em {time.time() - timestamp_template:.2f}s")
        
        # Tentar gerar PDF com timeout agressivo
        pdf_path = None
        timestamp_pdf = time.time()
        
        try:
            # Preparar nome do arquivo PDF
            nome_arquivo = nome.replace(' ', '_').replace('/', '_').replace('\\', '_')
            pdf_filename = f"relatorio_{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Garantir que o diretório existe
            reports_dir = os.path.join(app.static_folder, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            pdf_path = os.path.join(reports_dir, pdf_filename)
            
            # Simplificar HTML para PDF
            html_simplificado = simplificar_html_para_pdf(html_relatorio)
            
            # Tentar gerar PDF com timeout
            sucesso_pdf, resultado_pdf = gerar_pdf_com_timeout(html_simplificado, pdf_path, PDF_TIMEOUT)
            
            if sucesso_pdf:
                logger.info(f"PDF gerado com sucesso em {time.time() - timestamp_pdf:.2f}s: {pdf_path}")
            else:
                logger.warning(f"Falha na geração de PDF após {time.time() - timestamp_pdf:.2f}s: {resultado_pdf}")
                pdf_path = None
                
        except Exception as e:
            logger.error(f"Erro na geração de PDF: {e}")
            pdf_path = None
        
        # Tentar enviar email (mesmo sem PDF)
        timestamp_email = time.time()
        try:
            envio_sucesso = enviar_email(nome, email, pdf_path, pontuacao_geral)
            if envio_sucesso:
                logger.info(f"Email enviado em {time.time() - timestamp_email:.2f}s")
            else:
                logger.warning(f"Falha no envio de email após {time.time() - timestamp_email:.2f}s")
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
        
        # Retornar resposta sempre com sucesso
        tempo_total = time.time() - timestamp_inicio
        logger.info(f"Processamento completo em {tempo_total:.2f}s")
        
        return jsonify({
            'success': True,
            'message': f'Avaliação processada com sucesso! Pontuação: {pontuacao_geral:.2f}/5.00',
            'html_content': html_relatorio,
            'pontuacao_geral': pontuacao_geral,
            'tempo_processamento': f"{tempo_total:.2f}s",
            'pdf_gerado': pdf_path is not None
        })
        
    except Exception as e:
        logger.error(f"Erro no processamento da avaliação: {e}")
        return jsonify({
            'success': False, 
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500

# Rotas adicionais do site original
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    app.run(host='0.0.0.0', port=port, debug=False)

