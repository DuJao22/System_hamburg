"""
Script de migração para adicionar suporte a pedidos em mesa com notificações em tempo real
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🔄 Iniciando migração do banco de dados...")
    
    try:
        # Adicionar novos campos à tabela Order
        print("📝 Adicionando novos campos à tabela Order...")
        with db.engine.connect() as conn:
            # Campos para sessão de mesa e origem do pedido
            try:
                conn.execute(text("ALTER TABLE 'order' ADD COLUMN table_session_id INTEGER"))
                print("✅ Coluna table_session_id adicionada")
            except Exception as e:
                print(f"⚠️  table_session_id já existe ou erro: {e}")
            
            try:
                conn.execute(text("ALTER TABLE 'order' ADD COLUMN origin VARCHAR(20) DEFAULT 'delivery'"))
                print("✅ Coluna origin adicionada")
            except Exception as e:
                print(f"⚠️  origin já existe ou erro: {e}")
            
            # Timestamps de status da cozinha
            try:
                conn.execute(text("ALTER TABLE 'order' ADD COLUMN received_at DATETIME"))
                print("✅ Coluna received_at adicionada")
            except Exception as e:
                print(f"⚠️  received_at já existe ou erro: {e}")
            
            try:
                conn.execute(text("ALTER TABLE 'order' ADD COLUMN preparing_at DATETIME"))
                print("✅ Coluna preparing_at adicionada")
            except Exception as e:
                print(f"⚠️  preparing_at já existe ou erro: {e}")
            
            try:
                conn.execute(text("ALTER TABLE 'order' ADD COLUMN kitchen_ready_at DATETIME"))
                print("✅ Coluna kitchen_ready_at adicionada")
            except Exception as e:
                print(f"⚠️  kitchen_ready_at já existe ou erro: {e}")
            
            conn.commit()
        
        # Adicionar campos de status aos OrderItems
        print("\n📝 Adicionando campos de status à tabela OrderItem...")
        with db.engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE order_item ADD COLUMN status VARCHAR(50) DEFAULT 'Pendente'"))
                print("✅ Coluna status adicionada")
            except Exception as e:
                print(f"⚠️  status já existe ou erro: {e}")
            
            try:
                conn.execute(text("ALTER TABLE order_item ADD COLUMN received_at DATETIME"))
                print("✅ Coluna received_at adicionada")
            except Exception as e:
                print(f"⚠️  received_at já existe ou erro: {e}")
            
            try:
                conn.execute(text("ALTER TABLE order_item ADD COLUMN preparing_at DATETIME"))
                print("✅ Coluna preparing_at adicionada")
            except Exception as e:
                print(f"⚠️  preparing_at já existe ou erro: {e}")
            
            try:
                conn.execute(text("ALTER TABLE order_item ADD COLUMN ready_at DATETIME"))
                print("✅ Coluna ready_at adicionada")
            except Exception as e:
                print(f"⚠️  ready_at já existe ou erro: {e}")
            
            try:
                conn.execute(text("ALTER TABLE order_item ADD COLUMN delivered_at DATETIME"))
                print("✅ Coluna delivered_at adicionada")
            except Exception as e:
                print(f"⚠️  delivered_at já existe ou erro: {e}")
            
            conn.commit()
        
        # Criar tabelas novas
        print("\n📝 Criando novas tabelas...")
        db.create_all()
        print("✅ Tabelas TableSession e KitchenNotification criadas")
        
        print("\n✅ Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
        raise
