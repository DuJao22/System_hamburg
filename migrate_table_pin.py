from app import db, create_app
from app.models import Table
import secrets

def migrate():
    app = create_app()
    with app.app_context():
        tables = Table.query.all()
        
        for table in tables:
            if not table.access_pin:
                table.access_pin = ''.join([str(secrets.randbelow(10)) for _ in range(4)])
                print(f"Mesa {table.table_number}: PIN gerado = {table.access_pin}")
        
        db.session.commit()
        print("\nMigração concluída! PINs gerados para todas as mesas.")

if __name__ == '__main__':
    migrate()
