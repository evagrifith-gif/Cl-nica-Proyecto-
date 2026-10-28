
from conexion import conectar, crear_tablas

SCRIPT = """
CREATE TABLE IF NOT EXISTS pacientes_datos (
    paciente_id INTEGER PRIMARY KEY,
    dpi TEXT UNIQUE,
    fecha_nacimiento TEXT,
    direccion TEXT,
    contacto_emergencia TEXT,
    telefono_emergencia TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
);

CREATE TABLE IF NOT EXISTS medicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    especialidad TEXT NOT NULL,
    colegiado TEXT UNIQUE,
    telefono TEXT
);

CREATE TABLE IF NOT EXISTS citas_detalle (
    cita_id INTEGER PRIMARY KEY,
    medico_id INTEGER,
    especialidad TEXT,
    estado TEXT NOT NULL DEFAULT 'Programada',
    FOREIGN KEY (cita_id) REFERENCES citas (id),
    FOREIGN KEY (medico_id) REFERENCES medicos (id)
);

CREATE TABLE IF NOT EXISTS antecedentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_registro TEXT NOT NULL,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
);

CREATE TABLE IF NOT EXISTS signos_vitales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    peso_kg REAL,
    talla_cm REAL,
    imc REAL,
    presion TEXT,
    frecuencia_cardiaca INTEGER,
    temperatura REAL,
    saturacion INTEGER,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
);

CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    cita_id INTEGER,
    medico_id INTEGER,
    fecha TEXT NOT NULL,
    diagnostico TEXT NOT NULL,
    tratamiento TEXT,
    receta TEXT,
    observaciones TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
    FOREIGN KEY (cita_id) REFERENCES citas (id),
    FOREIGN KEY (medico_id) REFERENCES medicos (id)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL,
    salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TRIGGER IF NOT EXISTS trg_pacientes_borrar
AFTER DELETE ON pacientes
BEGIN
    DELETE FROM pacientes_datos WHERE paciente_id = OLD.id;
    DELETE FROM antecedentes    WHERE paciente_id = OLD.id;
    DELETE FROM signos_vitales  WHERE paciente_id = OLD.id;
    DELETE FROM consultas       WHERE paciente_id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_citas_borrar
AFTER DELETE ON citas
BEGIN
    DELETE FROM citas_detalle WHERE cita_id = OLD.id;
    UPDATE consultas SET cita_id = NULL WHERE cita_id = OLD.id;
END;
"""


def preparar_base_de_datos():
    """Crea (si no existen) las tablas originales, las nuevas y el usuario admin."""
    crear_tablas()  # función original: solo crea pacientes y citas si faltan
    conn = conectar()
    try:
        conn.executescript(SCRIPT)
        conn.commit()
    finally:
        conn.close()
    from usuarios import crear_admin_inicial
    crear_admin_inicial()


if __name__ == "__main__":
    preparar_base_de_datos()
    print("Base de datos lista: tablas originales y nuevas creadas.")
