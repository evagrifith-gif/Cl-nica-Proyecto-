
from datetime import datetime

from conexion import conectar
from pacientes_ext import existe_paciente, codigo_paciente, calcular_edad


def registrar_consulta(paciente_id, medico_id, diagnostico, tratamiento="", receta="",
                       observaciones="", cita_id=None):
    diagnostico = (diagnostico or "").strip()
    if not diagnostico:
        raise ValueError("Ingrese el diagnóstico.")
    conn = conectar()
    try:
        cur = conn.cursor()
        if not existe_paciente(conn, paciente_id):
            raise ValueError("El paciente no existe.")
        if cur.execute("SELECT 1 FROM medicos WHERE id = ?", (medico_id,)).fetchone() is None:
            raise ValueError("Seleccione el médico que atiende la consulta.")

        if cita_id is not None:
            fila = cur.execute(
                "SELECT c.paciente_id, IFNULL(d.estado, 'Programada') FROM citas c "
                "LEFT JOIN citas_detalle d ON d.cita_id = c.id WHERE c.id = ?", (cita_id,)
            ).fetchone()
            if fila is None or fila[0] != paciente_id:
                raise ValueError("La cita seleccionada no corresponde a este paciente.")
            if fila[1] == "Atendida":
                raise ValueError("Esa cita ya fue atendida.")

        cur.execute(
            "INSERT INTO consultas (paciente_id, cita_id, medico_id, fecha, diagnostico, tratamiento, "
            "receta, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (paciente_id, cita_id, medico_id, datetime.now().strftime("%Y-%m-%d %H:%M"), diagnostico,
             (tratamiento or "").strip(), (receta or "").strip(), (observaciones or "").strip()),
        )
        consulta_id = cur.lastrowid

        if cita_id is not None:
            cur.execute("UPDATE citas_detalle SET estado = 'Atendida' WHERE cita_id = ?", (cita_id,))
            if cur.rowcount == 0:  # cita creada con el código original (sin detalle)
                cur.execute(
                    "INSERT INTO citas_detalle (cita_id, medico_id, estado) VALUES (?, ?, 'Atendida')",
                    (cita_id, medico_id),
                )
        conn.commit()
        return consulta_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_consultas(paciente_id):
    """Filas: (id, fecha, médico, diagnóstico)."""
    conn = conectar()
    try:
        return conn.execute(
            "SELECT c.id, c.fecha, IFNULL(m.nombre, '—'), c.diagnostico FROM consultas c "
            "LEFT JOIN medicos m ON m.id = c.medico_id WHERE c.paciente_id = ? "
            "ORDER BY c.fecha DESC, c.id DESC", (paciente_id,)
        ).fetchall()
    finally:
        conn.close()


def obtener_consulta(consulta_id):
    conn = conectar()
    try:
        f = conn.execute(
            "SELECT c.id, c.fecha, c.diagnostico, c.tratamiento, c.receta, c.observaciones, "
            "p.id, p.nombre, d.fecha_nacimiento, IFNULL(m.nombre, '—'), IFNULL(m.especialidad, '—'), "
            "IFNULL(m.colegiado, '—') FROM consultas c JOIN pacientes p ON p.id = c.paciente_id "
            "LEFT JOIN pacientes_datos d ON d.paciente_id = p.id LEFT JOIN medicos m ON m.id = c.medico_id "
            "WHERE c.id = ?", (consulta_id,)
        ).fetchone()
    finally:
        conn.close()
    if f is None:
        return None
    return {
        "id": f[0], "fecha": f[1], "diagnostico": f[2], "tratamiento": f[3] or "",
        "receta": f[4] or "", "observaciones": f[5] or "", "paciente_id": f[6],
        "paciente": f[7], "edad": calcular_edad(f[8]), "medico": f[9],
        "especialidad": f[10], "colegiado": f[11],
    }


def generar_receta_texto(consulta_id):
    c = obtener_consulta(consulta_id)
    if c is None:
        raise ValueError("La consulta no existe.")
    linea = "=" * 60
    edad = f"{c['edad']} años" if c["edad"] != "" else "No registrada"
    partes = [
        linea,
        "CLÍNICA MÉDICA SERENIDAD".center(60),
        "RECETA MÉDICA".center(60),
        linea,
        f"Fecha:        {c['fecha']}",
        f"Paciente:     {c['paciente']} ({codigo_paciente(c['paciente_id'])})",
        f"Edad:         {edad}",
        f"Médico:       {c['medico']}",
        f"Especialidad: {c['especialidad']}   Colegiado: {c['colegiado']}",
        "-" * 60,
        "DIAGNÓSTICO:", c["diagnostico"], "",
        "TRATAMIENTO:", c["tratamiento"] or "—", "",
        "RECETA / INDICACIONES:", c["receta"] or "—", "",
        "OBSERVACIONES:", c["observaciones"] or "—",
        linea,
        "", "", "_" * 30, "Firma y sello del médico",
    ]
    return "\n".join(partes)
