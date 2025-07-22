#!/usr/bin/env python3
import requests
import json

# Dados de teste
dados = {
    'nome_completo': 'Teste Direto POST',
    'email': 'washington.a.dacruz@gmail.com',
    'celular': '(11) 99999-9999',
    'tipo_experiencia': 'gratuita'
}

# Adicionar todas as 50 perguntas
for i in range(1, 51):
    dados[f'pergunta_{i}'] = '4'  # Concordo

print("🧪 TESTE DIRETO VIA POST")
print("=" * 50)

try:
    # Fazer POST direto para o endpoint
    response = requests.post(
        'http://localhost:9003/submit_avaliacao',
        data=dados,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.headers.get('content-type', '').startswith('application/json'):
        print(f"JSON Response: {response.json()}")
    else:
        print(f"Text Response: {response.text[:500]}...")
        
    print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
    
except requests.exceptions.Timeout:
    print("❌ TIMEOUT - Servidor demorou mais de 30s")
except requests.exceptions.ConnectionError:
    print("❌ ERRO DE CONEXÃO - Servidor não está rodando")
except Exception as e:
    print(f"❌ ERRO: {e}")

