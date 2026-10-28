
from datetime import datetime

from conexion import conectar
from pacientes_ext import existe_paciente

TIPOS = [
    "Alergia", "Enfermedad crónica", "Cirugía previa", "Medicamento actual",
    "Antecedente familiar", "Hospitalización", "Vacunas", "Otro",
]


def agregar_antecedente(paciente_id, tipo, descripcion):
    descripcion = (descripcion or "").strip()
    if tipo not in TIPOS:
        raise ValueError("Seleccione un tipo de antecedente válido.")
    if not descripcion:
        raise ValueError("Ingrese la descripción del antecedente.")
    conn = conectar()
    try:
        if not existe_paciente(conn, paciente_id):
            raise ValueError("El paciente no existe.")
        conn.execute(
            "INSERT INTO antecedentes (paciente_id, tipo, descripcion, fecha_registro) VALUES (?, ?, ?, ?)",
            (paciente_id, tipo, descripcion, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
    finally:
        conn.close()


def listar_antecedentes(paciente_id):
    """Filas: (id, tipo, descripcion, fecha_registro)."""
    conn = conectar()
    try:
        return conn.execute(
            "SELECT id, tipo, descripcion, fecha_registro FROM antecedentes "
            "WHERE paciente_id = ? ORDER BY id DESC", (paciente_id,)
        ).fetchall()
    finally:
        conn.close()


def eliminar_antecedente(antecedente_id):
    conn = conectar()
    try:
        conn.execute("DELETE FROM antecedentes WHERE id = ?", (antecedente_id,))
        conn.commit()
    finally:
        conn.close()
