#!/usr/bin/env python3
import sys
import os
import traceback

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar as funções do app
from app import calcular_competencias_individuais, calcular_competencias_principais, gerar_ranking_competencias, identificar_pontos_fortes_oportunidades, identificar_competencias_desenvolver, gerar_plano_desenvolvimento

# Dados de teste
respostas = {}
for i in range(1, 51):
    respostas[f'pergunta_{i}'] = 4

print("🔍 DEBUG DO ERRO")
print("=" * 50)

try:
    print("1. Testando calcular_competencias_individuais...")
    competencias_individuais = calcular_competencias_individuais(respostas)
    print(f"✅ OK - {len(competencias_individuais)} competências calculadas")
    
    print("2. Testando calcular_competencias_principais...")
    competencias_principais = calcular_competencias_principais(competencias_individuais)
    print(f"✅ OK - {len(competencias_principais)} competências principais")
    
    print("3. Testando gerar_ranking_competencias...")
    ranking_principais = gerar_ranking_competencias(competencias_principais)
    print(f"✅ OK - {len(ranking_principais)} itens no ranking")
    
    print("4. Testando identificar_pontos_fortes_oportunidades...")
    pontos_fortes, oportunidades = identificar_pontos_fortes_oportunidades(ranking_principais)
    print(f"✅ OK - {len(pontos_fortes)} pontos fortes, {len(oportunidades)} oportunidades")
    
    print("5. Testando identificar_competencias_desenvolver...")
    competencias_desenvolver = identificar_competencias_desenvolver(ranking_principais)
    print(f"✅ OK - {len(competencias_desenvolver)} competências a desenvolver")
    
    print("6. Testando gerar_plano_desenvolvimento...")
    plano_desenvolvimento = gerar_plano_desenvolvimento(competencias_desenvolver, 'premium')
    print(f"✅ OK - Plano gerado")
    
    print("\n🎉 TODOS OS TESTES PASSARAM!")
    
except Exception as e:
    print(f"\n❌ ERRO ENCONTRADO: {e}")
    print("\nTraceback completo:")
    traceback.print_exc()

