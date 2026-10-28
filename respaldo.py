
import os
import sqlite3
from datetime import datetime

from conexion import conectar

CARPETA_RESPALDOS = "respaldos"


def crear_respaldo(carpeta=CARPETA_RESPALDOS, prefijo="clinica_respaldo"):
    """Crea una copia fechada de la base de datos y devuelve su ruta."""
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{prefijo}_{datetime.now():%Y%m%d_%H%M%S}.db")
    origen = conectar()
    destino = sqlite3.connect(ruta)
    try:
        origen.backup(destino)
    finally:
        destino.close()
        origen.close()
    return ruta


def validar_respaldo(ruta):
    """Verifica que el archivo sea una base de datos de la clínica."""
    if not os.path.isfile(ruta):
        raise ValueError("El archivo seleccionado no existe.")
    try:
        con = sqlite3.connect(ruta)
        try:
            tablas = {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        finally:
            con.close()
    except sqlite3.DatabaseError:
        raise ValueError("El archivo no es una base de datos SQLite válida.")
    if not {"pacientes", "citas"}.issubset(tablas):
        raise ValueError("El archivo no corresponde a una base de datos de la clínica.")


def restaurar_respaldo(ruta):
    """
    Reemplaza el contenido de clinica.db con el del respaldo.
    Antes de restaurar guarda una copia de seguridad del estado actual.
    Devuelve la ruta de esa copia previa.
    """
    validar_respaldo(ruta)
    previa = crear_respaldo(prefijo="clinica_antes_de_restaurar")
    origen = sqlite3.connect(ruta)
    destino = conectar()
    try:
        origen.backup(destino)
    finally:
        origen.close()
        destino.close()
    from migracion import preparar_base_de_datos  # por si el respaldo es de una versión anterior
    preparar_base_de_datos()
    return previa


def listar_respaldos(carpeta=CARPETA_RESPALDOS):
    """Filas: (archivo, tamaño en KB, fecha de modificación), del más nuevo al más antiguo."""
    if not os.path.isdir(carpeta):
        return []
    filas = []
    for nombre in os.listdir(carpeta):
        if nombre.endswith(".db"):
            ruta = os.path.join(carpeta, nombre)
            filas.append((
                nombre,
                f"{os.path.getsize(ruta) / 1024:.1f} KB",
                datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%Y-%m-%d %H:%M"),
            ))
    return sorted(filas, key=lambda f: f[2], reverse=True)
