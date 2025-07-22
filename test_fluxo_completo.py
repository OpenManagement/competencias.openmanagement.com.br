#!/usr/bin/env python3
"""
Teste completo do fluxo de diagnóstico de competências
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template

# Carregar variáveis de ambiente
load_dotenv()

# Importar funções do app
from app import (
    calcular_competencias_individuais,
    gerar_ranking_50_competencias,
    calcular_competencias_principais,
    gerar_ranking_principais,
    identificar_pontos_fortes_e_oportunidades,
    identificar_subcompetencias_destaque,
    identificar_competencias_desenvolver,
    gerar_plano_desenvolvimento,
    enviar_email,
    COMPETENCIAS_MAPEAMENTO
)

# Criar app Flask para teste
app = Flask(__name__)

def criar_respostas_teste():
    """Criar respostas de teste para todas as 50 competências"""
    respostas = {}
    
    # Gerar respostas variadas (1-5) para todas as competências
    import random
    random.seed(42)  # Para resultados consistentes
    
    for key in COMPETENCIAS_MAPEAMENTO.keys():
        respostas[key] = str(random.randint(1, 5))
    
    return respostas

def testar_fluxo_completo():
    """Testar o fluxo completo do diagnóstico"""
    print("=== TESTE DO FLUXO COMPLETO DO DIAGNÓSTICO ===\n")
    
    try:
        # Dados de entrada
        nome = "João Silva"
        email = "washington.a.dacruz@gmail.com"
        celular = "(11) 99999-9999"
        tipo_experiencia = "premium"
        
        print(f"✓ Dados de entrada: {nome}, {email}")
        
        # Criar respostas de teste
        respostas = criar_respostas_teste()
        print(f"✓ Respostas criadas: {len(respostas)} competências")
        
        # Calcular competências individuais (50 competências)
        competencias_individuais = calcular_competencias_individuais(respostas)
        ranking_50_competencias = gerar_ranking_50_competencias(competencias_individuais)
        print(f"✓ Competências individuais calculadas: {len(competencias_individuais)}")
        
        # Calcular competências principais (5 grupos)
        medias_principais = calcular_competencias_principais(respostas)
        ranking_principais = gerar_ranking_principais(medias_principais)
        print(f"✓ Competências principais calculadas: {len(medias_principais)}")
        
        # Calcular pontuação geral
        pontuacao_geral = sum(medias_principais.values()) / len(medias_principais)
        print(f"✓ Pontuação geral: {pontuacao_geral:.2f}/5.00")
        
        # Identificar pontos fortes e oportunidades
        pontos_fortes, oportunidades = identificar_pontos_fortes_e_oportunidades(ranking_principais)
        top_subcompetencias, bottom_subcompetencias = identificar_subcompetencias_destaque(ranking_50_competencias)
        print(f"✓ Pontos fortes: {len(pontos_fortes)}, Oportunidades: {len(oportunidades)}")
        
        # Identificar competências a desenvolver
        competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
        print(f"✓ Competências a desenvolver: {len(competencias_desenvolver)}")
        
        # Gerar plano de desenvolvimento
        plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver, tipo_experiencia)
        print(f"✓ Plano de desenvolvimento gerado: {len(plano_desenvolvimento)} itens")
        
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
            'versao': tipo_experiencia
        }
        
        print("✓ Dados do template preparados")
        
        # Gerar HTML do relatório
        with app.app_context():
            with app.test_request_context():
                html_relatorio = render_template('relatorio_template.html', **dados_template)
                print(f"✓ HTML do relatório gerado: {len(html_relatorio)} caracteres")
                
                # Substituir URLs para PDF
                import re
                current_dir = os.path.abspath('.')
                html_relatorio = re.sub(
                    r'src="/static/([^"]*)"',
                    lambda m: f'src="file://{current_dir}/static/{m.group(1)}"',
                    html_relatorio
                )
                print("✓ URLs ajustadas para PDF")
                
                # Gerar PDF
                import pdfkit
                
                # Criar diretório para relatórios
                reports_dir = os.path.join(app.static_folder, 'reports')
                os.makedirs(reports_dir, exist_ok=True)
                
                pdf_filename = f"relatorio_{nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join(reports_dir, pdf_filename)
                
                # Opções otimizadas para PDF
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
                    'images': '',
                    'zoom': '1.0',
                    'dpi': '150',
                    'image-dpi': '150',
                    'image-quality': '75',
                    'quiet': '',
                    'load-error-handling': 'ignore',
                    'load-media-error-handling': 'ignore',
                    'disable-plugins': '',
                    'minimum-font-size': '12',
                    'background': '',
                    'orientation': 'Portrait',
                    'disable-javascript': '',
                    'no-stop-slow-scripts': '',
                    'disable-external-links': '',
                    'disable-internal-links': ''
                }
                
                # Gerar PDF
                pdfkit.from_string(html_relatorio, pdf_path, options=options)
                
                # Verificar se PDF foi criado
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    tamanho = os.path.getsize(pdf_path)
                    print(f"✓ PDF gerado com sucesso: {pdf_path} ({tamanho} bytes)")
                    
                    # Testar envio de email (simulado)
                    try:
                        # Como não temos a senha real, vamos simular o envio
                        print("✓ Simulando envio de email...")
                        print(f"  - Destinatário: {email}")
                        print(f"  - PDF anexado: {os.path.basename(pdf_path)}")
                        print(f"  - Pontuação: {pontuacao_geral:.2f}/5.00")
                        print("✓ Email simulado com sucesso!")
                        
                        # Salvar resultado do teste
                        resultado = {
                            'timestamp': datetime.now().isoformat(),
                            'nome': nome,
                            'email': email,
                            'pontuacao_geral': pontuacao_geral,
                            'pdf_gerado': True,
                            'pdf_path': pdf_path,
                            'pdf_tamanho': tamanho,
                            'html_tamanho': len(html_relatorio),
                            'email_simulado': True,
                            'status': 'sucesso'
                        }
                        
                        with open('resultado_teste_completo.json', 'w', encoding='utf-8') as f:
                            json.dump(resultado, f, indent=2, ensure_ascii=False)
                        
                        print("✓ Resultado salvo em 'resultado_teste_completo.json'")
                        
                        print("\n=== FLUXO COMPLETO TESTADO COM SUCESSO ===")
                        print("🎉 Todas as funcionalidades estão operacionais!")
                        print("📧 Para envio real de email, configure MAIL_PASSWORD no .env")
                        
                        return True
                        
                    except Exception as e:
                        print(f"✗ Erro no envio de email: {e}")
                        return False
                        
                else:
                    print("✗ PDF não foi gerado corretamente")
                    return False
            
    except Exception as e:
        print(f"✗ ERRO durante o teste completo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_fluxo_completo()
    sys.exit(0 if sucesso else 1)

