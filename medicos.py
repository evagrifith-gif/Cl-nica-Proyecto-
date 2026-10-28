
import sqlite3

from conexion import conectar

ESPECIALIDADES = [
    "Medicina General", "Pediatría", "Ginecología y Obstetricia", "Medicina Interna",
    "Cardiología", "Dermatología", "Traumatología", "Oftalmología", "Odontología", "Psicología",
]


def registrar_medico(nombre, especialidad, colegiado="", telefono=""):
    nombre = (nombre or "").strip()
    especialidad = (especialidad or "").strip()
    if not nombre:
        raise ValueError("Ingrese el nombre del médico.")
    if not especialidad:
        raise ValueError("Seleccione la especialidad del médico.")
    colegiado = (colegiado or "").strip() or None
    conn = conectar()
    try:
        cur = conn.execute(
            "INSERT INTO medicos (nombre, especialidad, colegiado, telefono) VALUES (?, ?, ?, ?)",
            (nombre, especialidad, colegiado, (telefono or "").strip()),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Ya existe un médico con ese número de colegiado.")
    finally:
        conn.close()


def listar_medicos(especialidad=None):
    """Filas: (id, nombre, especialidad, colegiado, telefono)."""
    conn = conectar()
    try:
        sql = "SELECT id, nombre, especialidad, IFNULL(colegiado, ''), IFNULL(telefono, '') FROM medicos"
        if especialidad and especialidad != "Todas":
            return conn.execute(sql + " WHERE especialidad = ? ORDER BY nombre", (especialidad,)).fetchall()
        return conn.execute(sql + " ORDER BY nombre").fetchall()
    finally:
        conn.close()


def eliminar_medico(medico_id):
    conn = conectar()
    try:
        pendientes = conn.execute(
            "SELECT COUNT(*) FROM citas_detalle WHERE medico_id = ? AND estado = 'Programada'",
            (medico_id,),
        ).fetchone()[0]
        if pendientes:
            raise ValueError(
                f"El médico tiene {pendientes} cita(s) programada(s). Cancélelas o reasígnelas antes de eliminarlo."
            )
        conn.execute("UPDATE citas_detalle SET medico_id = NULL WHERE medico_id = ?", (medico_id,))
        conn.execute("UPDATE consultas SET medico_id = NULL WHERE medico_id = ?", (medico_id,))
        conn.execute("DELETE FROM medicos WHERE id = ?", (medico_id,))
        conn.commit()
    finally:
        conn.close()
