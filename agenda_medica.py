
from datetime import datetime, timedelta

from conexion import conectar

DURACION_MIN = 30
FORMATO = "%Y-%m-%d %H:%M"


def _parse(texto):
    for fmt in (FORMATO, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _hay_choque(fechas, nueva):
    limite = timedelta(minutes=DURACION_MIN)
    for f in fechas:
        otra = _parse(f)
        if otra is not None and abs(otra - nueva) < limite:
            return otra
    return None


def agendar_cita_con_medico(paciente_id, medico_id, fecha_hora, motivo):
    """Agenda una cita validando paciente, médico, formato de fecha y choques. Devuelve el ID de la cita."""
    try:
        dt = datetime.strptime((fecha_hora or "").strip(), FORMATO)
    except ValueError:
        raise ValueError("Fecha u hora inválida. Use el formato AAAA-MM-DD y HH:MM (ej. 2026-11-05 09:30).")
    if dt < datetime.now() - timedelta(minutes=1):
        raise ValueError("No se puede agendar una cita en una fecha u hora que ya pasó.")
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValueError("Ingrese el motivo de la consulta.")

    conn = conectar()
    try:
        cur = conn.cursor()
        pac = cur.execute("SELECT nombre FROM pacientes WHERE id = ?", (paciente_id,)).fetchone()
        if pac is None:
            raise ValueError(f"No existe ningún paciente con el ID {paciente_id}.")
        med = cur.execute("SELECT nombre, especialidad FROM medicos WHERE id = ?", (medico_id,)).fetchone()
        if med is None:
            raise ValueError("El médico seleccionado no existe.")

        fechas_medico = [r[0] for r in cur.execute(
            "SELECT c.fecha FROM citas c JOIN citas_detalle d ON d.cita_id = c.id "
            "WHERE d.medico_id = ? AND d.estado = 'Programada'", (medico_id,)).fetchall()]
        otra = _hay_choque(fechas_medico, dt)
        if otra:
            raise ValueError(
                f"El médico {med[0]} ya tiene una cita programada el {otra:%Y-%m-%d} a las {otra:%H:%M}. "
                f"Cada cita ocupa {DURACION_MIN} minutos; elija otro horario."
            )

        fechas_paciente = [r[0] for r in cur.execute(
            "SELECT c.fecha FROM citas c LEFT JOIN citas_detalle d ON d.cita_id = c.id "
            "WHERE c.paciente_id = ? AND IFNULL(d.estado, 'Programada') = 'Programada'",
            (paciente_id,)).fetchall()]
        otra = _hay_choque(fechas_paciente, dt)
        if otra:
            raise ValueError(
                f"El paciente {pac[0]} ya tiene una cita el {otra:%Y-%m-%d} a las {otra:%H:%M}."
            )

        cur.execute(
            "INSERT INTO citas (paciente_id, fecha, motivo) VALUES (?, ?, ?)",
            (paciente_id, dt.strftime(FORMATO), motivo),
        )
        cita_id = cur.lastrowid
        cur.execute(
            "INSERT INTO citas_detalle (cita_id, medico_id, especialidad, estado) VALUES (?, ?, ?, 'Programada')",
            (cita_id, medico_id, med[1]),
        )
        conn.commit()
        return cita_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_agenda_detallada():
    """Filas: (cita_id, paciente, médico, especialidad, fecha, motivo, estado)."""
    conn = conectar()
    try:
        return conn.execute(
            "SELECT c.id, p.nombre, IFNULL(m.nombre, 'Sin asignar'), IFNULL(d.especialidad, '—'), "
            "c.fecha, c.motivo, IFNULL(d.estado, 'Programada') "
            "FROM citas c JOIN pacientes p ON p.id = c.paciente_id "
            "LEFT JOIN citas_detalle d ON d.cita_id = c.id "
            "LEFT JOIN medicos m ON m.id = d.medico_id "
            "ORDER BY c.fecha"
        ).fetchall()
    finally:
        conn.close()


def citas_pendientes_paciente(paciente_id):
    """Citas programadas (aún no atendidas) de un paciente: (id, fecha, motivo)."""
    conn = conectar()
    try:
        return conn.execute(
            "SELECT c.id, c.fecha, c.motivo FROM citas c LEFT JOIN citas_detalle d ON d.cita_id = c.id "
            "WHERE c.paciente_id = ? AND IFNULL(d.estado, 'Programada') = 'Programada' ORDER BY c.fecha",
            (paciente_id,),
        ).fetchall()
    finally:
        conn.close()


def estado_cita(cita_id):
    conn = conectar()
    try:
        f = conn.execute(
            "SELECT IFNULL(d.estado, 'Programada') FROM citas c "
            "LEFT JOIN citas_detalle d ON d.cita_id = c.id WHERE c.id = ?", (cita_id,)
        ).fetchone()
    finally:
        conn.close()
    return f[0] if f else None
