from flask import Flask, render_template, request, jsonify, url_for, session, redirect
import logging
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pdfkit
import os
import mercadopago
from tabela_referencia_competencias import COMPETENCIAS_ACOES

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuração do Mercado Pago via variáveis de ambiente
mp = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
PUBLIC_KEY = os.getenv("MP_PUBLIC_KEY")
CLIENT_ID = os.getenv("MP_CLIENT_ID")
CLIENT_SECRET = os.getenv("MP_CLIENT_SECRET")


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Mapeamento das 50 competências individuais
COMPETENCIAS_MAPEAMENTO = {
    # Comunicação (c1)
    'c1_q1': 'Escuta ativa e empática',
    'c1_q2': 'Comunicação não-violenta',
    'c1_q3': 'Curiosidade genuína',
    'c1_q4': 'Adaptação da linguagem',
    'c1_q5': 'Clareza na transmissão',
    'c1_q6': 'Busca por feedback',
    'c1_q7': 'Linguagem corporal adequada',
    'c1_q8': 'Mediação de conflitos',
    'c1_q9': 'Comunicação assertiva',
    'c1_q10': 'Reconhecimento de sucessos',
    
    # Organização (c2)
    'c2_q1': 'Planejamento antecipado',
    'c2_q2': 'Uso de sistemas organizacionais',
    'c2_q3': 'Organização do espaço',
    'c2_q4': 'Acesso rápido à informação',
    'c2_q5': 'Divisão de projetos',
    'c2_q6': 'Cumprimento de prazos',
    'c2_q7': 'Revisão de prioridades',
    'c2_q8': 'Minimização de distrações',
    'c2_q9': 'Preparação para compromissos',
    'c2_q10': 'Delegação eficaz',
    
    # Proatividade (c3)
    'c3_q1': 'Identificação antecipada',
    'c3_q2': 'Iniciativa para soluções',
    'c3_q3': 'Responsabilidade pessoal',
    'c3_q4': 'Melhoria contínua',
    'c3_q5': 'Oferta de ajuda',
    'c3_q6': 'Atitude positiva',
    'c3_q7': 'Autodesenvolvimento',
    'c3_q8': 'Adaptabilidade',
    'c3_q9': 'Transformação de ideias',
    'c3_q10': 'Antecipação de necessidades',
    
    # Pensamento Crítico (c4)
    'c4_q1': 'Questionamento de padrões',
    'c4_q2': 'Busca por evidências',
    'c4_q3': 'Reconhecimento de vieses',
    'c4_q4': 'Flexibilidade mental',
    'c4_q5': 'Análise de causas profundas',
    'c4_q6': 'Diferenciação de raciocínios',
    'c4_q7': 'Consideração de perspectivas',
    'c4_q8': 'Pausas estratégicas',
    'c4_q9': 'Avaliação de riscos',
    'c4_q10': 'Aprendizado com erros',
    
    # Produtividade (c5)
    'c5_q1': 'Foco em uma tarefa',
    'c5_q2': 'Eliminação de desperdícios',
    'c5_q3': 'Técnicas de gestão de tempo',
    'c5_q4': 'Pausas regulares',
    'c5_q5': 'Estabelecimento de metas',
    'c5_q6': 'Uso de ferramentas',
    'c5_q7': 'Equilíbrio vida-trabalho',
    'c5_q8': 'Avaliação de desempenho',
    'c5_q9': 'Autocuidado produtivo',
    'c5_q10': 'Celebração de conquistas'
}

# Mapeamento de categorias
CATEGORIAS_COMPETENCIAS = {
    'c1': 'Comunicação',
    'c2': 'Organização', 
    'c3': 'Proatividade',
    'c4': 'Pensamento Crítico',
    'c5': 'Produtividade'
}

def calcular_competencias_individuais(respostas):
    """Calcula pontuação de cada uma das 50 competências individuais"""
    competencias_individuais = {}
    
    for key, value in respostas.items():
        if key in COMPETENCIAS_MAPEAMENTO:
            try:
                valor = int(value)
                competencias_individuais[key] = {
                    'nome': COMPETENCIAS_MAPEAMENTO[key],
                    'categoria': CATEGORIAS_COMPETENCIAS[key[:2]],
                    'pontuacao': valor
                }
            except (ValueError, TypeError):
                logger.warning(f"Valor inválido para {key}: {value}")
                continue
    
    return competencias_individuais

def gerar_ranking_50_competencias(competencias_individuais):
    """Gera ranking das 50 competências ordenadas por pontuação"""
    ranking = []
    
    for key, comp in competencias_individuais.items():
        ranking.append({
            'nome': comp['nome'],
            'categoria': comp['categoria'],
            'pontuacao': comp['pontuacao']
        })
    
    # Ordenar por pontuação (decrescente) e depois por nome (alfabética)
    ranking.sort(key=lambda x: (-x['pontuacao'], x['nome']))
    
    return ranking

def calcular_competencias_principais(respostas):
    """Calcula médias das 5 competências principais"""
    competencias = {
        'comunicacao': [],
        'organizacao': [],
        'proatividade': [],
        'pensamento_critico': [],
        'produtividade': []
    }
    
    for key, value in respostas.items():
        try:
            valor = int(value)
            if key.startswith('c1_'):  # Comunicação
                competencias['comunicacao'].append(valor)
            elif key.startswith('c2_'):  # Organização
                competencias['organizacao'].append(valor)
            elif key.startswith('c3_'):  # Proatividade
                competencias['proatividade'].append(valor)
            elif key.startswith('c4_'):  # Pensamento Crítico
                competencias['pensamento_critico'].append(valor)
            elif key.startswith('c5_'):  # Produtividade
                competencias['produtividade'].append(valor)
        except (ValueError, TypeError):
            logger.warning(f"Valor inválido para {key}: {value}")
            continue
    
    # Calcular médias
    medias = {}
    for comp, valores in competencias.items():
        if valores:
            medias[comp] = sum(valores) / len(valores)
        else:
            medias[comp] = 0
    
    return medias

def gerar_ranking_principais(medias):
    """Gera ranking das 5 competências principais"""
    competencias_info = [
        {'nome': 'Comunicação', 'emoji': '🟠', 'media': medias['comunicacao']},
        {'nome': 'Organização', 'emoji': '🟡', 'media': medias['organizacao']},
        {'nome': 'Proatividade', 'emoji': '🔵', 'media': medias['proatividade']},
        {'nome': 'Pensamento Crítico', 'emoji': '🟣', 'media': medias['pensamento_critico']},
        {'nome': 'Produtividade', 'emoji': '🟢', 'media': medias['produtividade']}
    ]
    
    # Ordenar por média (decrescente)
    competencias_ordenadas = sorted(competencias_info, key=lambda x: x['media'], reverse=True)
    
    return competencias_ordenadas

def identificar_pontos_fortes_e_oportunidades(ranking_principais):
    """Identifica os 3 pontos fortes e 3 oportunidades de desenvolvimento"""
    pontos_fortes = ranking_principais[:3]  # Top 3
    oportunidades = ranking_principais[-3:]  # Bottom 3 (invertido)
    oportunidades.reverse()  # Para mostrar do menor para o maior
    
    return pontos_fortes, oportunidades

def identificar_subcompetencias_destaque(ranking_50):
    """Identifica as subcompetências mais fortes e a desenvolver"""
    top_subcompetencias = ranking_50[:5]  # Top 5
    bottom_subcompetencias = ranking_50[-5:]  # Bottom 5
    bottom_subcompetencias.reverse()  # Para mostrar do menor para o maior
    
    return top_subcompetencias, bottom_subcompetencias

def identificar_competencias_desenvolver(ranking_principais):
    """Identifica as 3 competências com menores pontuações para desenvolvimento"""
    # Pegar as 3 últimas (menores pontuações) e ordenar por pontuação crescente
    competencias_desenvolver = ranking_principais[-3:]
    competencias_desenvolver.reverse()  # Do menor para o maior
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
    
    # Para versão gratuita, retorna apenas preview
    if versao == 'gratuita':
        return plano
    
    # Para versão premium, gera plano completo
    for comp in competencias_desenvolver:
        chave_competencia = mapear_nome_competencia_para_chave(comp['nome'])
        
        if chave_competencia in COMPETENCIAS_ACOES:
            acoes_competencia = COMPETENCIAS_ACOES[chave_competencia]
            
            # Pegar as 3 ações dos graus 1, 2 e 3
            acoes_plano = []
            for grau in ['grau_1', 'grau_2', 'grau_3']:
                if grau in acoes_competencia:
                    acoes_plano.extend(acoes_competencia[grau])
            
            plano.append({
                'nome': comp['nome'],
                'acoes': acoes_plano
            })
    
    return plano

def gerar_corpo_email(nome, pontuacao_geral):
    """Gera o corpo do email personalizado"""
    return f"""Olá {nome}!

Parabéns por completar sua autoavaliação de competências! 🎉

Sua pontuação geral foi: {pontuacao_geral:.2f}/5.00

Em anexo você encontrará seu relatório personalizado com:
✅ Análise detalhada de suas competências
✅ Gráficos visuais dos resultados
✅ Ranking de pontos fortes e oportunidades
✅ Plano de desenvolvimento personalizado com ações práticas
✅ Referências para continuar evoluindo

Este relatório foi desenvolvido especialmente para você com base em suas respostas na escala Likert. Use-o como guia para acelerar seu desenvolvimento pessoal e profissional.

Lembre-se: o crescimento é uma jornada contínua. Cada pequena ação diária faz a diferença!

Sucesso em sua jornada de desenvolvimento!

Equipe Método Faça Bem  
consultoria@openmanagement.com.br"""

def enviar_email(nome, email_destino, pdf_path, pontuacao_geral):
    """Envia email com relatório em anexo usando configurações SMTP Zoho"""
    try:
        # Configurações do SMTP Zoho Mail - Exatamente conforme especificado
        smtp_server = os.getenv("MAIL_SERVER")
        smtp_port = int(os.getenv("MAIL_PORT", 465))  # Default: 465
        email_usuario = os.getenv("MAIL_USERNAME")
        email_senha = os.getenv("MAIL_PASSWORD")
        email_interno = os.getenv("MAIL_USERNAME")
        
        # Verificar se o arquivo PDF existe antes de prosseguir
        if not pdf_path or not os.path.exists(pdf_path):
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.error(f"[{timestamp}] Arquivo PDF não encontrado: {pdf_path}")
            return False
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_usuario
        msg['To'] = f"{email_destino},{email_interno}"
        msg['Subject'] = "[Método Faça Bem] Seu Relatório de Competências (PDF)"
        
        # Corpo do email conforme especificado
        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Olá {nome}!</h2>
                
                <p>Parabéns por completar sua autoavaliação de competências! 🎉</p>
                
                <p><strong>Sua pontuação geral foi: {pontuacao_geral:.2f}/5.00</strong></p>
                
                <p>Em anexo, você encontrará seu relatório personalizado em PDF com:</p>
                <ul>
                    <li>✅ Análise detalhada de suas competências</li>
                    <li>✅ Gráficos visuais dos resultados</li>
                    <li>✅ Ranking de pontos fortes e oportunidades</li>
                    <li>✅ Plano de desenvolvimento personalizado</li>
                </ul>
                
                <p>Este relatório foi desenvolvido especialmente para você com base em suas respostas na escala Likert. Use-o como guia para acelerar seu desenvolvimento pessoal e profissional.</p>
                
                <p><strong>Sucesso em sua jornada de desenvolvimento!</strong></p>
                
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 14px;">
                    <strong>Equipe Método Faça Bem</strong><br>
                    consultoria@openmanagement.com.br
                </p>
            </div>
        </body>
        </html>
        """
        
        # Versão texto simples conforme especificado
        corpo_texto = f"""Olá {nome}!

Parabéns por completar sua autoavaliação de competências! 🎉

Sua pontuação geral foi: {pontuacao_geral:.2f}/5.00

Em anexo, você encontrará seu relatório personalizado em PDF com:
✅ Análise detalhada de suas competências  
✅ Gráficos visuais dos resultados  
✅ Ranking de pontos fortes e oportunidades  
✅ Plano de desenvolvimento personalizado  

Este relatório foi desenvolvido especialmente para você com base em suas respostas na escala Likert. Use-o como guia para acelerar seu desenvolvimento pessoal e profissional.

Sucesso em sua jornada de desenvolvimento!

Equipe Método Faça Bem  
consultoria@openmanagement.com.br"""
        
        # Anexar corpo do email
        msg.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))
        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))
        
        # Anexar PDF usando MIMEBase conforme especificado
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="Relatorio_Competencias_{nome.replace(" ", "_")}.pdf"'
            )
            msg.attach(part)
        
        # Enviar email usando SSL/TLS conforme especificado
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(email_usuario, email_senha)
        text = msg.as_string()
        server.sendmail(email_usuario, [email_destino, email_interno], text)
        server.quit()
        
        # Log de sucesso conforme especificado
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] E-mail enviado para: {email_destino}, {email_interno}")
        return True
        
    except Exception as e:
        # Log de erro conforme especificado
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.error(f"[{timestamp}] Erro ao enviar email: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/checkout', methods=['POST'])
def checkout():
    """Cria preferência de pagamento no Mercado Pago"""
    try:
        # Dados do produto Premium
        preference_data = {
            "items": [
                {
                    "title": "Avaliação de Competências - Versão Premium",
                    "quantity": 1,
                    "unit_price": 29.90,
                    "currency_id": "BRL"
                }
            ],
            "back_urls": {
                "success": request.url_root.rstrip('/') + "/pagamento_sucesso",
                "failure": request.url_root.rstrip('/') + "/pagamento_falha", 
                "pending": request.url_root.rstrip('/') + "/pagamento_pendente"
            },
            "external_reference": f"premium_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Criar preferência
        preference_response = mp.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            preference = preference_response["response"]
            logger.info(f"Preferência criada: {preference['id']}")
            
            return jsonify({
                'success': True,
                'preference_id': preference['id'],
                'init_point': preference['init_point']
            })
        else:
            logger.error(f"Erro ao criar preferência MP: {preference_response}")
            return jsonify({
                'success': False,
                'message': 'Erro ao processar pagamento'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao criar preferência MP: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao processar pagamento'
        }), 500

@app.route('/mp/webhook', methods=['POST'])
def mp_webhook():
    """Webhook para receber notificações do Mercado Pago"""
    try:
        data = request.get_json()
        
        if data and data.get('type') == 'payment':
            payment_id = data['data']['id']
            
            # Buscar informações do pagamento
            payment_info = mp.payment().get(payment_id)
            payment = payment_info["response"]
            
            logger.info(f"Webhook recebido - Payment ID: {payment_id}, Status: {payment.get('status')}")
            
            # Verificar se pagamento foi aprovado
            if payment.get('status') == 'approved':
                # Marcar usuário como premium na sessão
                # Em produção, isso deveria ser salvo em banco de dados
                external_reference = payment.get('external_reference', '')
                session[f'premium_paid_{external_reference}'] = True
                session['premium_user'] = True
                
                logger.info(f"Pagamento aprovado para referência: {external_reference}")
                
                return jsonify({'status': 'success'}), 200
            else:
                logger.warning(f"Pagamento não aprovado - Status: {payment.get('status')}")
                return jsonify({'status': 'payment_not_approved'}), 200
                
        return jsonify({'status': 'ignored'}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook MP: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pagamento_sucesso')
def pagamento_sucesso():
    """Página de sucesso do pagamento"""
    session['premium_user'] = True
    return render_template('pagamento_sucesso.html')

@app.route('/pagamento_falha')
def pagamento_falha():
    """Página de falha do pagamento"""
    return render_template('pagamento_falha.html')

@app.route('/pagamento_pendente')
def pagamento_pendente():
    """Página de pagamento pendente"""
    return render_template('pagamento_pendente.html')

@app.route('/verificar_premium')
def verificar_premium():
    """Verifica se usuário tem acesso premium"""
    is_premium = session.get('premium_user', False)
    return jsonify({'premium': is_premium})

@app.route('/submit_avaliacao', methods=['POST'])
def submit_avaliacao():
    try:
        # Obter dados do formulário
        nome = request.form.get('nome_completo', '').strip()
        email = request.form.get('email', '').strip()
        celular = request.form.get('celular', '').strip()
        tipo_experiencia = request.form.get('tipo_experiencia', 'gratuita').strip()
        
        # Validar dados obrigatórios
        if not nome or not email:
            return jsonify({
                'success': False,
                'message': 'Nome e email são obrigatórios'
            }), 400
        
        # Controle de acesso premium
        if tipo_experiencia == 'premium':
            is_premium = session.get('premium_user', False)
            if not is_premium:
                return jsonify({
                    'success': False,
                    'message': 'Acesso premium necessário. Complete o pagamento primeiro.',
                    'redirect_to_payment': True
                }), 403
        
        # Obter todas as respostas
        respostas = {}
        for key, value in request.form.items():
            if key.startswith('c') and '_q' in key:
                respostas[key] = value
        
        logger.info(f"Processando avaliação para {nome} ({email})")
        logger.info(f"Respostas recebidas: {len(respostas)} itens")
        
        # Calcular competências individuais (50 competências)
        competencias_individuais = calcular_competencias_individuais(respostas)
        ranking_50_competencias = gerar_ranking_50_competencias(competencias_individuais)
        
        # Calcular competências principais (5 grupos)
        medias_principais = calcular_competencias_principais(respostas)
        ranking_principais = gerar_ranking_principais(medias_principais)
        
        # Calcular pontuação geral
        pontuacao_geral = sum(medias_principais.values()) / len(medias_principais)
        
        # Identificar pontos fortes e oportunidades
        pontos_fortes, oportunidades = identificar_pontos_fortes_e_oportunidades(ranking_principais)
        top_subcompetencias, bottom_subcompetencias = identificar_subcompetencias_destaque(ranking_50_competencias)
        
        # Identificar competências a desenvolver (3 piores)
        competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
        
        # Determinar versão baseada na escolha do usuário
        versao = tipo_experiencia if tipo_experiencia in ['gratuita', 'premium'] else 'gratuita'
        
        # Gerar plano de desenvolvimento
        plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver, versao)
        
        # Preparar dados para o template
        data_avaliacao = datetime.now().strftime('%d/%m/%Y')
        
        dados_template = {
            'nome': nome,
            'email': email,
            'celular': celular,
            'data_avaliacao': data_avaliacao,
            'pontuacao_geral': pontuacao_geral,
            'ranking_50_competencias': ranking_50_competencias,
            'medias': ranking_principais,
            'pontos_fortes': pontos_fortes,
            'oportunidades': oportunidades,
            'top_subcompetencias': top_subcompetencias,
            'bottom_subcompetencias': bottom_subcompetencias,
            'competencias_desenvolver': competencias_desenvolver,
            'plano_desenvolvimento': plano_desenvolvimento,
            'versao': versao
        }
        
        # Gerar HTML do relatório
        html_relatorio = render_template('relatorio_template.html', **dados_template)
        
        # Substituir URLs relativos por caminhos absolutos para o PDF
        import re
        base_url = request.url_root
        html_relatorio = re.sub(
            r'src="([^"]*)"',
            lambda m: f'src="{base_url.rstrip("/")}{m.group(1)}"' if m.group(1).startswith('/') else m.group(0),
            html_relatorio
        )
        
        # Gerar PDF e salvar em pasta acessível
        pdf_path = None
        try:
            # Criar nome do arquivo PDF
            nome_arquivo = nome.replace(' ', '_').replace('/', '_').replace('\\', '_')
            pdf_filename = f"relatorio_{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Garantir que o diretório static/reports existe
            reports_dir = os.path.join(app.static_folder, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            pdf_path = os.path.join(reports_dir, pdf_filename)
            
            # Opções para geração do PDF com alta fidelidade
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
                'enable-javascript': '',
                'javascript-delay': '2000',  # Aumentado para garantir carregamento completo
                'images': '',
                'enable-external-links': '',
                'enable-internal-links': '',
                'zoom': '1.0',
                'dpi': '300',
                'image-dpi': '300',
                'image-quality': '100',
                'footer-line': '',
                'quiet': '',
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore',
                'disable-plugins': '',
                'minimum-font-size': '12',
                'background': '',
                'lowquality': False,
                'grayscale': False,
                'orientation': 'Portrait'
            }
            
            # Gerar PDF
            pdfkit.from_string(html_relatorio, pdf_path, options=options)
            
            # Verificar se o arquivo foi criado e tem tamanho válido
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"[{timestamp}] PDF gerado com sucesso: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
                logger.info(f"[{timestamp}] PDF de Diagnóstico formatado conforme HTML — OK")
            else:
                raise Exception("Arquivo PDF não foi criado ou está vazio")
            
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.error(f"[{timestamp}] Erro ao gerar PDF: {e}")
            pdf_path = None
        
        # Tentar enviar email apenas se PDF foi gerado com sucesso
        if pdf_path and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            try:
                envio_sucesso = enviar_email(nome, email, pdf_path, pontuacao_geral)
                if envio_sucesso:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(f"[{timestamp}] Email enviado com sucesso para {email}")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.warning(f"[{timestamp}] Falha no envio de email para {email}")
            except Exception as e:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.error(f"[{timestamp}] Erro ao enviar email: {e}")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.error(f"[{timestamp}] Não foi possível enviar email - PDF não gerado ou inválido")
        
        # Retornar resposta JSON com HTML do relatório
        return jsonify({
            'success': True,
            'message': f'Avaliação processada com sucesso! Pontuação: {pontuacao_geral:.2f}/5.00',
            'html_content': html_relatorio,
            'pontuacao_geral': pontuacao_geral
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar avaliação: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)

