"""
pacientes_ext.py
----------------
Extiende el módulo original pacientes.py SIN modificarlo:
datos completos (DPI, fecha de nacimiento, edad, dirección, contacto de
emergencia) y búsqueda por nombre, DPI o código.
Los datos adicionales viven en la tabla pacientes_datos.
"""
import re
import sqlite3
from datetime import date, datetime

from conexion import conectar


def codigo_paciente(paciente_id):
    return f"PAC-{int(paciente_id):04d}"


def calcular_edad(fecha_nacimiento):
    """Edad en años a partir de 'AAAA-MM-DD'. Devuelve '' si no hay fecha válida."""
    if not fecha_nacimiento:
        return ""
    try:
        nac = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
    except ValueError:
        return ""
    hoy = date.today()
    return hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))


def existe_paciente(conn, paciente_id):
    return conn.execute("SELECT 1 FROM pacientes WHERE id = ?", (paciente_id,)).fetchone() is not None


def _limpiar(nombre, telefono, historial, dpi, fecha_nac, direccion, contacto, tel_contacto):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("Ingrese el nombre del paciente.")

    dpi = re.sub(r"[\s-]", "", dpi or "")
    if dpi and not re.fullmatch(r"\d{13}", dpi):
        raise ValueError("El DPI debe tener exactamente 13 dígitos numéricos.")

    fecha_nac = (fecha_nac or "").strip()
    if fecha_nac:
        try:
            f = datetime.strptime(fecha_nac, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("La fecha de nacimiento debe tener el formato AAAA-MM-DD (ej. 1998-04-25).")
        if f > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        if f.year < 1900:
            raise ValueError("La fecha de nacimiento no es válida.")

    return {
        "nombre": nombre,
        "telefono": (telefono or "").strip(),
        "historial": (historial or "").strip(),
        "dpi": dpi or None,
        "fecha_nac": fecha_nac or None,
        "direccion": (direccion or "").strip() or None,
        "contacto": (contacto or "").strip() or None,
        "tel_contacto": (tel_contacto or "").strip() or None,
    }


def _dpi_duplicado(cur, dpi, excluir_id=None):
    if not dpi:
        return False
    if excluir_id is None:
        fila = cur.execute("SELECT paciente_id FROM pacientes_datos WHERE dpi = ?", (dpi,)).fetchone()
    else:
        fila = cur.execute(
            "SELECT paciente_id FROM pacientes_datos WHERE dpi = ? AND paciente_id <> ?", (dpi, excluir_id)
        ).fetchone()
    return fila is not None


def registrar_paciente_completo(nombre, telefono, historial, dpi, fecha_nac,
                                direccion, contacto, tel_contacto):
    """Registra al paciente con todos sus datos. Devuelve el ID asignado."""
    d = _limpiar(nombre, telefono, historial, dpi, fecha_nac, direccion, contacto, tel_contacto)
    conn = conectar()
    try:
        cur = conn.cursor()
        if _dpi_duplicado(cur, d["dpi"]):
            raise ValueError("Ya existe un paciente registrado con ese DPI.")
        cur.execute(
            "INSERT INTO pacientes (nombre, telefono, historial) VALUES (?, ?, ?)",
            (d["nombre"], d["telefono"], d["historial"]),
        )
        pid = cur.lastrowid
        cur.execute(
            "INSERT INTO pacientes_datos (paciente_id, dpi, fecha_nacimiento, direccion, "
            "contacto_emergencia, telefono_emergencia) VALUES (?, ?, ?, ?, ?, ?)",
            (pid, d["dpi"], d["fecha_nac"], d["direccion"], d["contacto"], d["tel_contacto"]),
        )
        conn.commit()
        return pid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def actualizar_paciente_completo(paciente_id, nombre, telefono, historial, dpi, fecha_nac,
                                 direccion, contacto, tel_contacto):
    d = _limpiar(nombre, telefono, historial, dpi, fecha_nac, direccion, contacto, tel_contacto)
    conn = conectar()
    try:
        cur = conn.cursor()
        if not existe_paciente(conn, paciente_id):
            raise ValueError("El paciente seleccionado ya no existe.")
        if _dpi_duplicado(cur, d["dpi"], excluir_id=paciente_id):
            raise ValueError("Otro paciente ya tiene registrado ese DPI.")
        cur.execute(
            "UPDATE pacientes SET nombre = ?, telefono = ?, historial = ? WHERE id = ?",
            (d["nombre"], d["telefono"], d["historial"], paciente_id),
        )
        existe = cur.execute("SELECT 1 FROM pacientes_datos WHERE paciente_id = ?", (paciente_id,)).fetchone()
        if existe:
            cur.execute(
                "UPDATE pacientes_datos SET dpi = ?, fecha_nacimiento = ?, direccion = ?, "
                "contacto_emergencia = ?, telefono_emergencia = ? WHERE paciente_id = ?",
                (d["dpi"], d["fecha_nac"], d["direccion"], d["contacto"], d["tel_contacto"], paciente_id),
            )
        else:
            cur.execute(
                "INSERT INTO pacientes_datos (paciente_id, dpi, fecha_nacimiento, direccion, "
                "contacto_emergencia, telefono_emergencia) VALUES (?, ?, ?, ?, ?, ?)",
                (paciente_id, d["dpi"], d["fecha_nac"], d["direccion"], d["contacto"], d["tel_contacto"]),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def obtener_paciente(paciente_id):
    """Devuelve un diccionario con todos los datos del paciente o None."""
    conn = conectar()
    try:
        f = conn.execute(
            "SELECT p.id, p.nombre, p.telefono, p.historial, d.dpi, d.fecha_nacimiento, "
            "d.direccion, d.contacto_emergencia, d.telefono_emergencia "
            "FROM pacientes p LEFT JOIN pacientes_datos d ON d.paciente_id = p.id WHERE p.id = ?",
            (paciente_id,),
        ).fetchone()
    finally:
        conn.close()
    if f is None:
        return None
    v = ["" if x is None else x for x in f]
    return {
        "id": v[0], "codigo": codigo_paciente(v[0]), "nombre": v[1], "telefono": v[2],
        "historial": v[3], "dpi": v[4], "fecha_nac": v[5], "direccion": v[6],
        "contacto": v[7], "tel_contacto": v[8], "edad": calcular_edad(v[5]),
    }


def buscar_pacientes(termino=""):
    """
    Busca por nombre, DPI, código (PAC-0001) o ID exacto.
    Devuelve filas: (id, codigo, nombre, dpi, fecha_nac, edad, telefono)
    """
    termino = (termino or "").strip()
    like = f"%{termino}%"
    conn = conectar()
    try:
        filas = conn.execute(
            "SELECT p.id, p.nombre, p.telefono, d.dpi, d.fecha_nacimiento "
            "FROM pacientes p LEFT JOIN pacientes_datos d ON d.paciente_id = p.id "
            "WHERE ? = '' OR p.nombre LIKE ? OR IFNULL(d.dpi, '') LIKE ? "
            "OR printf('PAC-%04d', p.id) LIKE ? OR CAST(p.id AS TEXT) = ? "
            "ORDER BY p.id",
            (termino, like, like, like, termino),
        ).fetchall()
    finally:
        conn.close()
    return [
        (f[0], codigo_paciente(f[0]), f[1], f[3] or "", f[4] or "", calcular_edad(f[4]), f[2] or "")
        for f in filas
    ]
