#!/usr/bin/env python3
import sys
import os
import traceback
from flask import Flask, render_template, request
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar as funções do app
from app import calcular_competencias_individuais, calcular_competencias_principais, gerar_ranking_competencias, identificar_pontos_fortes_oportunidades, identificar_competencias_desenvolver, gerar_plano_desenvolvimento

app = Flask(__name__)

# Dados de teste
respostas = {}
for i in range(1, 51):
    respostas[f'pergunta_{i}'] = 4

print("🔍 DEBUG DO TEMPLATE")
print("=" * 50)

try:
    # Calcular tudo
    competencias_individuais = calcular_competencias_individuais(respostas)
    competencias_principais = calcular_competencias_principais(competencias_individuais)
    pontuacao_geral = sum(comp['pontuacao'] for comp in competencias_principais.values()) / len(competencias_principais)
    ranking_principais = gerar_ranking_competencias(competencias_principais)
    pontos_fortes, oportunidades = identificar_pontos_fortes_oportunidades(ranking_principais)
    competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
    plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver, 'premium')
    
    # Preparar dados para o template
    dados_template = {
        'nome': 'Teste Debug',
        'email': 'teste@debug.com',
        'celular': '(11) 99999-9999',
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
    
    print("✅ Dados preparados com sucesso")
    
    # Testar template original
    print("Testando template original...")
    with app.test_request_context():
        html_original = render_template('relatorio_template.html', **dados_template)
        print(f"✅ Template original OK - {len(html_original)} caracteres")
    
    # Testar template PDF
    print("Testando template PDF...")
    with app.app_context():
        html_pdf = render_template('relatorio_pdf_template.html', **dados_template)
        print(f"✅ Template PDF OK - {len(html_pdf)} caracteres")
    
    print("\n🎉 TODOS OS TEMPLATES FUNCIONAM!")
    
except Exception as e:
    print(f"\n❌ ERRO ENCONTRADO: {e}")
    print("\nTraceback completo:")
    traceback.print_exc()

