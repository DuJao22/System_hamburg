import sqlite3

conn = sqlite3.connect('instance/ecommerce.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE 'table' ADD COLUMN access_pin VARCHAR(4);")
    conn.commit()
    print("Coluna access_pin adicionada com sucesso!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Coluna access_pin já existe!")
    else:
        print(f"Erro: {e}")
finally:
    conn.close()
