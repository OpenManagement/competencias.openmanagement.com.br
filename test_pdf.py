#!/usr/bin/env python3
"""
Script de teste para verificar a geração de PDF
"""

import os
import sys
import pdfkit
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

def testar_pdf():
    """Testar a geração de PDF"""
    print("=== TESTE DA GERAÇÃO DE PDF ===\n")
    
    try:
        # Criar dados de teste
        respostas = criar_respostas_teste()
        nome = "João Silva"
        email = "joao.silva@teste.com"
        celular = "(11) 99999-9999"
        
        # Calcular todas as métricas
        competencias_individuais = calcular_competencias_individuais(respostas)
        ranking_50_competencias = gerar_ranking_50_competencias(competencias_individuais)
        medias_principais = calcular_competencias_principais(respostas)
        ranking_principais = gerar_ranking_principais(medias_principais)
        pontuacao_geral = sum(medias_principais.values()) / len(medias_principais)
        pontos_fortes, oportunidades = identificar_pontos_fortes_e_oportunidades(ranking_principais)
        top_subcompetencias, bottom_subcompetencias = identificar_subcompetencias_destaque(ranking_50_competencias)
        competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
        plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver, 'premium')
        
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
            'versao': 'premium'
        }
        
        print("✓ Dados do template preparados")
        
        # Renderizar template HTML
        with app.app_context():
            with app.test_request_context():
                html_relatorio = render_template('relatorio_template.html', **dados_template)
                print(f"✓ Template renderizado: {len(html_relatorio)} caracteres")
                
                # Substituir URLs relativos por caminhos absolutos para o PDF
                import re
                base_url = "http://localhost:9000"
                html_relatorio = re.sub(
                    r'src="([^"]*)"',
                    lambda m: f'src="{base_url}{m.group(1)}"' if m.group(1).startswith('/') else m.group(0),
                    html_relatorio
                )
                print("✓ URLs ajustadas para geração de PDF")
                
                # Criar diretório para PDFs de teste
                os.makedirs('test_pdfs', exist_ok=True)
                
                # Nome do arquivo PDF
                pdf_filename = f"relatorio_teste_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join('test_pdfs', pdf_filename)
                
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
                    'javascript-delay': '2000',
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
                
                print("✓ Opções de PDF configuradas")
                
                # Gerar PDF
                pdfkit.from_string(html_relatorio, pdf_path, options=options)
                
                # Verificar se o arquivo foi criado e tem tamanho válido
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    tamanho = os.path.getsize(pdf_path)
                    print(f"✓ PDF gerado com sucesso: {pdf_path} ({tamanho} bytes)")
                    print("\n=== TESTE DE PDF CONCLUÍDO COM SUCESSO ===")
                    return True
                else:
                    print("✗ PDF não foi criado ou está vazio")
                    return False
            
    except Exception as e:
        print(f"✗ ERRO durante o teste de PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_pdf()
    sys.exit(0 if sucesso else 1)

