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
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações de email
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.zoho.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'consultoria@openmanagement.com.br')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')

# Timeout ultra-agressivo para PDF
PDF_TIMEOUT = 10  # Apenas 10 segundos

def gerar_pdf_rapido_ou_falhar(html_content, pdf_path):
    """Tenta gerar PDF rapidamente ou falha graciosamente"""
    try:
        import pdfkit
        
        # Opções mínimas para velocidade máxima
        options = {
            'page-size': 'A4',
            'margin-top': '0.3in',
            'margin-right': '0.3in',
            'margin-bottom': '0.3in', 
            'margin-left': '0.3in',
            'encoding': "UTF-8",
            'quiet': '',
            'no-outline': None,
            'disable-smart-shrinking': '',
            'zoom': '0.75',
            'dpi': '72',  # DPI mínimo
            'image-dpi': '72',
            'image-quality': '30',  # Qualidade mínima
            'disable-javascript': '',
            'disable-plugins': '',
            'no-images': '',  # Sem imagens
            'grayscale': '',  # Escala de cinza
            'lowquality': '',
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore'
        }
        
        # HTML ultra-simplificado
        html_simples = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial; margin: 20px; font-size: 12px; }}
                h1 {{ color: #2c3e50; font-size: 18px; }}
                h2 {{ color: #34495e; font-size: 14px; }}
                .competencia {{ margin: 10px 0; padding: 5px; border-left: 3px solid #3498db; }}
                .pontuacao {{ font-weight: bold; color: #e74c3c; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
                th, td {{ padding: 4px; border: 1px solid #ddd; }}
                th {{ background: #f8f9fa; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Tentar gerar com timeout de processo
        import subprocess
        import tempfile
        
        # Salvar HTML temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_simples)
            temp_html = f.name
        
        try:
            # Comando wkhtmltopdf direto com timeout
            cmd = [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--margin-top', '0.3in',
                '--margin-right', '0.3in', 
                '--margin-bottom', '0.3in',
                '--margin-left', '0.3in',
                '--quiet',
                '--disable-smart-shrinking',
                '--zoom', '0.75',
                '--dpi', '72',
                '--image-quality', '30',
                '--disable-javascript',
                '--no-images',
                '--grayscale',
                '--lowquality',
                '--load-error-handling', 'ignore',
                temp_html,
                pdf_path
            ]
            
            # Executar com timeout
            result = subprocess.run(cmd, timeout=PDF_TIMEOUT, capture_output=True)
            
            # Limpar arquivo temporário
            os.unlink(temp_html)
            
            if result.returncode == 0 and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 500:
                return True, "PDF gerado com sucesso"
            else:
                return False, f"wkhtmltopdf falhou: {result.stderr.decode()}"
                
        except subprocess.TimeoutExpired:
            os.unlink(temp_html)
            return False, f"Timeout após {PDF_TIMEOUT} segundos"
        except Exception as e:
            os.unlink(temp_html)
            return False, f"Erro no subprocess: {str(e)}"
            
    except ImportError:
        return False, "pdfkit não disponível"
    except Exception as e:
        return False, f"Erro geral: {str(e)}"

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

def enviar_email_com_fallback(nome, email, html_relatorio, pdf_path, pontuacao_geral):
    """Envia email com PDF se disponível, senão apenas HTML"""
    try:
        if not MAIL_PASSWORD:
            logger.warning("MAIL_PASSWORD não configurada - simulando envio de email")
            return True
        
        # Configurar email
        msg = MIMEMultipart('alternative')
        msg['From'] = MAIL_USERNAME
        msg['To'] = email
        msg['Subject'] = f"Seu Diagnóstico de Competências - Pontuação: {pontuacao_geral:.2f}/5.00"
        
        # Corpo do email em texto
        corpo_texto = f"""
        Olá {nome},
        
        Seu diagnóstico de competências foi concluído com sucesso!
        
        Pontuação Geral: {pontuacao_geral:.2f}/5.00
        
        {"Em anexo você encontrará seu relatório completo em PDF." if pdf_path and os.path.exists(pdf_path) else "Seu relatório está incluído neste email em formato HTML."}
        
        Atenciosamente,
        Equipe Faça Bem
        """
        
        # Adicionar texto
        msg.attach(MIMEText(corpo_texto, 'plain'))
        
        # Se não tiver PDF, incluir HTML no corpo do email
        if not pdf_path or not os.path.exists(pdf_path):
            # HTML simplificado para email
            html_email = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .competencia {{ margin: 10px 0; padding: 10px; border-left: 4px solid #3498db; }}
                    .pontuacao {{ font-weight: bold; color: #e74c3c; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>Diagnóstico de Competências - {nome}</h1>
                <p><strong>Pontuação Geral: {pontuacao_geral:.2f}/5.00</strong></p>
                {html_relatorio}
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
                        f'attachment; filename= {os.path.basename(pdf_path)}'
                    )
                    msg.attach(part)
                logger.info("PDF anexado ao email")
            except Exception as e:
                logger.warning(f"Erro ao anexar PDF: {e}")
        
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
        logger.info("=== INICIANDO PROCESSAMENTO ULTRA-OTIMIZADO ===")
        
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
        
        logger.info(f"✓ Dados coletados em {time.time() - timestamp_inicio:.2f}s")
        
        # Calcular competências (RÁPIDO)
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
        
        logger.info(f"✓ Cálculos concluídos em {time.time() - timestamp_calculo:.2f}s")
        
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
        
        # Renderizar template HTML (RÁPIDO)
        timestamp_template = time.time()
        html_relatorio = render_template('relatorio_template.html', **dados_template)
        logger.info(f"✓ Template renderizado em {time.time() - timestamp_template:.2f}s")
        
        # Tentar gerar PDF em background (NÃO BLOQUEIA)
        pdf_path = None
        pdf_gerado = False
        
        def gerar_pdf_background():
            nonlocal pdf_path, pdf_gerado
            try:
                timestamp_pdf = time.time()
                
                # Preparar nome do arquivo PDF
                nome_arquivo = nome.replace(' ', '_').replace('/', '_').replace('\\', '_')
                pdf_filename = f"relatorio_{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Garantir que o diretório existe
                reports_dir = os.path.join(app.static_folder, 'reports')
                os.makedirs(reports_dir, exist_ok=True)
                pdf_path_temp = os.path.join(reports_dir, pdf_filename)
                
                # Tentar gerar PDF rapidamente
                sucesso, mensagem = gerar_pdf_rapido_ou_falhar(html_relatorio, pdf_path_temp)
                
                if sucesso:
                    pdf_path = pdf_path_temp
                    pdf_gerado = True
                    logger.info(f"✓ PDF gerado em background em {time.time() - timestamp_pdf:.2f}s")
                else:
                    logger.warning(f"⚠ PDF falhou em background: {mensagem}")
                    
            except Exception as e:
                logger.error(f"✗ Erro no PDF background: {e}")
        
        # Iniciar geração de PDF em background
        pdf_thread = threading.Thread(target=gerar_pdf_background)
        pdf_thread.daemon = True
        pdf_thread.start()
        
        # Aguardar PDF por no máximo 8 segundos
        pdf_thread.join(timeout=8)
        
        # Enviar email (com ou sem PDF)
        timestamp_email = time.time()
        try:
            envio_sucesso = enviar_email_com_fallback(nome, email, html_relatorio, pdf_path, pontuacao_geral)
            if envio_sucesso:
                logger.info(f"✓ Email enviado em {time.time() - timestamp_email:.2f}s")
            else:
                logger.warning(f"⚠ Falha no envio de email")
        except Exception as e:
            logger.error(f"✗ Erro ao enviar email: {e}")
        
        # Retornar resposta SEMPRE com sucesso
        tempo_total = time.time() - timestamp_inicio
        logger.info(f"🎉 PROCESSAMENTO COMPLETO EM {tempo_total:.2f}s")
        
        return jsonify({
            'success': True,
            'message': f'Avaliação processada com sucesso! Pontuação: {pontuacao_geral:.2f}/5.00',
            'html_content': html_relatorio,
            'pontuacao_geral': pontuacao_geral,
            'tempo_processamento': f"{tempo_total:.2f}s",
            'pdf_gerado': pdf_gerado,
            'detalhes': {
                'competencias_calculadas': len(competencias_principais),
                'pontos_fortes': len(pontos_fortes),
                'oportunidades': len(oportunidades),
                'plano_acoes': len(plano_desenvolvimento)
            }
        })
        
    except Exception as e:
        logger.error(f"✗ ERRO CRÍTICO: {e}")
        return jsonify({
            'success': False, 
            'message': 'Erro interno do servidor. Tente novamente.',
            'erro_tecnico': str(e)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    app.run(host='0.0.0.0', port=port, debug=False)

