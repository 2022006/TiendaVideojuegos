"""Esquema, datos de ejemplo y conexión a SQLite para la tienda de videojuegos."""
from pathlib import Path
import os
import shutil
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
# Archivo .db que va dentro del repositorio (en la computadora se usa directamente).
REPO_DB = BASE_DIR / "tienda_videojuegos.db"
# En Vercel la carpeta del proyecto es de solo lectura: lo único escribible es /tmp.
# Vercel define la variable de entorno VERCEL, así que ahí se trabaja con una copia en /tmp.
DB_PATH = Path("/tmp/tienda_videojuegos.db") if os.environ.get("VERCEL") else REPO_DB

# Igual que en la guía: persona es la tabla "madre" de cliente y empleado,
# hay catálogos (género, plataforma, desarrolladora), una tabla principal
# (videojuego), una transacción (venta) y tablas de relación muchos a muchos.
SCHEMA = """
CREATE TABLE IF NOT EXISTS persona (
  cedula TEXT PRIMARY KEY, nombre TEXT NOT NULL, apellidos TEXT NOT NULL,
  correo TEXT NOT NULL, telefono TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cliente (
  cedula TEXT PRIMARY KEY, nivel TEXT NOT NULL,
  FOREIGN KEY (cedula) REFERENCES persona(cedula) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS empleado (
  cedula TEXT PRIMARY KEY, puesto TEXT NOT NULL,
  salario_x_hora REAL NOT NULL CHECK(salario_x_hora >= 0),
  FOREIGN KEY (cedula) REFERENCES persona(cedula) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS desarrolladora (
  identificador TEXT PRIMARY KEY, nombre TEXT NOT NULL, pais TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS genero (
  identificador TEXT PRIMARY KEY, nombre TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS plataforma (
  identificador TEXT PRIMARY KEY, nombre TEXT NOT NULL, fabricante TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS videojuego (
  identificador TEXT PRIMARY KEY, titulo TEXT NOT NULL,
  anno_lanzamiento INTEGER NOT NULL CHECK(anno_lanzamiento >= 1970),
  clasificacion TEXT NOT NULL,
  precio REAL NOT NULL CHECK(precio >= 0),
  stock INTEGER NOT NULL CHECK(stock >= 0),
  desarrolladora TEXT NOT NULL,
  FOREIGN KEY (desarrolladora) REFERENCES desarrolladora(identificador) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS venta (
  identificador TEXT PRIMARY KEY, fecha TEXT NOT NULL, metodo_pago TEXT NOT NULL,
  cliente TEXT NOT NULL, atendido_por TEXT NOT NULL,
  FOREIGN KEY (cliente) REFERENCES cliente(cedula) ON DELETE RESTRICT,
  FOREIGN KEY (atendido_por) REFERENCES empleado(cedula) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS videojuego_genero (
  identificador_videojuego TEXT NOT NULL, identificador_genero TEXT NOT NULL,
  PRIMARY KEY (identificador_videojuego, identificador_genero),
  FOREIGN KEY (identificador_videojuego) REFERENCES videojuego(identificador) ON DELETE CASCADE,
  FOREIGN KEY (identificador_genero) REFERENCES genero(identificador) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS videojuego_plataforma (
  identificador_videojuego TEXT NOT NULL, identificador_plataforma TEXT NOT NULL,
  PRIMARY KEY (identificador_videojuego, identificador_plataforma),
  FOREIGN KEY (identificador_videojuego) REFERENCES videojuego(identificador) ON DELETE CASCADE,
  FOREIGN KEY (identificador_plataforma) REFERENCES plataforma(identificador) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS venta_videojuego (
  identificador_venta TEXT NOT NULL, identificador_videojuego TEXT NOT NULL,
  cantidad INTEGER NOT NULL CHECK(cantidad > 0),
  precio_unitario REAL NOT NULL CHECK(precio_unitario >= 0),
  PRIMARY KEY (identificador_venta, identificador_videojuego),
  FOREIGN KEY (identificador_venta) REFERENCES venta(identificador) ON DELETE CASCADE,
  FOREIGN KEY (identificador_videojuego) REFERENCES videojuego(identificador) ON DELETE RESTRICT
);
"""

# Datos de ejemplo para que la página no arranque vacía.
SEED = {
    "persona": [
        ("1-1111-1111", "Andrea", "Mora Vargas", "andrea@correo.com", "8888-1111"),
        ("2-2222-2222", "Diego", "Solís Rojas", "diego@correo.com", "8888-2222"),
        ("3-3333-3333", "Valeria", "Chaves Arias", "valeria@correo.com", "8888-3333"),
        ("4-4444-4444", "Kevin", "Jiménez Brenes", "kevin@correo.com", "8888-4444"),
    ],
    "cliente": [("1-1111-1111", "VIP"), ("2-2222-2222", "Casual")],
    "empleado": [("3-3333-3333", "Vendedora", 2500), ("4-4444-4444", "Encargado de inventario", 2800)],
    "desarrolladora": [
        ("D01", "343 Industries", "Estados Unidos"), ("D02", "id Software", "Estados Unidos"),
        ("D03", "Team Cherry", "Australia"), ("D04", "Maddy Makes Games", "Canadá"),
        ("D05", "ConcernedApe", "Estados Unidos"), ("D06", "Naughty Dog", "Estados Unidos"),
        ("D07", "Rockstar Games", "Estados Unidos"), ("D08", "Santa Monica Studio", "Estados Unidos"),
        ("D09", "FromSoftware", "Japón"), ("D10", "Nintendo EPD", "Japón"),
    ],
    "genero": [
        ("G01", "Shooter"), ("G02", "Indie"), ("G03", "Historia"), ("G04", "RPG"),
        ("G05", "Plataformas"), ("G06", "Mundo abierto"), ("G07", "Acción"), ("G08", "Simulación"),
    ],
    "plataforma": [
        ("P01", "PlayStation 5", "Sony"), ("P02", "Xbox Series X|S", "Microsoft"),
        ("P03", "Nintendo Switch", "Nintendo"), ("P04", "PC", "Varios"),
    ],
    "videojuego": [
        ("VJ01", "Halo Infinite", 2021, "T", 29990, 12, "D01"),
        ("VJ02", "DOOM Eternal", 2020, "M", 19990, 8, "D02"),
        ("VJ03", "Hollow Knight", 2017, "E10+", 9990, 20, "D03"),
        ("VJ04", "Celeste", 2018, "E10+", 11990, 15, "D04"),
        ("VJ05", "Stardew Valley", 2016, "E", 8990, 25, "D05"),
        ("VJ06", "The Last of Us Part I", 2022, "M", 39990, 6, "D06"),
        ("VJ07", "Red Dead Redemption 2", 2018, "M", 24990, 10, "D07"),
        ("VJ08", "God of War Ragnarök", 2022, "M", 34990, 7, "D08"),
        ("VJ09", "Elden Ring", 2022, "M", 34990, 9, "D09"),
        ("VJ10", "Super Mario Odyssey", 2017, "E10+", 34990, 11, "D10"),
    ],
    "videojuego_genero": [
        ("VJ01", "G01"), ("VJ01", "G07"), ("VJ02", "G01"), ("VJ02", "G07"),
        ("VJ03", "G02"), ("VJ03", "G05"), ("VJ04", "G02"), ("VJ04", "G05"),
        ("VJ05", "G02"), ("VJ05", "G08"), ("VJ06", "G03"), ("VJ06", "G07"),
        ("VJ07", "G03"), ("VJ07", "G06"), ("VJ08", "G03"), ("VJ08", "G07"),
        ("VJ09", "G04"), ("VJ09", "G06"), ("VJ10", "G05"),
    ],
    "videojuego_plataforma": [
        ("VJ01", "P02"), ("VJ01", "P04"), ("VJ02", "P01"), ("VJ02", "P02"), ("VJ02", "P03"), ("VJ02", "P04"),
        ("VJ03", "P01"), ("VJ03", "P02"), ("VJ03", "P03"), ("VJ03", "P04"),
        ("VJ04", "P01"), ("VJ04", "P02"), ("VJ04", "P03"), ("VJ04", "P04"),
        ("VJ05", "P01"), ("VJ05", "P02"), ("VJ05", "P03"), ("VJ05", "P04"),
        ("VJ06", "P01"), ("VJ06", "P04"), ("VJ07", "P01"), ("VJ07", "P02"), ("VJ07", "P04"),
        ("VJ08", "P01"), ("VJ08", "P04"), ("VJ09", "P01"), ("VJ09", "P02"), ("VJ09", "P04"),
        ("VJ10", "P03"),
    ],
    "venta": [
        ("V001", "2026-09-28", "Tarjeta", "1-1111-1111", "3-3333-3333"),
        ("V002", "2026-10-02", "SINPE Móvil", "2-2222-2222", "3-3333-3333"),
    ],
    "venta_videojuego": [
        ("V001", "VJ09", 1, 34990), ("V001", "VJ03", 1, 9990), ("V002", "VJ05", 2, 8990),
    ],
}


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # Permite convertir cada fila en diccionario.
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite no revisa llaves foráneas si no se activa.
    return conn


def get_connection():
    # Si Vercel abrió una instancia nueva, /tmp está vacío: se vuelve a preparar la base.
    if not DB_PATH.exists():
        initialize_database()
    return _connect()


def initialize_database():
    # En Vercel: si la copia de /tmp no existe todavía, se copia la base del repositorio.
    if DB_PATH != REPO_DB and not DB_PATH.exists() and REPO_DB.exists():
        shutil.copy(REPO_DB, DB_PATH)
    with _connect() as conn:
        conn.executescript(SCHEMA)
        # Solo inserta los datos de ejemplo la primera vez (si no hay videojuegos).
        if conn.execute("SELECT COUNT(*) FROM videojuego").fetchone()[0] == 0:
            for table, rows in SEED.items():
                marks = ", ".join("?" for _ in rows[0])
                conn.executemany(f"INSERT OR IGNORE INTO {table} VALUES ({marks})", rows)
