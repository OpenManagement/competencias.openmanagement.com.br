import sqlite3
import logging
from datetime import datetime
import os

# Configurar logging
logger = logging.getLogger(__name__)

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), 'transactions.db')

def init_database():
    """Inicializa o banco de dados e cria as tabelas necessárias"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Criar tabela de transações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                external_reference TEXT,
                status TEXT NOT NULL,
                amount REAL,
                currency_id TEXT,
                payment_method TEXT,
                payment_type TEXT,
                payer_email TEXT,
                payer_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                webhook_data TEXT
            )
        ''')
        
        # Criar índices para melhor performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_id ON transactions(payment_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_external_reference ON transactions(external_reference)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON transactions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON transactions(created_at)')
        
        conn.commit()
        conn.close()
        
        logger.info("Banco de dados inicializado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        return False

def save_transaction(payment_data, webhook_data=None):
    """Salva ou atualiza uma transação no banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Extrair dados do pagamento
        payment_id = str(payment_data.get('id', ''))
        external_reference = payment_data.get('external_reference', '')
        status = payment_data.get('status', '')
        amount = float(payment_data.get('transaction_amount', 0))
        currency_id = payment_data.get('currency_id', '')
        
        # Dados do método de pagamento
        payment_method = ''
        payment_type = ''
        if 'payment_method_id' in payment_data:
            payment_method = payment_data.get('payment_method_id', '')
        if 'payment_type_id' in payment_data:
            payment_type = payment_data.get('payment_type_id', '')
        
        # Dados do pagador
        payer_email = ''
        payer_name = ''
        if 'payer' in payment_data:
            payer = payment_data['payer']
            payer_email = payer.get('email', '')
            if 'first_name' in payer and 'last_name' in payer:
                payer_name = f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip()
        
        # Converter webhook_data para string JSON se fornecido
        webhook_data_str = str(webhook_data) if webhook_data else None
        
        # Verificar se a transação já existe
        cursor.execute('SELECT id FROM transactions WHERE payment_id = ?', (payment_id,))
        existing = cursor.fetchone()
        
        current_time = datetime.now().isoformat()
        
        if existing:
            # Atualizar transação existente
            cursor.execute('''
                UPDATE transactions 
                SET status = ?, amount = ?, currency_id = ?, payment_method = ?, 
                    payment_type = ?, payer_email = ?, payer_name = ?, 
                    updated_at = ?, webhook_data = ?
                WHERE payment_id = ?
            ''', (status, amount, currency_id, payment_method, payment_type, 
                  payer_email, payer_name, current_time, webhook_data_str, payment_id))
            
            logger.info(f"Transação atualizada: {payment_id} - Status: {status}")
        else:
            # Inserir nova transação
            cursor.execute('''
                INSERT INTO transactions 
                (payment_id, external_reference, status, amount, currency_id, 
                 payment_method, payment_type, payer_email, payer_name, 
                 created_at, updated_at, webhook_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (payment_id, external_reference, status, amount, currency_id,
                  payment_method, payment_type, payer_email, payer_name,
                  current_time, current_time, webhook_data_str))
            
            logger.info(f"Nova transação salva: {payment_id} - Status: {status}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Erro ao salvar transação: {e}")
        return False

def get_transaction_by_payment_id(payment_id):
    """Busca uma transação pelo payment_id"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM transactions WHERE payment_id = ?', (payment_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            # Converter tupla em dicionário
            columns = ['id', 'payment_id', 'external_reference', 'status', 'amount', 
                      'currency_id', 'payment_method', 'payment_type', 'payer_email', 
                      'payer_name', 'created_at', 'updated_at', 'webhook_data']
            return dict(zip(columns, row))
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao buscar transação: {e}")
        return None

def get_transactions_by_status(status, limit=100):
    """Busca transações por status"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE status = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (status, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Converter tuplas em dicionários
        columns = ['id', 'payment_id', 'external_reference', 'status', 'amount', 
                  'currency_id', 'payment_method', 'payment_type', 'payer_email', 
                  'payer_name', 'created_at', 'updated_at', 'webhook_data']
        
        return [dict(zip(columns, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"Erro ao buscar transações por status: {e}")
        return []

def get_all_transactions(limit=100, offset=0):
    """Busca todas as transações com paginação"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transactions 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Converter tuplas em dicionários
        columns = ['id', 'payment_id', 'external_reference', 'status', 'amount', 
                  'currency_id', 'payment_method', 'payment_type', 'payer_email', 
                  'payer_name', 'created_at', 'updated_at', 'webhook_data']
        
        return [dict(zip(columns, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"Erro ao buscar todas as transações: {e}")
        return []

def get_transaction_stats():
    """Retorna estatísticas das transações"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Contar transações por status
        cursor.execute('''
            SELECT status, COUNT(*) as count, SUM(amount) as total_amount
            FROM transactions 
            GROUP BY status
        ''')
        
        stats_by_status = {}
        for row in cursor.fetchall():
            status, count, total_amount = row
            stats_by_status[status] = {
                'count': count,
                'total_amount': total_amount or 0
            }
        
        # Total geral
        cursor.execute('SELECT COUNT(*) as total_count, SUM(amount) as total_amount FROM transactions')
        total_row = cursor.fetchone()
        total_count, total_amount = total_row
        
        conn.close()
        
        return {
            'total_transactions': total_count,
            'total_amount': total_amount or 0,
            'by_status': stats_by_status
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return {
            'total_transactions': 0,
            'total_amount': 0,
            'by_status': {}
        }

