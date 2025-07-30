#!/usr/bin/env python3
"""
Script de teste para o webhook do Mercado Pago e integração com banco de dados
"""

import sys
import os
import json
from datetime import datetime

# Adicionar o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(__file__))

from database import init_database, save_transaction, get_transaction_by_payment_id, get_transaction_stats

def test_database_initialization():
    """Testa a inicialização do banco de dados"""
    print("🔧 Testando inicialização do banco de dados...")
    
    success = init_database()
    if success:
        print("✅ Banco de dados inicializado com sucesso")
        return True
    else:
        print("❌ Erro na inicialização do banco de dados")
        return False

def test_save_transaction():
    """Testa o salvamento de uma transação"""
    print("\n💾 Testando salvamento de transação...")
    
    # Dados simulados de uma transação do Mercado Pago
    payment_data = {
        "id": "12345678901",
        "external_reference": "premium_20250730_143000",
        "status": "approved",
        "transaction_amount": 29.90,
        "currency_id": "BRL",
        "payment_method_id": "visa",
        "payment_type_id": "credit_card",
        "payer": {
            "email": "teste@exemplo.com",
            "first_name": "João",
            "last_name": "Silva"
        }
    }
    
    webhook_data = {
        "type": "payment",
        "data": {
            "id": "12345678901"
        }
    }
    
    success = save_transaction(payment_data, webhook_data)
    if success:
        print("✅ Transação salva com sucesso")
        return True
    else:
        print("❌ Erro ao salvar transação")
        return False

def test_retrieve_transaction():
    """Testa a recuperação de uma transação"""
    print("\n🔍 Testando recuperação de transação...")
    
    payment_id = "12345678901"
    transaction = get_transaction_by_payment_id(payment_id)
    
    if transaction:
        print("✅ Transação recuperada com sucesso:")
        print(f"   Payment ID: {transaction['payment_id']}")
        print(f"   Status: {transaction['status']}")
        print(f"   Valor: R$ {transaction['amount']}")
        print(f"   Email: {transaction['payer_email']}")
        print(f"   Nome: {transaction['payer_name']}")
        return True
    else:
        print("❌ Transação não encontrada")
        return False

def test_update_transaction():
    """Testa a atualização de uma transação existente"""
    print("\n🔄 Testando atualização de transação...")
    
    # Dados atualizados (mesmo payment_id, status diferente)
    payment_data = {
        "id": "12345678901",
        "external_reference": "premium_20250730_143000",
        "status": "refunded",  # Status alterado
        "transaction_amount": 29.90,
        "currency_id": "BRL",
        "payment_method_id": "visa",
        "payment_type_id": "credit_card",
        "payer": {
            "email": "teste@exemplo.com",
            "first_name": "João",
            "last_name": "Silva"
        }
    }
    
    success = save_transaction(payment_data)
    if success:
        print("✅ Transação atualizada com sucesso")
        
        # Verificar se foi realmente atualizada
        transaction = get_transaction_by_payment_id("12345678901")
        if transaction and transaction['status'] == 'refunded':
            print("✅ Status atualizado corretamente para 'refunded'")
            return True
        else:
            print("❌ Status não foi atualizado corretamente")
            return False
    else:
        print("❌ Erro ao atualizar transação")
        return False

def test_multiple_transactions():
    """Testa o salvamento de múltiplas transações"""
    print("\n📊 Testando múltiplas transações...")
    
    transactions_data = [
        {
            "id": "11111111111",
            "external_reference": "premium_20250730_140000",
            "status": "approved",
            "transaction_amount": 29.90,
            "currency_id": "BRL",
            "payment_method_id": "pix",
            "payment_type_id": "bank_transfer",
            "payer": {
                "email": "maria@exemplo.com",
                "first_name": "Maria",
                "last_name": "Santos"
            }
        },
        {
            "id": "22222222222",
            "external_reference": "premium_20250730_141000",
            "status": "pending",
            "transaction_amount": 29.90,
            "currency_id": "BRL",
            "payment_method_id": "bolbradesco",
            "payment_type_id": "ticket",
            "payer": {
                "email": "pedro@exemplo.com",
                "first_name": "Pedro",
                "last_name": "Oliveira"
            }
        },
        {
            "id": "33333333333",
            "external_reference": "premium_20250730_142000",
            "status": "rejected",
            "transaction_amount": 29.90,
            "currency_id": "BRL",
            "payment_method_id": "master",
            "payment_type_id": "credit_card",
            "payer": {
                "email": "ana@exemplo.com",
                "first_name": "Ana",
                "last_name": "Costa"
            }
        }
    ]
    
    success_count = 0
    for payment_data in transactions_data:
        if save_transaction(payment_data):
            success_count += 1
    
    if success_count == len(transactions_data):
        print(f"✅ Todas as {len(transactions_data)} transações foram salvas com sucesso")
        return True
    else:
        print(f"⚠️ Apenas {success_count} de {len(transactions_data)} transações foram salvas")
        return False

def test_statistics():
    """Testa as estatísticas das transações"""
    print("\n📈 Testando estatísticas...")
    
    stats = get_transaction_stats()
    
    if stats:
        print("✅ Estatísticas recuperadas com sucesso:")
        print(f"   Total de transações: {stats['total_transactions']}")
        print(f"   Valor total: R$ {stats['total_amount']:.2f}")
        print("   Por status:")
        for status, data in stats['by_status'].items():
            print(f"     {status}: {data['count']} transações, R$ {data['total_amount']:.2f}")
        return True
    else:
        print("❌ Erro ao recuperar estatísticas")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do webhook e banco de dados\n")
    
    tests = [
        ("Inicialização do BD", test_database_initialization),
        ("Salvamento de transação", test_save_transaction),
        ("Recuperação de transação", test_retrieve_transaction),
        ("Atualização de transação", test_update_transaction),
        ("Múltiplas transações", test_multiple_transactions),
        ("Estatísticas", test_statistics)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Teste '{test_name}' falhou")
        except Exception as e:
            print(f"❌ Teste '{test_name}' falhou com erro: {e}")
    
    print(f"\n📋 Resumo dos testes:")
    print(f"   Aprovados: {passed}/{total}")
    print(f"   Taxa de sucesso: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 Todos os testes passaram! A integração está funcionando corretamente.")
        return True
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")
        return False

if __name__ == "__main__":
    main()

