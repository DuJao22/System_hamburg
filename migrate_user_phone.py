from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Tornar email nullable
        db.session.execute(text("""
            CREATE TABLE user_new (
                id INTEGER PRIMARY KEY,
                username VARCHAR(80) NOT NULL,
                email VARCHAR(120) UNIQUE,
                password_hash VARCHAR(200),
                cpf VARCHAR(14),
                phone VARCHAR(20) UNIQUE NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                role VARCHAR(20) DEFAULT 'customer',
                created_at DATETIME
            )
        """))
        
        # Copiar dados existentes
        db.session.execute(text("""
            INSERT INTO user_new (id, username, email, password_hash, cpf, phone, is_admin, role, created_at)
            SELECT id, username, email, password_hash, cpf, 
                   CASE WHEN phone IS NULL OR phone = '' THEN '+55' || id ELSE phone END,
                   is_admin, role, created_at
            FROM user
        """))
        
        # Remover tabela antiga e renomear
        db.session.execute(text("DROP TABLE user"))
        db.session.execute(text("ALTER TABLE user_new RENAME TO user"))
        
        db.session.commit()
        print("✅ Migração concluída com sucesso!")
        print("⚠️  Usuários sem telefone receberam um telefone temporário. Peça para atualizarem.")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro na migração: {e}")
        print("Tentando aplicar alterações incrementais...")
        
        try:
            # Tentar adicionar constraint unique ao telefone se não existir
            db.session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_phone ON user(phone)"))
            db.session.commit()
            print("✅ Índice único no telefone criado!")
        except:
            pass
