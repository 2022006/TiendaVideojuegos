"""API REST de la tienda de videojuegos (Python + SQLite + FastAPI)."""
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from database import get_connection, initialize_database


# ---------- Modelos: validan los datos que llegan desde el formulario ----------
class Persona(BaseModel):
    cedula: str = Field(min_length=1, max_length=30)
    nombre: str = Field(min_length=1, max_length=80)
    apellidos: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=3, max_length=120)
    telefono: str = Field(min_length=1, max_length=30)

class Cliente(BaseModel):
    cedula: str
    nivel: str = Field(min_length=1, max_length=40)        # Casual, Frecuente, VIP...

class Empleado(BaseModel):
    cedula: str
    puesto: str = Field(min_length=1, max_length=80)
    salario_x_hora: float = Field(ge=0)

class Desarrolladora(BaseModel):
    identificador: str
    nombre: str = Field(min_length=1)
    pais: str = Field(min_length=1)

class Genero(BaseModel):
    identificador: str
    nombre: str = Field(min_length=1)                       # Shooter, Indie, Historia...

class Plataforma(BaseModel):
    identificador: str
    nombre: str = Field(min_length=1)
    fabricante: str = Field(min_length=1)

class Videojuego(BaseModel):
    identificador: str
    titulo: str = Field(min_length=1)
    anno_lanzamiento: int = Field(ge=1970, le=2100)
    clasificacion: str = Field(min_length=1, max_length=10)  # E, E10+, T, M...
    precio: float = Field(ge=0)
    stock: int = Field(ge=0)
    desarrolladora: str

class Venta(BaseModel):
    identificador: str
    fecha: date
    metodo_pago: str = Field(min_length=1)
    cliente: str
    atendido_por: str

class VideojuegoGenero(BaseModel):
    identificador_videojuego: str
    identificador_genero: str

class VideojuegoPlataforma(BaseModel):
    identificador_videojuego: str
    identificador_plataforma: str

class VentaVideojuego(BaseModel):
    identificador_venta: str
    identificador_videojuego: str
    cantidad: int = Field(gt=0)
    precio_unitario: float = Field(ge=0)


MODELS = {
    "persona": Persona, "cliente": Cliente, "empleado": Empleado,
    "desarrolladora": Desarrolladora, "genero": Genero, "plataforma": Plataforma,
    "videojuego": Videojuego, "venta": Venta,
    "videojuego_genero": VideojuegoGenero, "videojuego_plataforma": VideojuegoPlataforma,
    "venta_videojuego": VentaVideojuego,
}
# Las tablas de relación tienen llave compuesta (dos columnas).
PRIMARY_KEYS = {
    "persona": ("cedula",), "cliente": ("cedula",), "empleado": ("cedula",),
    "desarrolladora": ("identificador",), "genero": ("identificador",),
    "plataforma": ("identificador",), "videojuego": ("identificador",), "venta": ("identificador",),
    "videojuego_genero": ("identificador_videojuego", "identificador_genero"),
    "videojuego_plataforma": ("identificador_videojuego", "identificador_plataforma"),
    "venta_videojuego": ("identificador_venta", "identificador_videojuego"),
}


def check_table(table: str):
    if table not in MODELS:
        raise HTTPException(404, "Entidad no encontrada")

def split_key(table: str, key: str):
    """Convierte 'VJ01/G01' en ('VJ01', 'G01') para las llaves compuestas."""
    parts = key.split("/")
    if len(parts) != len(PRIMARY_KEYS[table]):
        raise HTTPException(400, f"La llave de {table} necesita {len(PRIMARY_KEYS[table])} valor(es)")
    return parts

def where_pk(table: str):
    return " AND ".join(f"{col} = ?" for col in PRIMARY_KEYS[table])

def db_error(exc: sqlite3.IntegrityError):
    raise HTTPException(409, "No se puede completar: clave duplicada, relación inexistente o registro en uso.") from exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()   # Crea las tablas (y datos de ejemplo) al arrancar.
    yield

app = FastAPI(title="Tienda de videojuegos", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


# ---------- Endpoints especiales (van ANTES de los genéricos) ----------
@app.get("/api/catalogo")
def catalogo(genero: str | None = None):
    """Lista los juegos con sus géneros y plataformas; se puede filtrar por género."""
    sql = """
      SELECT v.*, d.nombre AS desarrolladora_nombre,
        (SELECT GROUP_CONCAT(g.nombre, ', ') FROM videojuego_genero vg
           JOIN genero g ON g.identificador = vg.identificador_genero
          WHERE vg.identificador_videojuego = v.identificador) AS generos,
        (SELECT GROUP_CONCAT(p.nombre, ', ') FROM videojuego_plataforma vp
           JOIN plataforma p ON p.identificador = vp.identificador_plataforma
          WHERE vp.identificador_videojuego = v.identificador) AS plataformas
      FROM videojuego v JOIN desarrolladora d ON d.identificador = v.desarrolladora
    """
    params = []
    if genero:
        sql += " WHERE v.identificador IN (SELECT identificador_videojuego FROM videojuego_genero WHERE identificador_genero = ?)"
        params.append(genero)
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql + " ORDER BY v.titulo", params)]

@app.get("/api/venta/{identificador}/detalle")
def venta_detalle(identificador: str):
    """Devuelve la venta, el cliente, los juegos vendidos y el total calculado."""
    with get_connection() as conn:
        venta = conn.execute("""
          SELECT ve.*, p.nombre || ' ' || p.apellidos AS cliente_nombre
          FROM venta ve JOIN persona p ON p.cedula = ve.cliente
          WHERE ve.identificador = ?""", (identificador,)).fetchone()
        if not venta:
            raise HTTPException(404, "Venta no encontrada")
        items = conn.execute("""
          SELECT v.titulo, vv.cantidad, vv.precio_unitario, vv.cantidad * vv.precio_unitario AS subtotal
          FROM venta_videojuego vv JOIN videojuego v ON v.identificador = vv.identificador_videojuego
          WHERE vv.identificador_venta = ?""", (identificador,)).fetchall()
    items = [dict(i) for i in items]
    return {"venta": dict(venta), "videojuegos": items, "total": sum(i["subtotal"] for i in items)}


# ---------- CRUD genérico: sirve para las 11 tablas ----------
@app.get("/api/{table}")
def list_rows(table: str):
    check_table(table)
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table}")]

@app.get("/api/{table}/{key:path}")
def get_row(table: str, key: str):
    check_table(table)
    with get_connection() as conn:
        row = conn.execute(f"SELECT * FROM {table} WHERE {where_pk(table)}", split_key(table, key)).fetchone()
    if not row:
        raise HTTPException(404, "Registro no encontrado")
    return dict(row)

@app.post("/api/{table}", status_code=201)
def create_row(table: str, payload: dict):
    check_table(table)
    data = MODELS[table].model_validate(payload).model_dump(mode="json")
    columns = ", ".join(data)
    marks = ", ".join("?" for _ in data)
    try:
        with get_connection() as conn:
            conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({marks})", list(data.values()))
    except sqlite3.IntegrityError as exc:
        db_error(exc)
    return data

@app.put("/api/{table}/{key:path}")
def update_row(table: str, key: str, payload: dict):
    check_table(table)
    data = MODELS[table].model_validate(payload).model_dump(mode="json")
    pks = PRIMARY_KEYS[table]
    key_values = split_key(table, key)
    if [data[c] for c in pks] != key_values:
        raise HTTPException(400, "La clave de la URL debe coincidir con el cuerpo")
    editable = [c for c in data if c not in pks]
    if not editable:
        raise HTTPException(400, "Esta relación no tiene campos editables: bórrela y créela de nuevo")
    try:
        with get_connection() as conn:
            result = conn.execute(
                f"UPDATE {table} SET {', '.join(f'{c} = ?' for c in editable)} WHERE {where_pk(table)}",
                [data[c] for c in editable] + key_values)
    except sqlite3.IntegrityError as exc:
        db_error(exc)
    if result.rowcount == 0:
        raise HTTPException(404, "Registro no encontrado")
    return data

@app.delete("/api/{table}/{key:path}", status_code=204)
def delete_row(table: str, key: str):
    check_table(table)
    try:
        with get_connection() as conn:
            result = conn.execute(f"DELETE FROM {table} WHERE {where_pk(table)}", split_key(table, key))
    except sqlite3.IntegrityError as exc:
        db_error(exc)
    if result.rowcount == 0:
        raise HTTPException(404, "Registro no encontrado")
