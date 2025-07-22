#!/usr/bin/env python3
from flask import Flask, render_template
import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Dados de teste simples
dados_teste = {
    'nome': 'Teste Simples',
    'email': 'teste@teste.com',
    'celular': '(11) 99999-9999',
    'pontuacao_geral': 4.5,
    'competencias_principais': {
        'comunicacao': {'pontuacao': 4.5, 'nivel': 'Alto'},
        'organizacao': {'pontuacao': 4.0, 'nivel': 'Alto'},
        'proatividade': {'pontuacao': 3.5, 'nivel': 'Médio'},
        'pensamento_critico': {'pontuacao': 4.2, 'nivel': 'Alto'},
        'produtividade': {'pontuacao': 3.8, 'nivel': 'Alto'}
    },
    'ranking_principais': [
        {'competencia': 'Comunicação', 'pontuacao': 4.5, 'nivel': 'Alto'},
        {'competencia': 'Pensamento Crítico', 'pontuacao': 4.2, 'nivel': 'Alto'},
        {'competencia': 'Organização', 'pontuacao': 4.0, 'nivel': 'Alto'},
        {'competencia': 'Produtividade', 'pontuacao': 3.8, 'nivel': 'Alto'},
        {'competencia': 'Proatividade', 'pontuacao': 3.5, 'nivel': 'Médio'}
    ],
    'pontos_fortes': ['Comunicação', 'Pensamento Crítico'],
    'oportunidades': ['Proatividade'],
    'competencias_desenvolver': ['Proatividade'],
    'plano_desenvolvimento': {
        'acoes': ['Desenvolver iniciativa própria', 'Buscar novas oportunidades'],
        'recursos': ['Cursos online', 'Mentoria'],
        'prazo': '3 meses'
    },
    'data_avaliacao': '22/07/2025',
    'hora_avaliacao': '19:15'
}

print("🧪 TESTE SIMPLES DO TEMPLATE")
print("=" * 50)

try:
    with app.app_context():
        html = render_template('relatorio_template.html', **dados_teste)
        print(f"✅ Template renderizado com sucesso!")
        print(f"Tamanho do HTML: {len(html)} caracteres")
        print(f"Primeiros 200 caracteres: {html[:200]}...")
        
except Exception as e:
    print(f"❌ ERRO ao renderizar template: {e}")
    import traceback
    traceback.print_exc()

