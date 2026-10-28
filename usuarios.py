
import hashlib
import secrets
import sqlite3

from conexion import conectar

ROLES = ("Administrador", "Médico", "Recepcionista")

USUARIO_INICIAL = "admin"
PASSWORD_INICIAL = "Admin123"
_ITERACIONES = 120_000

# Permisos por rol. "*" = todo.
PERMISOS = {
    "Administrador": {"*"},
    "JIbarra": {"*"},
    "Médico": {
        "base_expedientes", "base_agenda", "ficha", "cita_medico", "historia",
    },
    "Recepcionista": {
        "base_registro", "base_expedientes", "base_cita", "base_agenda",
        "ficha", "cita_medico", "cancelar_cita",
    },
}


def tiene_permiso(rol, permiso):
    permisos = PERMISOS.get(rol, set())
    return "*" in permisos or permiso in permisos


def _hash(password, salt_hex):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), _ITERACIONES
    ).hex()


def _validar_datos(usuario, password=None):
    if len(usuario) < 3 or " " in usuario:
        raise ValueError("El usuario debe tener al menos 3 caracteres y no llevar espacios.")
    if password is not None and len(password) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")


def crear_usuario(usuario, nombre, rol, password):
    usuario = (usuario or "").strip().lower()
    nombre = (nombre or "").strip()
    _validar_datos(usuario, password)
    if not nombre:
        raise ValueError("Ingrese el nombre completo del usuario.")
    if rol not in ROLES:
        raise ValueError("Seleccione un rol válido.")
    salt = secrets.token_hex(16)
    conn = conectar()
    try:
        conn.execute(
            "INSERT INTO usuarios (usuario, nombre, rol, salt, password_hash) VALUES (?, ?, ?, ?, ?)",
            (usuario, nombre, rol, salt, _hash(password, salt)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un usuario llamado '{usuario}'.")
    finally:
        conn.close()


def crear_admin_inicial():
    """Si no hay ningún usuario, crea el administrador inicial."""
    conn = conectar()
    try:
        total = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    finally:
        conn.close()
    if total == 0:
        crear_usuario(USUARIO_INICIAL, "Administrador del sistema", "Administrador", PASSWORD_INICIAL)


def autenticar(usuario, password):
    """Devuelve un diccionario con los datos del usuario o None si las credenciales son incorrectas."""
    usuario = (usuario or "").strip().lower()
    conn = conectar()
    try:
        fila = conn.execute(
            "SELECT id, usuario, nombre, rol, salt, password_hash, activo FROM usuarios WHERE usuario = ?",
            (usuario,),
        ).fetchone()
    finally:
        conn.close()
    if fila is None or not fila[6]:
        return None
    if not secrets.compare_digest(_hash(password or "", fila[4]), fila[5]):
        return None
    return {"id": fila[0], "usuario": fila[1], "nombre": fila[2], "rol": fila[3]}


def usa_password_inicial(usuario_dict):
    """True si el usuario es el admin y todavía conserva la contraseña de fábrica."""
    if usuario_dict["usuario"] != USUARIO_INICIAL:
        return False
    return autenticar(USUARIO_INICIAL, PASSWORD_INICIAL) is not None


def listar_usuarios():
    conn = conectar()
    try:
        return conn.execute(
            "SELECT id, usuario, nombre, rol, CASE activo WHEN 1 THEN 'Activo' ELSE 'Inactivo' END "
            "FROM usuarios ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def cambiar_password(usuario_id, nueva_password):
    if len(nueva_password or "") < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
    salt = secrets.token_hex(16)
    conn = conectar()
    try:
        cur = conn.execute(
            "UPDATE usuarios SET salt = ?, password_hash = ? WHERE id = ?",
            (salt, _hash(nueva_password, salt), usuario_id),
        )
        if cur.rowcount == 0:
            raise ValueError("El usuario no existe.")
        conn.commit()
    finally:
        conn.close()


def eliminar_usuario(usuario_id, usuario_actual_id):
    if usuario_id == usuario_actual_id:
        raise ValueError("No puede eliminar el usuario con el que inició sesión.")
    conn = conectar()
    try:
        fila = conn.execute("SELECT rol FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        if fila is None:
            raise ValueError("El usuario no existe.")
        if fila[0] == "Administrador":
            admins = conn.execute(
                "SELECT COUNT(*) FROM usuarios WHERE rol = 'Administrador' AND activo = 1"
            ).fetchone()[0]
            if admins <= 1:
                raise ValueError("Debe existir al menos un administrador en el sistema.")
        conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
    finally:
        conn.close()
