#!/usr/bin/env python3
"""
Script de teste para verificar o funcionamento do diagnóstico de competências
"""

import os
import sys
from dotenv import load_dotenv

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

def criar_respostas_teste():
    """Criar respostas de teste para todas as 50 competências"""
    respostas = {}
    
    # Gerar respostas variadas (1-5) para todas as competências
    import random
    random.seed(42)  # Para resultados consistentes
    
    for key in COMPETENCIAS_MAPEAMENTO.keys():
        respostas[key] = str(random.randint(1, 5))
    
    return respostas

def testar_diagnostico():
    """Testar todas as funções do diagnóstico"""
    print("=== TESTE DO DIAGNÓSTICO DE COMPETÊNCIAS ===\n")
    
    # Criar respostas de teste
    respostas = criar_respostas_teste()
    print(f"✓ Respostas de teste criadas: {len(respostas)} itens")
    
    try:
        # Testar cálculo de competências individuais
        competencias_individuais = calcular_competencias_individuais(respostas)
        print(f"✓ Competências individuais calculadas: {len(competencias_individuais)} itens")
        
        # Testar ranking das 50 competências
        ranking_50 = gerar_ranking_50_competencias(competencias_individuais)
        print(f"✓ Ranking 50 competências gerado: {len(ranking_50)} itens")
        
        # Testar cálculo de competências principais
        medias_principais = calcular_competencias_principais(respostas)
        print(f"✓ Competências principais calculadas: {len(medias_principais)} itens")
        
        # Testar ranking principais
        ranking_principais = gerar_ranking_principais(medias_principais)
        print(f"✓ Ranking principais gerado: {len(ranking_principais)} itens")
        
        # Testar identificação de pontos fortes e oportunidades
        pontos_fortes, oportunidades = identificar_pontos_fortes_e_oportunidades(ranking_principais)
        print(f"✓ Pontos fortes identificados: {len(pontos_fortes)} itens")
        print(f"✓ Oportunidades identificadas: {len(oportunidades)} itens")
        
        # Testar subcompetências destaque
        top_sub, bottom_sub = identificar_subcompetencias_destaque(ranking_50)
        print(f"✓ Top subcompetências: {len(top_sub)} itens")
        print(f"✓ Bottom subcompetências: {len(bottom_sub)} itens")
        
        # Testar competências a desenvolver
        competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
        print(f"✓ Competências a desenvolver: {len(competencias_desenvolver)} itens")
        
        # Testar plano de desenvolvimento
        plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver, 'premium')
        print(f"✓ Plano de desenvolvimento gerado: {len(plano_desenvolvimento)} itens")
        
        # Calcular pontuação geral
        pontuacao_geral = sum(medias_principais.values()) / len(medias_principais)
        print(f"✓ Pontuação geral: {pontuacao_geral:.2f}/5.00")
        
        print("\n=== TESTE CONCLUÍDO COM SUCESSO ===")
        print("Todas as funções do diagnóstico estão funcionando corretamente!")
        
        return True
        
    except Exception as e:
        print(f"✗ ERRO durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_diagnostico()
    sys.exit(0 if sucesso else 1)

