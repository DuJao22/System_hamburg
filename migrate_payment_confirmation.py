#!/usr/bin/env python3
"""
Script de migração para adicionar colunas de confirmação de pagamento
"""
import sqlite3
import os

db_path = 'instance/ecommerce.db'

def migrate():
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Iniciando migração do banco de dados...")
    
    # Verificar se as colunas já existem
    cursor.execute("PRAGMA table_info('order')")
    columns = [column[1] for column in cursor.fetchall()]
    
    migrations_applied = 0
    
    # Adicionar payment_confirmed_by se não existir
    if 'payment_confirmed_by' not in columns:
        try:
            cursor.execute("""
                ALTER TABLE "order" 
                ADD COLUMN payment_confirmed_by INTEGER
            """)
            print("✅ Coluna 'payment_confirmed_by' adicionada")
            migrations_applied += 1
        except sqlite3.OperationalError as e:
            print(f"⚠️ Erro ao adicionar 'payment_confirmed_by': {e}")
    else:
        print("ℹ️ Coluna 'payment_confirmed_by' já existe")
    
    # Adicionar payment_confirmed_at se não existir
    if 'payment_confirmed_at' not in columns:
        try:
            cursor.execute("""
                ALTER TABLE "order" 
                ADD COLUMN payment_confirmed_at DATETIME
            """)
            print("✅ Coluna 'payment_confirmed_at' adicionada")
            migrations_applied += 1
        except sqlite3.OperationalError as e:
            print(f"⚠️ Erro ao adicionar 'payment_confirmed_at': {e}")
    else:
        print("ℹ️ Coluna 'payment_confirmed_at' já existe")
    
    # Adicionar payment_confirmation_notes se não existir
    if 'payment_confirmation_notes' not in columns:
        try:
            cursor.execute("""
                ALTER TABLE "order" 
                ADD COLUMN payment_confirmation_notes TEXT
            """)
            print("✅ Coluna 'payment_confirmation_notes' adicionada")
            migrations_applied += 1
        except sqlite3.OperationalError as e:
            print(f"⚠️ Erro ao adicionar 'payment_confirmation_notes': {e}")
    else:
        print("ℹ️ Coluna 'payment_confirmation_notes' já existe")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Migração concluída! {migrations_applied} coluna(s) adicionada(s)")
    return True

if __name__ == '__main__':
    migrate()
