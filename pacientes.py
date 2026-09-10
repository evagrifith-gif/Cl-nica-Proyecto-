from conexion import conectar

def registrar_paciente(nombre, telefono, historial):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pacientes (nombre, telefono, historial) VALUES (?, ?, ?)",
            (nombre, telefono, historial)
        )
        conn.commit()
        conn.close()
        print("\n Paciente registrado con éxito.")
    except Exception as e:
        print(f"\n Error de conexión o registro: {e}")

def listar_pacientes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pacientes")
    pacientes = cursor.fetchall()
    conn.close()
    return pacientes