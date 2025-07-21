import os
import platform
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, render_template, request, jsonify, url_for
import pdfkit
import logging

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do wkhtmltopdf baseada no sistema operacional
def get_wkhtmltopdf_config():
    """Detecta o sistema operacional e configura o wkhtmltopdf adequadamente"""
    system = platform.system().lower()
    
    if system == 'windows':
        # Caminhos comuns do wkhtmltopdf no Windows
        possible_paths = [
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'wkhtmltopdf.exe'  # Se estiver no PATH
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return pdfkit.configuration(wkhtmltopdf=path)
        
        # Se não encontrar, retorna None (usará configuração padrão)
        logger.warning("wkhtmltopdf não encontrado. Instale de: https://wkhtmltopdf.org/downloads.html")
        return None
        
    elif system == 'linux':
        # Configuração para Linux
        linux_paths = ['/usr/bin/wkhtmltopdf', '/usr/local/bin/wkhtmltopdf']
        for path in linux_paths:
            if os.path.exists(path):
                return pdfkit.configuration(wkhtmltopdf=path)
        return None
        
    elif system == 'darwin':  # macOS
        mac_paths = ['/usr/local/bin/wkhtmltopdf', '/opt/homebrew/bin/wkhtmltopdf']
        for path in mac_paths:
            if os.path.exists(path):
                return pdfkit.configuration(wkhtmltopdf=path)
        return None
    
    return None

# Configurar wkhtmltopdf
config = get_wkhtmltopdf_config()

# Configurações de email - CONFIGURAÇÃO DIRETA PARA FUNCIONAMENTO IMEDIATO
# Para usar suas próprias credenciais, altere os valores abaixo:

# Configurações padrão para Zoho Mail
DEFAULT_EMAIL_HOST = 'smtp.zoho.com'
DEFAULT_EMAIL_PORT = 587
DEFAULT_EMAIL_USER = 'consultoria@openmanagement.com.br'  # ALTERE AQUI para seu e-mail
DEFAULT_EMAIL_PASS = 'sua_senha_de_app_aqui'  # ALTERE AQUI para sua senha de app do Zoho

# Opção 2: Gmail (Alternativa)
# DEFAULT_EMAIL_HOST = 'smtp.gmail.com'
# DEFAULT_EMAIL_PORT = 587
# DEFAULT_EMAIL_USER = 'seu_email@gmail.com'
# DEFAULT_EMAIL_PASS = 'sua_senha_de_app'

# Opção 3: Outlook/Hotmail
# DEFAULT_EMAIL_HOST = 'smtp-mail.outlook.com'
# DEFAULT_EMAIL_PORT = 587
# DEFAULT_EMAIL_USER = 'seu_email@outlook.com'
# DEFAULT_EMAIL_PASS = 'sua_senha'

# IMPORTANTE: Para Zoho Mail, você precisa:
# 1. Ativar autenticação de 2 fatores na conta Zoho
# 2. Gerar uma senha de app específica para SMTP
# 3. Usar essa senha de app no campo DEFAULT_EMAIL_PASS (não a senha normal)

# Configuração final (variáveis de ambiente sobrescrevem as configurações padrão)
EMAIL_HOST = os.getenv('EMAIL_HOST', DEFAULT_EMAIL_HOST)
EMAIL_PORT = int(os.getenv('EMAIL_PORT', str(DEFAULT_EMAIL_PORT)))
EMAIL_USER = os.getenv('EMAIL_USER', DEFAULT_EMAIL_USER)
EMAIL_PASS = os.getenv('EMAIL_PASS', DEFAULT_EMAIL_PASS)

# Verificar se e-mail está configurado
EMAIL_ENABLED = bool(EMAIL_PASS and EMAIL_USER and EMAIL_PASS != 'sua_senha_de_app_aqui')

print(f"🔧 Configuração de E-mail:")
print(f"   Host: {EMAIL_HOST}")
print(f"   Porta: {EMAIL_PORT}")
print(f"   Usuário: {EMAIL_USER}")
print(f"   Senha configurada: {'✅ Sim' if EMAIL_PASS and EMAIL_PASS != 'sua_senha_de_app_aqui' else '❌ Não'}")
print(f"   E-mail habilitado: {'✅ Sim' if EMAIL_ENABLED else '❌ Não'}")
if not EMAIL_ENABLED:
    print("   ⚠️  Para habilitar e-mail, configure EMAIL_USER e EMAIL_PASS no código ou via variáveis de ambiente")

def calcular_competencias(respostas):
    """Calcula as médias das competências baseado nas respostas da escala Likert"""
    competencias = {
        'comunicacao': [],
        'organizacao': [],
        'proatividade': [],
        'pensamento_critico': [],
        'produtividade': []
    }
    
    # Mapear respostas para competências
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

def gerar_ranking(medias):
    """Gera ranking das competências"""
    competencias_info = [
        {'nome': 'Comunicação', 'emoji': '🟠', 'media': medias['comunicacao']},
        {'nome': 'Organização', 'emoji': '🟡', 'media': medias['organizacao']},
        {'nome': 'Proatividade', 'emoji': '🔵', 'media': medias['proatividade']},
        {'nome': 'Pensamento Crítico', 'emoji': '🟣', 'media': medias['pensamento_critico']},
        {'nome': 'Produtividade', 'emoji': '🟢', 'media': medias['produtividade']}
    ]
    
    # Ordenar por média (decrescente)
    competencias_ordenadas = sorted(competencias_info, key=lambda x: x['media'], reverse=True)
    
    return {
        'mais_fortes': competencias_ordenadas[:3],
        'mais_fracas': competencias_ordenadas[-3:][::-1]  # Inverter para mostrar da menor para maior
    }

def gerar_plano_desenvolvimento(medias, ranking):
    """Gera plano de desenvolvimento personalizado baseado nas competências mais fracas"""
    
    # Base de ações por competência e nível (baseado no documento anexado)
    acoes_desenvolvimento = {
        'comunicacao': {
            'grau_1': [
                {
                    'acao': 'Praticar Escuta Ativa diariamente',
                    'o_que_e': 'Trata-se de ouvir com total atenção, sem interromper a pessoa que está falando, e depois resumir o que foi dito para confirmar que você entendeu corretamente.',
                    'por_que': 'Esta prática cria conexões genuínas com as pessoas e evita mal-entendidos que podem prejudicar relacionamentos pessoais e profissionais. Quando as pessoas se sentem realmente ouvidas, a confiança aumenta.',
                    'como': 'Passo a passo: 1) Escolha uma conversa por dia para praticar; 2) Durante essa conversa, foque 100% na pessoa (guarde o celular); 3) Não interrompa, apenas faça perguntas para entender melhor; 4) Ao final, diga "Deixa eu ver se entendi..." e resuma o que a pessoa disse; 5) Pergunte se seu resumo está correto.',
                    'meta': 'Realizar 60 conversas com escuta ativa completa (aproximadamente 2 por semana durante 3 meses)'
                },
                {
                    'acao': 'Fazer Perguntas Poderosas',
                    'o_que_e': 'São questões abertas (que não podem ser respondidas com sim/não) formuladas para estimular reflexão profunda e revelar informações importantes que normalmente ficariam ocultas.',
                    'por_que': 'Perguntas poderosas ampliam sua perspectiva e a dos outros, evitando que você faça suposições incorretas. Elas transformam conversas superficiais em diálogos significativos e reveladores.',
                    'como': 'Passo a passo: 1) Substitua afirmações por perguntas que começam com "como" ou "o quê"; 2) Em vez de "Isso não vai funcionar", pergunte "Como podemos fazer isso funcionar?"; 3) Em vez de "Você está errado", pergunte "O que te faz pensar assim?"; 4) Anote as reações e insights gerados por essas perguntas.',
                    'meta': 'Fazer pelo menos 3 perguntas poderosas por dia, totalizando mais de 270 perguntas transformadoras em 90 dias'
                }
            ],
            'grau_2': [
                {
                    'acao': 'Mapear Estilos de Comunicação',
                    'o_que_e': 'É o processo de identificar e categorizar como diferentes pessoas preferem receber e transmitir informações, reconhecendo padrões como direto, analítico, amigável ou expressivo.',
                    'por_que': 'Adaptar sua abordagem comunicativa a diferentes perfis aumenta drasticamente sua eficácia. O que funciona com uma pessoa pode alienar completamente outra. Este mapeamento permite personalizar sua comunicação.',
                    'como': 'Passo a passo: 1) Observe como as pessoas respondem a diferentes tipos de mensagens; 2) Classifique-as em: Direto (prefere brevidade e fatos), Analítico (prefere detalhes e lógica), Amigável (valoriza conexão pessoal), Expressivo (aprecia entusiasmo e visão geral); 3) Adapte sua comunicação ao estilo preferido de cada pessoa; 4) Mantenha um registro das suas observações e ajustes.',
                    'meta': 'Mapear completamente os estilos de comunicação de pelo menos 10 pessoas importantes em sua vida pessoal e profissional'
                }
            ],
            'grau_3': [
                {
                    'acao': 'Criar Ritual de Comunicação Semanal',
                    'o_que_e': 'É um momento fixo e recorrente dedicado exclusivamente para alinhar expectativas, compartilhar informações importantes e fortalecer conexões com pessoas-chave em sua vida pessoal ou profissional.',
                    'por_que': 'Previne conflitos causados por falta de comunicação e mantém conexões fortes mesmo em períodos ocupados. Rituais criam previsibilidade e segurança nos relacionamentos.',
                    'como': 'Passo a passo: 1) Escolha um dia e horário fixo semanal (ex: domingo às 19h ou sexta às 16h); 2) Reserve 30 minutos ininterruptos; 3) Estruture o encontro em: a) Revisão da semana passada, b) Celebração de conquistas, c) Discussão de desafios, d) Alinhamento para próxima semana; 4) Mantenha o compromisso mesmo quando parecer desnecessário.',
                    'meta': 'Realizar 13 rituais semanais consecutivos (um ciclo completo de 3 meses) sem falhas'
                }
            ]
        },
        'organizacao': {
            'grau_1': [
                {
                    'acao': 'Criar Sistema de Captura',
                    'o_que_e': 'É um método único e confiável para registrar todos os seus compromissos, ideias, tarefas e informações importantes assim que surgem, evitando que fiquem apenas na sua memória.',
                    'por_que': 'Libera sua mente da carga cognitiva de tentar lembrar de tudo, reduzindo estresse e esquecimentos. Um sistema externo confiável permite que seu cérebro foque em pensar e criar, não em armazenar informações.',
                    'como': 'Passo a passo: 1) Escolha uma ferramenta que esteja sempre com você (aplicativo no celular como Evernote/Google Keep ou um caderno pequeno); 2) Desenvolva o hábito de registrar IMEDIATAMENTE qualquer compromisso, ideia ou tarefa que surgir; 3) Estabeleça um horário diário fixo (5-10 minutos) para revisar e organizar o que foi capturado; 4) Transfira os itens para os sistemas apropriados (calendário, lista de tarefas, etc.).',
                    'meta': 'Capturar 100% dos compromissos e tarefas em seu sistema externo por 90 dias consecutivos'
                },
                {
                    'acao': 'Implementar Regra dos 2 Minutos',
                    'o_que_e': 'É um princípio simples: se uma tarefa pode ser concluída em 2 minutos ou menos, faça-a imediatamente em vez de adiá-la ou registrá-la para depois.',
                    'por_que': 'Evita o acúmulo de pequenas pendências que, juntas, criam uma sensação de sobrecarga. Tarefas pequenas adiadas frequentemente consomem mais energia mental do que realizá-las de imediato.',
                    'como': 'Passo a passo: 1) Quando uma nova tarefa surgir, pergunte-se: "Posso fazer isso em 2 minutos ou menos?"; 2) Se sim, faça imediatamente, sem exceções; 3) Exemplos: responder um email simples, guardar um item fora do lugar, fazer uma ligação rápida; 4) Mantenha um contador diário de quantas vezes você aplicou a regra.',
                    'meta': 'Atingir 80% de aderência à regra dos 2 minutos (medido através de auto-monitoramento diário) durante os 90 dias'
                }
            ],
            'grau_2': [
                {
                    'acao': 'Implementar Revisão Semanal',
                    'o_que_e': 'É uma prática estruturada de dedicar 1 hora por semana para organizar a próxima semana, revisar pendências e ajustar seus sistemas e projetos.',
                    'por_que': 'Mantém seu sistema de organização confiável e atualizado, evitando que tarefas importantes caiam no esquecimento. A revisão semanal proporciona clareza mental e sensação de controle sobre sua vida.',
                    'como': 'Passo a passo: 1) Escolha um momento fixo semanal (muitos preferem sexta à tarde ou domingo à noite); 2) Siga uma checklist: a) Revisar conquistas da semana, b) Processar caixa de entrada e anotações, c) Atualizar listas de tarefas, d) Revisar calendário das próximas semanas, e) Atualizar status de projetos, f) Definir prioridades para a próxima semana; 3) Documente insights e ajustes necessários.',
                    'meta': 'Completar 13 revisões semanais completas (um ciclo de 3 meses) sem pular nenhuma semana'
                }
            ],
            'grau_3': [
                {
                    'acao': 'Criar Sistema de Projetos',
                    'o_que_e': 'É um método estruturado para planejar e executar iniciativas complexas que envolvem múltiplas etapas, transformando ideias abstratas em resultados concretos através de planejamento detalhado.',
                    'por_que': 'Transforma ideias e objetivos ambiciosos em resultados concretos através de passos gerenciáveis. Um sistema de projetos evita que iniciativas importantes fiquem estagnadas por parecerem muito complexas.',
                    'como': 'Passo a passo: 1) Crie um template com os seguintes elementos: a) Objetivo claro e mensurável, b) Lista de etapas sequenciais, c) Recursos necessários, d) Prazos para cada etapa, e) Critérios de sucesso; 2) Aplique este template a 3 projetos importantes; 3) Divida cada projeto em tarefas de no máximo 1-2 horas; 4) Estabeleça revisões semanais de progresso; 5) Documente aprendizados durante a execução.',
                    'meta': 'Concluir com sucesso 3 projetos significativos utilizando o sistema criado, com resultados mensuráveis'
                }
            ]
        },
        'proatividade': {
            'grau_1': [
                {
                    'acao': 'Implementar Regra 5/25',
                    'o_que_e': 'É uma prática de gerenciamento de tempo que consiste em chegar 5 minutos antes e terminar 25 minutos antes do prazo em todos os compromissos e entregas.',
                    'por_que': 'Elimina atrasos crônicos e cria uma margem de segurança para imprevistos, reduzindo significativamente o estresse. Ser consistentemente pontual constrói uma reputação de confiabilidade.',
                    'como': 'Passo a passo: 1) Configure todos os seus alarmes e lembretes 5 minutos antes do horário real; 2) Ao planejar quanto tempo uma tarefa levará, adicione 25% de tempo extra; 3) Ao agendar compromissos no calendário, bloqueie 25 minutos após o horário previsto de término; 4) Mantenha um registro de pontualidade para monitorar seu progresso; 5) Utilize o tempo extra quando tudo corre bem para revisar, preparar a próxima atividade ou simplesmente respirar.',
                    'meta': 'Aplicar a regra 5/25 em pelo menos 90% de todos os seus compromissos durante os 3 meses'
                }
            ],
            'grau_2': [
                {
                    'acao': 'Criar Gatilho Se-Então',
                    'o_que_e': 'São planos de ação automáticos pré-definidos para situações específicas, eliminando a necessidade de tomar decisões no momento e garantindo respostas consistentes.',
                    'por_que': 'Remove a hesitação e garante que você responda de forma adequada mesmo em situações desafiadoras ou inesperadas.',
                    'como': 'Passo a passo: 1) Identifique situações recorrentes onde você hesita ou reage mal; 2) Crie planos "Se X acontecer, então eu farei Y"; 3) Exemplos: "Se alguém me criticar, então eu vou respirar fundo e perguntar por detalhes específicos"; 4) Pratique mentalmente esses cenários; 5) Revise e ajuste os gatilhos baseado nos resultados.',
                    'meta': 'Criar e implementar 10 gatilhos Se-Então para situações importantes da sua vida'
                }
            ],
            'grau_3': [
                {
                    'acao': 'Desenvolver Visão Antecipada',
                    'o_que_e': 'É a capacidade de identificar tendências, oportunidades e problemas potenciais antes que se manifestem completamente, permitindo preparação e ação preventiva.',
                    'por_que': 'Permite que você se posicione estrategicamente, evite crises e aproveite oportunidades antes dos outros.',
                    'como': 'Passo a passo: 1) Dedique 30 minutos semanais para analisar tendências em sua área; 2) Identifique 3 cenários futuros possíveis para projetos importantes; 3) Crie planos de contingência para riscos identificados; 4) Monitore indicadores-chave que sinalizam mudanças; 5) Documente suas previsões e avalie a precisão.',
                    'meta': 'Antecipar e se preparar para 5 situações futuras importantes, demonstrando visão estratégica'
                }
            ]
        },
        'pensamento_critico': {
            'grau_1': [
                {
                    'acao': 'Questionar Padrões Automáticos',
                    'o_que_e': 'É o hábito consciente de pausar e examinar seus pensamentos, reações e suposições automáticas antes de agir ou formar conclusões.',
                    'por_que': 'Evita decisões impulsivas e baseadas em vieses, melhorando a qualidade do seu raciocínio e resultados.',
                    'como': 'Passo a passo: 1) Identifique momentos onde você reage automaticamente; 2) Implemente uma pausa de 10 segundos antes de responder; 3) Pergunte-se: "Por que penso assim?", "Que evidências tenho?", "Que outras perspectivas existem?"; 4) Documente situações onde o questionamento mudou sua perspectiva.',
                    'meta': 'Questionar e revisar pelo menos 30 reações automáticas durante os 90 dias'
                }
            ],
            'grau_2': [
                {
                    'acao': 'Buscar Evidências e Dados',
                    'o_que_e': 'É a prática sistemática de procurar informações concretas e verificáveis antes de aceitar afirmações ou tomar decisões importantes.',
                    'por_que': 'Melhora a qualidade das decisões e reduz erros baseados em suposições ou informações incorretas.',
                    'como': 'Passo a passo: 1) Para cada decisão importante, liste 3 fontes de informação necessárias; 2) Procure dados quantitativos quando possível; 3) Verifique a credibilidade das fontes; 4) Compare informações de múltiplas perspectivas; 5) Documente as evidências encontradas.',
                    'meta': 'Basear 100% das decisões importantes em evidências verificáveis durante os 3 meses'
                }
            ],
            'grau_3': [
                {
                    'acao': 'Considerar Múltiplas Perspectivas',
                    'o_que_e': 'É a habilidade de examinar situações e problemas através de diferentes pontos de vista, incluindo perspectivas que podem contradizer sua visão inicial.',
                    'por_que': 'Amplia sua compreensão, reduz pontos cegos e leva a soluções mais robustas e criativas.',
                    'como': 'Passo a passo: 1) Para cada decisão importante, identifique pelo menos 3 stakeholders afetados; 2) Imagine como cada um veria a situação; 3) Procure ativamente opiniões contrárias à sua; 4) Use técnicas como "advogado do diabo"; 5) Sintetize insights de diferentes perspectivas.',
                    'meta': 'Aplicar análise multi-perspectiva em 10 decisões importantes e documentar insights obtidos'
                }
            ]
        },
        'produtividade': {
            'grau_1': [
                {
                    'acao': 'Concentrar-se em Uma Tarefa',
                    'o_que_e': 'É a prática de dedicar atenção completa a uma única atividade por vez, evitando multitarefas e distrações.',
                    'por_que': 'Aumenta a qualidade do trabalho, reduz erros e melhora a eficiência, já que o cérebro funciona melhor com foco único.',
                    'como': 'Passo a passo: 1) Escolha uma tarefa importante; 2) Elimine todas as distrações (celular, notificações, etc.); 3) Defina um tempo específico para a tarefa; 4) Trabalhe apenas nela até completar ou até o tempo acabar; 5) Faça uma pausa antes da próxima tarefa.',
                    'meta': 'Praticar foco único em pelo menos 2 horas de trabalho por dia durante 90 dias'
                },
                {
                    'acao': 'Utilizar Técnica Pomodoro',
                    'o_que_e': 'É um método de gerenciamento de tempo que divide o trabalho em intervalos de 25 minutos (pomodoros) seguidos de pausas curtas.',
                    'por_que': 'Mantém a concentração, previne fadiga mental e torna tarefas grandes mais gerenciáveis.',
                    'como': 'Passo a passo: 1) Escolha uma tarefa; 2) Configure timer para 25 minutos; 3) Trabalhe com foco total até o timer tocar; 4) Faça pausa de 5 minutos; 5) Após 4 pomodoros, faça pausa longa de 15-30 minutos.',
                    'meta': 'Completar pelo menos 6 pomodoros por dia de trabalho durante os 90 dias'
                }
            ],
            'grau_2': [
                {
                    'acao': 'Priorizar Tarefas de Alto Impacto',
                    'o_que_e': 'É a habilidade de identificar e focar nas atividades que geram os maiores resultados em relação ao tempo e energia investidos.',
                    'por_que': 'Maximiza o retorno do seu esforço e garante que você trabalhe no que realmente importa para seus objetivos.',
                    'como': 'Passo a passo: 1) Liste todas as suas tarefas; 2) Avalie cada uma em termos de impacto (alto/médio/baixo); 3) Identifique as 20% de tarefas que geram 80% dos resultados; 4) Dedique pelo menos 60% do seu tempo a essas tarefas de alto impacto; 5) Elimine ou delegue tarefas de baixo impacto.',
                    'meta': 'Aumentar tempo dedicado a atividades de alto impacto para 70% da agenda de trabalho'
                }
            ],
            'grau_3': [
                {
                    'acao': 'Otimizar Processos Continuamente',
                    'o_que_e': 'É a prática sistemática de analisar, melhorar e automatizar processos recorrentes para aumentar eficiência e qualidade.',
                    'por_que': 'Libera tempo para atividades mais estratégicas e reduz erros em tarefas repetitivas.',
                    'como': 'Passo a passo: 1) Identifique 5 processos que você executa regularmente; 2) Documente cada passo atual; 3) Identifique gargalos e desperdícios; 4) Implemente melhorias (automação, eliminação de passos, etc.); 5) Meça resultados e continue otimizando.',
                    'meta': 'Otimizar 5 processos importantes, reduzindo tempo de execução em pelo menos 30%'
                }
            ]
        }
    }
    
    plano = []
    competencias_foco = ranking['mais_fracas'][:3]  # Focar nas 3 mais fracas
    
    for comp_info in competencias_foco:
        comp_nome = comp_info['nome'].lower().replace(' ', '_').replace('ê', 'e').replace('í', 'i')
        if comp_nome == 'pensamento_critico':
            comp_nome = 'pensamento_critico'
        elif comp_nome == 'comunicacao':
            comp_nome = 'comunicacao'
        elif comp_nome == 'organizacao':
            comp_nome = 'organizacao'
        elif comp_nome == 'proatividade':
            comp_nome = 'proatividade'
        elif comp_nome == 'produtividade':
            comp_nome = 'produtividade'
        
        media = comp_info['media']
        
        # Determinar grau baseado na média da escala Likert (1-5)
        if media <= 1:
            grau = 'grau_1'
        elif media <= 2:
            grau = 'grau_2'
        else:
            grau = 'grau_3'
        
        if comp_nome in acoes_desenvolvimento and grau in acoes_desenvolvimento[comp_nome]:
            acoes = acoes_desenvolvimento[comp_nome][grau]
            
            plano.append({
                'competencia': comp_info['nome'],
                'emoji': comp_info['emoji'],
                'media': media,
                'acoes': acoes
            })
    
    return plano

def gerar_introducao_plano(medias, ranking):
    """Gera introdução personalizada para o plano de desenvolvimento"""
    pontuacao_geral = sum(medias.values()) / len(medias)
    mais_forte = ranking['mais_fortes'][0]['nome']
    mais_fraca = ranking['mais_fracas'][0]['nome']
    
    if pontuacao_geral >= 4.0:
        intro = f"Parabéns! Você demonstra um excelente nível de desenvolvimento nas competências avaliadas. Sua maior força está em {mais_forte}, que pode servir como base para alavancar outras áreas. "
    elif pontuacao_geral >= 3.0:
        intro = f"Você está no caminho certo! Possui uma base sólida, especialmente em {mais_forte}. "
    else:
        intro = f"Este é um momento excelente para começar sua jornada de desenvolvimento! Você tem grande potencial de crescimento. "
    
    intro += f"O plano a seguir foca nas competências com maior oportunidade de impacto: priorizamos {mais_fraca} como área principal de desenvolvimento, pois melhorias aqui terão efeito multiplicador em outras áreas da sua vida."
    
    return intro

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_avaliacao', methods=['POST'])
def submit_avaliacao():
    try:
        data = request.get_json()
        nome_completo = data.get('nome_completo', '')
        email = data.get('email', '')
        celular = data.get('celular', '')
        respostas = data.get('respostas', {})
        
        if not nome_completo or not email or not celular or not respostas:
            return jsonify({'error': 'Dados incompletos'}), 400
        
        # Calcular competências
        medias = calcular_competencias(respostas)
        pontuacao_geral = sum(medias.values()) / len(medias)
        
        # Gerar ranking
        ranking = gerar_ranking(medias)
        
        # Gerar plano de desenvolvimento
        plano_desenvolvimento = gerar_plano_desenvolvimento(medias, ranking)
        
        # Gerar introdução personalizada
        introducao_plano = gerar_introducao_plano(medias, ranking)
        
        # Preparar dados para o template
        todas_competencias = [
            {'nome': 'Comunicação', 'emoji': '🟠', 'media': medias['comunicacao']},
            {'nome': 'Organização', 'emoji': '🟡', 'media': medias['organizacao']},
            {'nome': 'Proatividade', 'emoji': '🔵', 'media': medias['proatividade']},
            {'nome': 'Pensamento Crítico', 'emoji': '🟣', 'media': medias['pensamento_critico']},
            {'nome': 'Produtividade', 'emoji': '🟢', 'media': medias['produtividade']}
        ]
        
        # Gerar relatório HTML
        logo_path = url_for('static', filename='img/logo.png', _external=True)
        
        html_content = render_template('relatorio_template.html',
            nome_completo=nome_completo,
            email=email,
            celular=celular,
            data_avaliacao=datetime.datetime.now().strftime('%d/%m/%Y'),
            pontuacao_geral=round(pontuacao_geral, 2),
            todas_competencias=todas_competencias,
            ranking=ranking,
            plano_desenvolvimento=plano_desenvolvimento,
            introducao_plano=introducao_plano,
            logo_path=logo_path
        )
        
        # Tentar gerar PDF se wkhtmltopdf estiver disponível
        pdf_path = None
        try:
            if config is not None:
                # Gerar PDF
                options = {
                    'page-size': 'A4',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': "UTF-8",
                    'no-outline': None,
                    'enable-local-file-access': None
                }
                
                # Criar diretório temporário se não existir
                temp_dir = os.path.join(os.getcwd(), 'relatorios_temp')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Nome do arquivo PDF
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                pdf_filename = f'relatorio_competencias_{timestamp}.pdf'
                pdf_path = os.path.join(temp_dir, pdf_filename)
                
                # Gerar PDF
                pdfkit.from_string(html_content, pdf_path, options=options, configuration=config)
                logger.info(f"PDF gerado com sucesso: {pdf_path}")
            else:
                logger.warning("wkhtmltopdf não disponível. PDF não será gerado.")
                
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {str(e)}")
            pdf_path = None
        
        # Enviar por email (se PDF foi gerado e email estiver configurado)
        print(f"🔍 Verificando envio de e-mail:")
        print(f"   PDF gerado: {'✅ Sim' if pdf_path and os.path.exists(pdf_path) else '❌ Não'}")
        print(f"   E-mail habilitado: {'✅ Sim' if EMAIL_ENABLED else '❌ Não'}")
        
        if pdf_path and os.path.exists(pdf_path) and EMAIL_ENABLED:
            print(f"📧 Tentando enviar e-mail...")
            try:
                enviar_email(nome_completo, email, pdf_path, pontuacao_geral)
                # Limpar arquivo temporário após envio
                os.remove(pdf_path)
                mensagem = f'Relatório gerado e enviado para {email}!'
                print(f"✅ E-mail enviado com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao enviar email: {str(e)}")
                mensagem = f'Relatório gerado com sucesso! (Email não enviado - erro: {str(e)})'
                print(f"❌ Erro ao enviar e-mail: {str(e)}")
        elif pdf_path and os.path.exists(pdf_path):
            print(f"⚠️  E-mail não configurado - PDF gerado mas não enviado")
            mensagem = f'Relatório gerado com sucesso! (Email não configurado - configure EMAIL_USER e EMAIL_PASS)'
        else:
            print(f"⚠️  PDF não foi gerado")
            mensagem = f'Avaliação processada com sucesso! Pontuação: {round(pontuacao_geral, 2)}/5.00'
        
        return jsonify({
            'message': mensagem,
            'pontuacao_geral': round(pontuacao_geral, 2),
            'html_content': html_content  # Retornar HTML para visualização
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar avaliação: {str(e)}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

def enviar_email(nome, email_destino, pdf_path, pontuacao_geral):
    """Envia o relatório por email com logs detalhados"""
    print(f"📧 Iniciando envio de e-mail...")
    print(f"   Destinatário: {email_destino}")
    print(f"   PDF: {pdf_path}")
    print(f"   Configuração: {EMAIL_HOST}:{EMAIL_PORT}")
    
    try:
        # Verificar se arquivo PDF existe
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")
        
        print(f"   ✅ PDF encontrado: {os.path.getsize(pdf_path)} bytes")
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = email_destino
        msg['Subject'] = f'Seu Relatório de Autoavaliação de Competências - Nota: {pontuacao_geral:.2f}/5.00'
        
        print(f"   ✅ Mensagem criada")
        
        # Corpo do email
        corpo = f"""
Olá {nome}!

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
consultoria@openmanagement.com.br
        """
        
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
        print(f"   ✅ Corpo do e-mail anexado")
        
        # Anexar PDF
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= relatorio_competencias_{nome.replace(" ", "_")}.pdf'
        )
        msg.attach(part)
        print(f"   ✅ PDF anexado ao e-mail")
        
        # Conectar ao servidor SMTP
        print(f"   🔗 Conectando ao servidor SMTP...")
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        print(f"   ✅ Conectado ao {EMAIL_HOST}:{EMAIL_PORT}")
        
        # Iniciar TLS
        print(f"   🔐 Iniciando TLS...")
        server.starttls()
        print(f"   ✅ TLS iniciado")
        
        # Fazer login
        print(f"   🔑 Fazendo login como {EMAIL_USER}...")
        server.login(EMAIL_USER, EMAIL_PASS)
        print(f"   ✅ Login realizado com sucesso")
        
        # Enviar email
        print(f"   📤 Enviando e-mail...")
        text = msg.as_string()
        server.sendmail(EMAIL_USER, email_destino, text)
        print(f"   ✅ E-mail enviado com sucesso!")
        
        # Fechar conexão
        server.quit()
        print(f"   ✅ Conexão fechada")
        
        logger.info(f"Email enviado com sucesso para {email_destino}")
        print(f"📧 ✅ SUCESSO: E-mail enviado para {email_destino}")
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Erro de autenticação SMTP: {str(e)}"
        print(f"   ❌ {error_msg}")
        print(f"   💡 Para Zoho Mail:")
        print(f"      1. Acesse: https://accounts.zoho.com/home#security/app-passwords")
        print(f"      2. Gere uma senha de app para 'Mail'")
        print(f"      3. Use essa senha no campo EMAIL_PASS")
        print(f"      4. Certifique-se que 2FA está ativado na conta")
        print(f"   💡 Para Gmail, use senha de app (não a senha normal)")
        logger.error(error_msg)
        raise Exception(error_msg)
        
    except smtplib.SMTPConnectError as e:
        error_msg = f"Erro de conexão SMTP: {str(e)}"
        print(f"   ❌ {error_msg}")
        print(f"   💡 Verifique sua conexão com a internet")
        print(f"   💡 Verifique se o host {EMAIL_HOST} e porta {EMAIL_PORT} estão corretos")
        logger.error(error_msg)
        raise Exception(error_msg)
        
    except Exception as e:
        error_msg = f"Erro ao enviar email: {str(e)}"
        print(f"   ❌ {error_msg}")
        logger.error(error_msg)
        raise Exception(error_msg)
        
if __name__ == '__main__':
    # Verificar se wkhtmltopdf está disponível
    if config is None:
        print("\n" + "="*60)
        print("⚠️  AVISO: wkhtmltopdf não encontrado!")
        print("📄 O site funcionará, mas PDFs não serão gerados.")
        print("💡 Para gerar PDFs, instale wkhtmltopdf:")
        print("   Windows: https://wkhtmltopdf.org/downloads.html")
        print("   Linux: sudo apt install wkhtmltopdf")
        print("   macOS: brew install wkhtmltopdf")
        print("="*60 + "\n")
    else:
        print("✅ wkhtmltopdf configurado com sucesso!")
    
    print("🚀 Iniciando servidor Flask...")
    print("🌐 Acesse: http://localhost:5000")
    # Configuração para produção
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

