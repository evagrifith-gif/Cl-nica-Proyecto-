
import re
from datetime import datetime

from conexion import conectar
from pacientes_ext import existe_paciente


def calcular_imc(peso_kg, talla_cm):
    if not peso_kg or not talla_cm:
        return None
    talla_m = talla_cm / 100.0
    return round(peso_kg / (talla_m ** 2), 1)


def clasificar_imc(imc):
    if imc is None:
        return ""
    if imc < 18.5:
        return "Bajo peso"
    if imc < 25:
        return "Normal"
    if imc < 30:
        return "Sobrepeso"
    return "Obesidad"


def _numero(texto, nombre, minimo, maximo, entero=False):
    texto = (texto or "").strip().replace(",", ".")
    if not texto:
        return None
    try:
        valor = int(texto) if entero else float(texto)
    except ValueError:
        raise ValueError(f"{nombre} debe ser un número{' entero' if entero else ''}.")
    if not (minimo <= valor <= maximo):
        raise ValueError(f"{nombre} debe estar entre {minimo} y {maximo}.")
    return valor


def registrar_signos(paciente_id, peso, talla_cm, presion, frecuencia, temperatura, saturacion):
    """Recibe los valores como texto (tal como vienen de la interfaz) y los valida."""
    peso = _numero(peso, "El peso (kg)", 1, 400)
    talla = _numero(talla_cm, "La talla (cm)", 30, 250)
    fc = _numero(frecuencia, "La frecuencia cardíaca", 20, 250, entero=True)
    temp = _numero(temperatura, "La temperatura (°C)", 30, 45)
    sat = _numero(saturacion, "La saturación de oxígeno (%)", 50, 100, entero=True)

    presion = (presion or "").strip().replace(" ", "")
    if presion:
        if not re.fullmatch(r"\d{2,3}/\d{2,3}", presion):
            raise ValueError("La presión arterial debe tener el formato 120/80.")
        sis, dia = (int(x) for x in presion.split("/"))
        if not (60 <= sis <= 260 and 30 <= dia <= 160 and sis > dia):
            raise ValueError("La presión arterial ingresada no es válida (sistólica > diastólica).")
    else:
        presion = None

    if (peso is None) != (talla is None):
        raise ValueError("Para calcular el IMC ingrese tanto el peso como la talla.")
    if all(v is None for v in (peso, talla, presion, fc, temp, sat)):
        raise ValueError("Ingrese al menos un signo vital.")

    imc = calcular_imc(peso, talla)
    conn = conectar()
    try:
        if not existe_paciente(conn, paciente_id):
            raise ValueError("El paciente no existe.")
        conn.execute(
            "INSERT INTO signos_vitales (paciente_id, fecha, peso_kg, talla_cm, imc, presion, "
            "frecuencia_cardiaca, temperatura, saturacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (paciente_id, datetime.now().strftime("%Y-%m-%d %H:%M"), peso, talla, imc, presion, fc, temp, sat),
        )
        conn.commit()
    finally:
        conn.close()
    return imc


def listar_signos(paciente_id):
    """Filas: (id, fecha, peso, talla, imc, clasificación, presión, FC, temp, saturación)."""
    conn = conectar()
    try:
        filas = conn.execute(
            "SELECT id, fecha, peso_kg, talla_cm, imc, presion, frecuencia_cardiaca, temperatura, saturacion "
            "FROM signos_vitales WHERE paciente_id = ? ORDER BY fecha DESC, id DESC", (paciente_id,)
        ).fetchall()
    finally:
        conn.close()
    return [
        (f[0], f[1], f[2], f[3], f[4], clasificar_imc(f[4]), f[5], f[6], f[7], f[8])
        for f in filas
    ]


def eliminar_signos(registro_id):
    conn = conectar()
    try:
        conn.execute("DELETE FROM signos_vitales WHERE id = ?", (registro_id,))
        conn.commit()
    finally:
        conn.close()
