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

def listar_pacientes(filtro=""):
    conn = conectar()
    cursor = conn.cursor()
    if filtro:
        cursor.execute("SELECT * FROM pacientes WHERE nombre LIKE ?", (f"%{filtro}%",))
    else:
        cursor.execute("SELECT * FROM pacientes")
    pacientes = cursor.fetchall()
    conn.close()
    return pacientes

def eliminar_paciente(paciente_id):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM citas WHERE paciente_id = ?", (paciente_id,))
        cursor.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        raise e