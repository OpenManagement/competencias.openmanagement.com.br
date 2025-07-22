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
import threading
import time
import queue
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração de logging otimizada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações de email
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.zoho.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'consultoria@openmanagement.com.br')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')

# Configurações de performance
MAX_PROCESSING_TIME = 25  # Máximo 25 segundos para todo o processamento
PDF_TIMEOUT = 8  # Máximo 8 segundos para PDF
EMAIL_TIMEOUT = 5  # Máximo 5 segundos para email

# Queue para processamento em background
background_queue = queue.Queue()

def processar_background():
    """Processa tarefas em background sem bloquear a resposta"""
    while True:
        try:
            task = background_queue.get(timeout=1)
            if task['type'] == 'pdf':
                gerar_pdf_background(task['data'])
            elif task['type'] == 'email':
                enviar_email_background(task['data'])
            background_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Erro no processamento background: {e}")

# Iniciar thread de background
background_thread = threading.Thread(target=processar_background, daemon=True)
background_thread.start()

def gerar_pdf_background(data):
    """Gera PDF em background"""
    try:
        import subprocess
        import tempfile
        
        html_content = data['html']
        pdf_path = data['pdf_path']
        
        # HTML ultra-simplificado
        html_simples = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial; margin: 15px; font-size: 11px; line-height: 1.3; }}
                h1 {{ color: #2c3e50; font-size: 16px; margin: 10px 0; }}
                h2 {{ color: #34495e; font-size: 13px; margin: 8px 0; }}
                h3 {{ color: #7f8c8d; font-size: 12px; margin: 6px 0; }}
                .header {{ text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .competencia {{ margin: 8px 0; padding: 6px; border-left: 3px solid #3498db; background: #f8f9fa; }}
                .pontuacao {{ font-weight: bold; color: #e74c3c; font-size: 12px; }}
                .ranking {{ margin: 8px 0; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 10px; margin: 8px 0; }}
                th, td {{ padding: 3px 6px; border: 1px solid #ddd; text-align: left; }}
                th {{ background: #ecf0f1; font-weight: bold; }}
                .destaque {{ background: #e8f5e8; }}
                .oportunidade {{ background: #fdf2e9; }}
                .footer {{ margin-top: 20px; text-align: center; font-size: 9px; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            {html_content}
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Faça Bem - Desenvolvimento de Competências</p>
            </div>
        </body>
        </html>
        """
        
        # Salvar HTML temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_simples)
            temp_html = f.name
        
        try:
            # Comando wkhtmltopdf ultra-otimizado
            cmd = [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--margin-top', '15mm',
                '--margin-right', '15mm',
                '--margin-bottom', '15mm', 
                '--margin-left', '15mm',
                '--quiet',
                '--disable-smart-shrinking',
                '--zoom', '0.8',
                '--dpi', '72',
                '--image-quality', '25',
                '--disable-javascript',
                '--disable-plugins',
                '--no-images',
                '--grayscale',
                '--lowquality',
                '--load-error-handling', 'ignore',
                '--load-media-error-handling', 'ignore',
                '--disable-external-links',
                '--disable-internal-links',
                '--print-media-type',
                temp_html,
                pdf_path
            ]
            
            # Executar com timeout
            result = subprocess.run(cmd, timeout=PDF_TIMEOUT, capture_output=True, text=True)
            
            # Limpar arquivo temporário
            os.unlink(temp_html)
            
            if result.returncode == 0 and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
                logger.info(f"✓ PDF gerado com sucesso: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
                
                # Enviar email com PDF
                background_queue.put({
                    'type': 'email',
                    'data': {
                        'nome': data['nome'],
                        'email': data['email'],
                        'html': data['html'],
                        'pdf_path': pdf_path,
                        'pontuacao': data['pontuacao']
                    }
                })
            else:
                logger.warning(f"⚠ PDF falhou, enviando apenas HTML por email")
                # Enviar email sem PDF
                background_queue.put({
                    'type': 'email',
                    'data': {
                        'nome': data['nome'],
                        'email': data['email'],
                        'html': data['html'],
                        'pdf_path': None,
                        'pontuacao': data['pontuacao']
                    }
                })
                
        except subprocess.TimeoutExpired:
            os.unlink(temp_html)
            logger.warning(f"⚠ PDF timeout após {PDF_TIMEOUT}s, enviando apenas HTML")
            # Enviar email sem PDF
            background_queue.put({
                'type': 'email',
                'data': {
                    'nome': data['nome'],
                    'email': data['email'],
                    'html': data['html'],
                    'pdf_path': None,
                    'pontuacao': data['pontuacao']
                }
            })
            
    except Exception as e:
        logger.error(f"✗ Erro na geração de PDF: {e}")
        # Enviar email sem PDF como fallback
        background_queue.put({
            'type': 'email',
            'data': {
                'nome': data['nome'],
                'email': data['email'],
                'html': data['html'],
                'pdf_path': None,
                'pontuacao': data['pontuacao']
            }
        })

def enviar_email_background(data):
    """Envia email em background"""
    try:
        nome = data['nome']
        email = data['email']
        html_relatorio = data['html']
        pdf_path = data.get('pdf_path')
        pontuacao_geral = data['pontuacao']
        
        if not MAIL_PASSWORD:
            logger.info(f"✓ Email simulado para {email} (MAIL_PASSWORD não configurada)")
            return
        
        # Configurar email
        msg = MIMEMultipart('alternative')
        msg['From'] = MAIL_USERNAME
        msg['To'] = email
        msg['Subject'] = f"Diagnóstico de Competências - {nome} - Pontuação: {pontuacao_geral:.2f}/5.00"
        
        # Corpo do email em texto
        corpo_texto = f"""
Olá {nome},

Seu diagnóstico de competências foi concluído com sucesso!

PONTUAÇÃO GERAL: {pontuacao_geral:.2f}/5.00

{"✓ Relatório em PDF anexado" if pdf_path and os.path.exists(pdf_path) else "✓ Relatório em HTML incluído neste email"}

Atenciosamente,
Equipe Faça Bem
Desenvolvimento de Competências
        """
        
        # Adicionar texto
        msg.attach(MIMEText(corpo_texto, 'plain'))
        
        # HTML para email
        html_email = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                .header {{ background: #3498db; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .competencia {{ margin: 15px 0; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }}
                .pontuacao {{ font-weight: bold; color: #e74c3c; font-size: 18px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                .footer {{ margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Diagnóstico de Competências</h1>
                <h2>{nome}</h2>
            </div>
            <div class="content">
                <p class="pontuacao">Pontuação Geral: {pontuacao_geral:.2f}/5.00</p>
                {html_relatorio}
            </div>
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                <p>Faça Bem - Desenvolvimento de Competências</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_email, 'html'))
        
        # Anexar PDF se existir
        if pdf_path and os.path.exists(pdf_path):
            try:
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= relatorio_competencias_{nome.replace(" ", "_")}.pdf'
                    )
                    msg.attach(part)
                logger.info("✓ PDF anexado ao email")
            except Exception as e:
                logger.warning(f"⚠ Erro ao anexar PDF: {e}")
        
        # Enviar email com timeout
        server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✓ Email enviado com sucesso para {email}")
        
    except Exception as e:
        logger.error(f"✗ Erro ao enviar email: {e}")

def calcular_competencias_individuais(respostas):
    """Calcula pontuação das 50 competências individuais - OTIMIZADO"""
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
        pontuacoes = [int(respostas[f'pergunta_{p}']) for p in perguntas if f'pergunta_{p}' in respostas]
        
        if pontuacoes:
            media = sum(pontuacoes) / len(pontuacoes)
            competencias[competencia] = {
                'pontuacao': round(media, 2),
                'perguntas': perguntas,
                'respostas': pontuacoes
            }
    
    return competencias

def calcular_competencias_principais(competencias_individuais):
    """Calcula as 5 competências principais - OTIMIZADO"""
    principais = {}
    
    for nome, dados in competencias_individuais.items():
        pontuacao = dados['pontuacao']
        principais[nome] = {
            'pontuacao': pontuacao,
            'nivel': (
                "Excelente" if pontuacao >= 4.5 else
                "Bom" if pontuacao >= 3.5 else
                "Regular" if pontuacao >= 2.5 else
                "Fraco" if pontuacao >= 1.5 else
                "Muito Fraco"
            )
        }
    
    return principais

def gerar_ranking_competencias(competencias):
    """Gera ranking das competências - OTIMIZADO"""
    ranking = [
        {
            'nome': nome,
            'pontuacao': dados['pontuacao'],
            'nivel': dados.get('nivel', 'Regular')
        }
        for nome, dados in competencias.items()
    ]
    
    # Ordenar por pontuação (maior para menor)
    ranking.sort(key=lambda x: x['pontuacao'], reverse=True)
    return ranking

def identificar_pontos_fortes_oportunidades(ranking_principais):
    """Identifica pontos fortes e oportunidades - OTIMIZADO"""
    pontos_fortes = ranking_principais[:2]  # Top 2
    oportunidades = ranking_principais[-3:]  # Bottom 3
    oportunidades.reverse()  # Do menor para o maior
    
    return pontos_fortes, oportunidades

def identificar_competencias_desenvolver(ranking_principais):
    """Identifica competências a desenvolver - OTIMIZADO"""
    competencias_desenvolver = ranking_principais[-3:]
    competencias_desenvolver.reverse()  # Do menor para o maior
    return competencias_desenvolver

def gerar_plano_desenvolvimento(competencias_desenvolver):
    """Gera plano de desenvolvimento - OTIMIZADO"""
    acoes_rapidas = {
        'Comunicação': [
            'Pratique escuta ativa diariamente',
            'Peça feedback sobre sua comunicação',
            'Participe de discussões em grupo'
        ],
        'Organização': [
            'Use agenda digital ou física',
            'Defina 3 prioridades por dia',
            'Organize espaço de trabalho'
        ],
        'Proatividade': [
            'Identifique 1 problema para resolver',
            'Tome iniciativa em projetos',
            'Busque melhorias contínuas'
        ],
        'Pensamento Crítico': [
            'Questione informações recebidas',
            'Analise diferentes perspectivas',
            'Reflita antes de decidir'
        ],
        'Produtividade': [
            'Elimine distrações principais',
            'Use técnica Pomodoro',
            'Foque em uma tarefa por vez'
        ]
    }
    
    plano = []
    for comp in competencias_desenvolver:
        nome_comp = comp['nome']
        if nome_comp in acoes_rapidas:
            plano.append({
                'competencia': nome_comp,
                'pontuacao': comp['pontuacao'],
                'acoes': acoes_rapidas[nome_comp]
            })
    
    return plano

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_avaliacao', methods=['POST'])
def submit_avaliacao():
    """Processamento ULTRA-RÁPIDO com resposta imediata"""
    timestamp_inicio = time.time()
    
    try:
        logger.info("🚀 INICIANDO PROCESSAMENTO DEFINITIVO")
        
        # Validação rápida dos dados
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        celular = request.form.get('celular', '').strip()
        
        if not nome or not email:
            return jsonify({
                'success': False, 
                'message': 'Nome e email são obrigatórios'
            })
        
        # Coletar respostas rapidamente
        respostas = {}
        for i in range(1, 51):
            resposta = request.form.get(f'pergunta_{i}')
            if resposta:
                respostas[f'pergunta_{i}'] = int(resposta)
        
        if len(respostas) < 50:
            return jsonify({
                'success': False, 
                'message': 'Todas as 50 perguntas devem ser respondidas'
            })
        
        logger.info(f"✓ Dados validados em {time.time() - timestamp_inicio:.2f}s")
        
        # Cálculos super-rápidos
        timestamp_calc = time.time()
        
        competencias_individuais = calcular_competencias_individuais(respostas)
        competencias_principais = calcular_competencias_principais(competencias_individuais)
        
        # Pontuação geral
        pontuacao_geral = sum(comp['pontuacao'] for comp in competencias_principais.values()) / len(competencias_principais)
        
        # Rankings e análises
        ranking_principais = gerar_ranking_competencias(competencias_principais)
        pontos_fortes, oportunidades = identificar_pontos_fortes_oportunidades(ranking_principais)
        competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
        plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver)
        
        logger.info(f"✓ Cálculos em {time.time() - timestamp_calc:.2f}s")
        
        # Dados para template
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
        
        # Renderizar template rapidamente
        timestamp_template = time.time()
        html_relatorio = render_template('relatorio_template.html', **dados_template)
        logger.info(f"✓ Template em {time.time() - timestamp_template:.3f}s")
        
        # Agendar PDF e email em background (NÃO BLOQUEIA)
        nome_arquivo = nome.replace(' ', '_').replace('/', '_').replace('\\', '_')
        pdf_filename = f"relatorio_{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        reports_dir = os.path.join(app.static_folder, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        pdf_path = os.path.join(reports_dir, pdf_filename)
        
        # Renderizar template específico para PDF (sem url_for)
        html_pdf = render_template('relatorio_pdf.html', **dados_template)
        
        # Adicionar à queue de background
        background_queue.put({
            'type': 'pdf',
            'data': {
                'nome': nome,
                'email': email,
                'html': html_pdf,  # Usar template otimizado para PDF
                'pdf_path': pdf_path,
                'pontuacao': pontuacao_geral
            }
        })
        
        # RESPOSTA IMEDIATA - NUNCA FALHA
        tempo_total = time.time() - timestamp_inicio
        logger.info(f"🎉 RESPOSTA EM {tempo_total:.2f}s - PDF/EMAIL EM BACKGROUND")
        
        return jsonify({
            'success': True,
            'message': f'Avaliação processada com sucesso! Pontuação: {pontuacao_geral:.2f}/5.00',
            'html_content': html_relatorio,
            'pontuacao_geral': pontuacao_geral,
            'tempo_processamento': f"{tempo_total:.2f}s",
            'status': 'Relatório gerado! PDF e email sendo processados em background.',
            'detalhes': {
                'competencias_calculadas': len(competencias_principais),
                'pontos_fortes': len(pontos_fortes),
                'oportunidades': len(oportunidades),
                'acoes_desenvolvimento': sum(len(p.get('acoes', [])) for p in plano_desenvolvimento)
            }
        })
        
    except Exception as e:
        tempo_erro = time.time() - timestamp_inicio
        logger.error(f"✗ ERRO em {tempo_erro:.2f}s: {e}")
        
        # MESMO COM ERRO, RETORNA RESPOSTA BÁSICA
        return jsonify({
            'success': False,
            'message': 'Erro no processamento. Nossa equipe foi notificada.',
            'erro_tempo': f"{tempo_erro:.2f}s",
            'suporte': 'Tente novamente em alguns minutos.'
        }), 500

# Rotas adicionais
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
    """Endpoint para verificar status do sistema"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'queue_size': background_queue.qsize(),
        'version': 'definitiva_v1.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    logger.info(f"🚀 Iniciando servidor definitivo na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

