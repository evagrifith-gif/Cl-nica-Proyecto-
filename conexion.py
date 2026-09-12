import sqlite3

def conectar():
    return sqlite3.connect("clinica.db")

# Alias por si alguna otra parte del código aún usa 'obtener_conexion'
obtener_conexion = conectar

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            historial TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            fecha TEXT NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    crear_tablas()