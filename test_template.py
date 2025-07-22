#!/usr/bin/env python3
"""
Script de teste para verificar a renderização do template HTML
"""

import os
import sys
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

def testar_template():
    """Testar a renderização do template HTML"""
    print("=== TESTE DO TEMPLATE HTML ===\n")
    
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
        
        # Testar renderização do template
        with app.app_context():
            with app.test_request_context():
                html_relatorio = render_template('relatorio_template.html', **dados_template)
                print(f"✓ Template renderizado com sucesso: {len(html_relatorio)} caracteres")
                
                # Salvar HTML para inspeção
                with open('relatorio_teste.html', 'w', encoding='utf-8') as f:
                    f.write(html_relatorio)
                print("✓ HTML salvo em 'relatorio_teste.html'")
                
                print("\n=== TESTE DO TEMPLATE CONCLUÍDO COM SUCESSO ===")
                return True
            
    except Exception as e:
        print(f"✗ ERRO durante o teste do template: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_template()
    sys.exit(0 if sucesso else 1)

