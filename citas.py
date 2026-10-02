from conexion import conectar

def agendar_cita(paciente_id, fecha, motivo):
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT nombre FROM pacientes WHERE id = ?", (paciente_id,))
        paciente = cursor.fetchone()
        
        if paciente is None:
            conn.close()
            raise ValueError(f"No existe ningún paciente registrado con el ID {paciente_id}.")

        cursor.execute(
            "INSERT INTO citas (paciente_id, fecha, motivo) VALUES (?, ?, ?)",
            (paciente_id, fecha, motivo)
        )
        conn.commit()
        conn.close()
        print(f"\n Cita agendada con éxito para el paciente {paciente[0]}.")
    except Exception as e:
        raise e

def eliminar_cita(cita_id):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM citas WHERE id = ?", (cita_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        raise e

def listar_citas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT citas.id, pacientes.nombre, citas.fecha, citas.motivo
        FROM citas
        INNER JOIN pacientes ON citas.paciente_id = pacientes.id
    """)
    citas = cursor.fetchall()
    conn.close()
    return citas