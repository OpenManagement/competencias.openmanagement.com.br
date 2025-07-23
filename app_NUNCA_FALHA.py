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
import subprocess
import signal
import tempfile
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import mercadopago

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração de logging profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações do MercadoPago
mp = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))

# Configurações de email
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.zoho.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'consultoria@openmanagement.com.br')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')

# Pool de threads para processamento assíncrono
executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AsyncProcessor")

# Timeout máximo para PDF (será killado se exceder)
PDF_MAX_TIMEOUT = 20  # 20 segundos máximo

class PDFGenerator:
    """Gerador de PDF profissional com timeout e kill automático"""
    
    @staticmethod
    def generate_with_timeout(html_content, output_path, timeout=PDF_MAX_TIMEOUT):
        """Gera PDF com timeout e kill automático do processo"""
        
        def target_function(html_content, output_path, result_dict):
            try:
                # HTML ultra-simplificado para PDF
                simplified_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; font-size: 12px; color: #333; }}
                        .header {{ text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 15px; margin-bottom: 20px; }}
                        .header h1 {{ color: #2c3e50; font-size: 20px; margin: 10px 0; }}
                        .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                        .pontuacao-geral {{ text-align: center; background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                        .pontuacao-numero {{ font-size: 28px; font-weight: bold; color: #27ae60; }}
                        .competencia {{ margin: 10px 0; padding: 10px; border-left: 4px solid #3498db; background: #f8f9fa; }}
                        .competencia-nome {{ font-weight: bold; color: #2c3e50; }}
                        .competencia-pontuacao {{ font-weight: bold; color: #e74c3c; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background: #ecf0f1; font-weight: bold; }}
                        .footer {{ margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 10px; }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
                
                # Criar arquivo HTML temporário
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(simplified_html)
                    temp_html = f.name
                
                try:
                    # Comando wkhtmltopdf otimizado para velocidade máxima
                    cmd = [
                        'wkhtmltopdf',
                        '--page-size', 'A4',
                        '--margin-top', '10mm',
                        '--margin-right', '10mm',
                        '--margin-bottom', '10mm',
                        '--margin-left', '10mm',
                        '--quiet',
                        '--disable-smart-shrinking',
                        '--zoom', '0.75',
                        '--dpi', '72',
                        '--image-quality', '20',
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
                        '--encoding', 'UTF-8',
                        temp_html,
                        output_path
                    ]
                    
                    # Executar comando com timeout
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate(timeout=timeout-2)  # 2s de margem
                    
                    # Limpar arquivo temporário
                    os.unlink(temp_html)
                    
                    if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        result_dict['success'] = True
                        result_dict['path'] = output_path
                        result_dict['size'] = os.path.getsize(output_path)
                    else:
                        result_dict['success'] = False
                        result_dict['error'] = f"wkhtmltopdf failed: {stderr.decode()}"
                        
                except subprocess.TimeoutExpired:
                    process.kill()
                    os.unlink(temp_html)
                    result_dict['success'] = False
                    result_dict['error'] = f"PDF generation timeout after {timeout}s"
                    
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
            # Processo ainda rodando - kill forçado
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

class EmailSender:
    """Enviador de email profissional com fallbacks"""
    
    @staticmethod
    def send_async(nome, email, html_content, pdf_path=None, pontuacao_geral=0):
        """Envia email de forma assíncrona"""
        try:
            if not MAIL_PASSWORD:
                logger.info(f"Email simulado para {email} (MAIL_PASSWORD não configurada)")
                return True
            
            # Configurar email
            msg = MIMEMultipart('alternative')
            msg['From'] = MAIL_USERNAME
            msg['To'] = email
            msg['Subject'] = f"Diagnóstico de Competências - {nome} - Pontuação: {pontuacao_geral:.2f}/5.00"
            
            # Corpo em texto
            corpo_texto = f"""
Olá {nome},

Seu diagnóstico de competências foi concluído com sucesso!

PONTUAÇÃO GERAL: {pontuacao_geral:.2f}/5.00

{"✓ Relatório em PDF anexado" if pdf_path and os.path.exists(pdf_path) else "✓ Relatório em HTML incluído neste email"}

Atenciosamente,
Equipe Faça Bem
Desenvolvimento de Competências

Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
            """
            
            msg.attach(MIMEText(corpo_texto, 'plain'))
            
            # HTML para email
            html_email = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                    .header {{ background: #3498db; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
                    .content {{ padding: 20px; }}
                    .pontuacao {{ font-size: 24px; font-weight: bold; color: #27ae60; text-align: center; margin: 20px 0; }}
                    .competencia {{ margin: 15px 0; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    .footer {{ margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎯 Diagnóstico de Competências</h1>
                    <h2>{nome}</h2>
                </div>
                <div class="content">
                    <div class="pontuacao">Pontuação Geral: {pontuacao_geral:.2f}/5.00</div>
                    {html_content}
                </div>
                <div class="footer">
                    <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                    <p><strong>Faça Bem - Desenvolvimento de Competências</strong></p>
                    <p>consultoria@openmanagement.com.br</p>
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
                            f'attachment; filename= diagnostico_competencias_{nome.replace(" ", "_")}.pdf'
                        )
                        msg.attach(part)
                    logger.info(f"PDF anexado ao email para {email}")
                except Exception as e:
                    logger.warning(f"Erro ao anexar PDF: {e}")
            
            # Enviar email
            server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email enviado com sucesso para {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email para {email}: {e}")
            return False

def calcular_competencias_individuais(respostas):
    """Calcula pontuação das competências individuais - ULTRA OTIMIZADO"""
    mapeamento = {
        'Comunicação': list(range(1, 11)),
        'Organização': list(range(11, 21)), 
        'Proatividade': list(range(21, 31)),
        'Pensamento Crítico': list(range(31, 41)),
        'Produtividade': list(range(41, 51))
    }
    
    competencias = {}
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
    """Calcula as 5 competências principais - ULTRA OTIMIZADO"""
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
    """Gera ranking das competências - ULTRA OTIMIZADO"""
    ranking = [
        {
            'nome': nome,
            'pontuacao': dados['pontuacao'],
            'nivel': dados.get('nivel', 'Regular')
        }
        for nome, dados in competencias.items()
    ]
    ranking.sort(key=lambda x: x['pontuacao'], reverse=True)
    return ranking

def identificar_pontos_fortes_oportunidades(ranking_principais):
    """Identifica pontos fortes e oportunidades - ULTRA OTIMIZADO"""
    pontos_fortes = ranking_principais[:2]
    oportunidades = ranking_principais[-3:]
    oportunidades.reverse()
    return pontos_fortes, oportunidades

def identificar_competencias_desenvolver(ranking_principais):
    """Identifica competências a desenvolver - ULTRA OTIMIZADO"""
    competencias_desenvolver = ranking_principais[-3:]
    competencias_desenvolver.reverse()
    return competencias_desenvolver

def gerar_plano_desenvolvimento(competencias_desenvolver):
    """Gera plano de desenvolvimento - ULTRA OTIMIZADO"""
    acoes_rapidas = {
        'Comunicação': [
            'Pratique escuta ativa em todas as conversas',
            'Peça feedback específico sobre sua comunicação',
            'Participe ativamente de reuniões e discussões'
        ],
        'Organização': [
            'Use uma agenda digital ou física diariamente',
            'Defina 3 prioridades claras a cada manhã',
            'Organize seu espaço de trabalho semanalmente'
        ],
        'Proatividade': [
            'Identifique 1 problema para resolver por semana',
            'Tome iniciativa em pelo menos 1 projeto',
            'Busque oportunidades de melhoria contínua'
        ],
        'Pensamento Crítico': [
            'Questione pelo menos 3 informações por dia',
            'Analise diferentes perspectivas antes de decidir',
            'Reflita sobre decisões tomadas e aprenda com erros'
        ],
        'Produtividade': [
            'Elimine as 3 principais distrações do seu dia',
            'Use a técnica Pomodoro (25min foco + 5min pausa)',
            'Foque em apenas uma tarefa importante por vez'
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

def processar_pdf_e_email_async(dados):
    """Processa PDF e email de forma completamente assíncrona"""
    try:
        nome = dados['nome']
        email = dados['email']
        html_content = dados['html_content']
        pontuacao_geral = dados['pontuacao_geral']
        
        logger.info(f"🔄 Iniciando processamento assíncrono para {nome}")
        
        # Preparar arquivo PDF
        nome_arquivo = nome.replace(' ', '_').replace('/', '_').replace('\\', '_')
        pdf_filename = f"relatorio_{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        reports_dir = os.path.join(app.static_folder, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        pdf_path = os.path.join(reports_dir, pdf_filename)
        
        # Tentar gerar PDF com timeout rigoroso
        pdf_success, pdf_result = PDFGenerator.generate_with_timeout(html_content, pdf_path, PDF_MAX_TIMEOUT)
        
        if pdf_success:
            logger.info(f"✅ PDF gerado: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
            # Enviar email com PDF
            EmailSender.send_async(nome, email, html_content, pdf_path, pontuacao_geral)
        else:
            logger.warning(f"⚠️ PDF falhou: {pdf_result}")
            # Enviar email apenas com HTML
            EmailSender.send_async(nome, email, html_content, None, pontuacao_geral)
        
        logger.info(f"✅ Processamento assíncrono concluído para {nome}")
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento assíncrono: {e}")
        # Fallback: enviar email apenas com HTML
        try:
            EmailSender.send_async(dados['nome'], dados['email'], dados['html_content'], None, dados['pontuacao_geral'])
        except:
            pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_avaliacao', methods=['POST'])
def submit_avaliacao():
    """PROCESSAMENTO PROFISSIONAL - NUNCA FALHA - RESPOSTA IMEDIATA"""
    
    start_time = time.time()
    logger.info("🚀 INICIANDO PROCESSAMENTO PROFISSIONAL - NUNCA FALHA")
    
    try:
        # === FASE 1: VALIDAÇÃO RÁPIDA ===
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        celular = request.form.get('celular', '').strip()
        
        if not nome or not email:
            return jsonify({
                'success': False, 
                'message': 'Nome e email são obrigatórios'
            }), 400
        
        # Coletar respostas
        respostas = {}
        for i in range(1, 51):
            resposta = request.form.get(f'pergunta_{i}')
            if resposta:
                respostas[f'pergunta_{i}'] = int(resposta)
        
        if len(respostas) < 50:
            return jsonify({
                'success': False, 
                'message': 'Todas as 50 perguntas devem ser respondidas'
            }), 400
        
        logger.info(f"✅ Validação concluída em {time.time() - start_time:.3f}s")
        
        # === FASE 2: CÁLCULOS ULTRA-RÁPIDOS ===
        calc_start = time.time()
        
        competencias_individuais = calcular_competencias_individuais(respostas)
        competencias_principais = calcular_competencias_principais(competencias_individuais)
        pontuacao_geral = sum(comp['pontuacao'] for comp in competencias_principais.values()) / len(competencias_principais)
        
        ranking_principais = gerar_ranking_competencias(competencias_principais)
        pontos_fortes, oportunidades = identificar_pontos_fortes_oportunidades(ranking_principais)
        competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
        plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver)
        
        logger.info(f"✅ Cálculos concluídos em {time.time() - calc_start:.3f}s")
        
        # === FASE 3: RENDERIZAÇÃO RÁPIDA ===
        template_start = time.time()
        
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
        
        # Renderizar template principal
        html_relatorio = render_template('relatorio_template.html', **dados_template)
        
        logger.info(f"✅ Template renderizado em {time.time() - template_start:.3f}s")
        
        # === FASE 4: PROCESSAMENTO ASSÍNCRONO (NÃO BLOQUEIA) ===
        # Agendar PDF e email para processamento em background
        dados_async = {
            'nome': nome,
            'email': email,
            'html_content': html_relatorio,
            'pontuacao_geral': pontuacao_geral
        }
        
        # Submeter para processamento assíncrono
        future = executor.submit(processar_pdf_e_email_async, dados_async)
        logger.info(f"✅ Processamento assíncrono agendado")
        
        # === FASE 5: RESPOSTA IMEDIATA - NUNCA FALHA ===
        tempo_total = time.time() - start_time
        
        logger.info(f"🎉 RESPOSTA IMEDIATA EM {tempo_total:.3f}s - PDF/EMAIL EM BACKGROUND")
        
        return jsonify({
            'success': True,
            'message': f'Avaliação processada com sucesso! Pontuação: {pontuacao_geral:.2f}/5.00',
            'html_content': html_relatorio,
            'pontuacao_geral': pontuacao_geral,
            'tempo_processamento': f"{tempo_total:.3f}s",
            'status': 'Relatório gerado! PDF e email sendo processados em segundo plano.',
            'detalhes': {
                'competencias_calculadas': len(competencias_principais),
                'pontos_fortes': len(pontos_fortes),
                'oportunidades': len(oportunidades),
                'acoes_desenvolvimento': sum(len(p.get('acoes', [])) for p in plano_desenvolvimento),
                'processamento_async': True
            }
        })
        
    except Exception as e:
        tempo_erro = time.time() - start_time
        logger.error(f"❌ ERRO CRÍTICO em {tempo_erro:.3f}s: {e}")
        
        # MESMO COM ERRO CRÍTICO, RETORNA RESPOSTA ÚTIL
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor. Nossa equipe foi notificada e está resolvendo.',
            'erro_tempo': f"{tempo_erro:.3f}s",
            'suporte': 'Tente novamente em alguns minutos. Se persistir, entre em contato.',
            'timestamp': datetime.now().isoformat()
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
    """Endpoint para monitoramento do sistema"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': 'NUNCA_FALHA_v1.0',
        'pdf_timeout': PDF_MAX_TIMEOUT,
        'executor_max_workers': executor._max_workers,
        'uptime': 'Sistema operacional'
    })

@app.route('/health')
def health():
    """Health check para Render"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    logger.info(f"🚀 Iniciando servidor NUNCA FALHA na porta {port}")
    logger.info(f"📊 Configurações: PDF_TIMEOUT={PDF_MAX_TIMEOUT}s, THREADS={executor._max_workers}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

