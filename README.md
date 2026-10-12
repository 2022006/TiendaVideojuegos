# Cartucho · Tienda de videojuegos

Aplicación web para administrar una tienda de videojuegos: catálogo, inventario, clientes, empleados y ventas. Cubre juegos de todo tipo, como shooters, indies, historia y RPG.

- **Aplicación publicada:** https://ESCRIBA-AQUI-SU-LINK.vercel.app
- **Repositorio:** https://github.com/ESCRIBA-AQUI-SU-USUARIO/tienda-videojuegos

## Descripción
Cartucho permite registrar, consultar, modificar y eliminar videojuegos y su información relacionada: géneros, plataformas y desarrolladoras. También maneja las personas de la tienda (clientes y empleados) y las ventas con su detalle. Toda la información se guarda en SQLite y la interfaz se comunica con el servidor por medio de una API REST hecha con FastAPI.

El análisis del problema, los usuarios y el diseño de la base de datos (diagrama entidad-relación, tablas, llaves y relaciones) están en [`docs/DOCUMENTACION.md`](docs/DOCUMENTACION.md).

## Tecnologías utilizadas
| Parte | Tecnología |
|---|---|
| Backend | Python 3.12 y FastAPI |
| Validación de datos | Pydantic (incluido con FastAPI) |
| Base de datos | SQLite (módulo `sqlite3` de Python) |
| Frontend | HTML, CSS y JavaScript (fetch a la API) |
| Servidor local | Uvicorn |
| Control de versiones | Git y GitHub |
| Publicación | Vercel |

## Instalación
Requisitos: Python 3.10 o superior y Git.

```bash
git clone https://github.com/ESCRIBA-AQUI-SU-USUARIO/tienda-videojuegos.git
cd tienda-videojuegos
python -m venv venv
```

Activar el entorno virtual:
- Windows: `venv\Scripts\activate`
- macOS / Linux: `source venv/bin/activate`

Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Ejecución
```bash
uvicorn main:app --reload
```
- Página: http://127.0.0.1:8000
- Documentación automática de la API: http://127.0.0.1:8000/docs

La base `tienda_videojuegos.db` ya viene con datos de ejemplo. Si se borra, el sistema la vuelve a crear sola al arrancar, con las tablas y los mismos datos de ejemplo.

## Estructura del sistema
```
tienda-videojuegos/
├── main.py                  # API con FastAPI: endpoints CRUD, catálogo y detalle de venta
├── database.py              # Conexión a SQLite, creación de tablas y datos de ejemplo
├── tienda_videojuegos.db    # Base de datos SQLite
├── requirements.txt         # Dependencias de Python
├── .gitignore
├── static/                  # Frontend
│   ├── index.html
│   ├── styles.css
│   └── app.js               # Llama a la API con fetch y dibuja la interfaz
└── docs/
    ├── DOCUMENTACION.md     # Análisis, descripción de tablas y relaciones
    ├── diagrama_er.png      # Diagrama entidad-relación
    ├── diagrama_er.pdf
    └── diagrama_er.dot      # Código fuente del diagrama (Graphviz)
```

Flujo: **Frontend (static/)** → `fetch` → **API FastAPI (main.py)** → **SQLite (database.py)**.

## Endpoints de la API
| Método | Ruta | Acción |
|---|---|---|
| GET | `/api/{tabla}` | Listar registros |
| GET | `/api/{tabla}/{id}` | Consultar un registro |
| POST | `/api/{tabla}` | Crear un registro |
| PUT | `/api/{tabla}/{id}` | Modificar un registro |
| DELETE | `/api/{tabla}/{id}` | Eliminar un registro |
| GET | `/api/catalogo?genero=G01` | Juegos con géneros y plataformas, con filtro opcional |
| GET | `/api/venta/{id}/detalle` | Recibo de una venta con total calculado |

Tablas disponibles: `persona`, `cliente`, `empleado`, `desarrolladora`, `genero`, `plataforma`, `videojuego`, `venta`, `videojuego_genero`, `videojuego_plataforma`, `venta_videojuego`. En las tablas de relación la llave es doble, por ejemplo `/api/videojuego_genero/VJ01/G01`.

Errores manejados: `404` si la tabla o el registro no existen, `409` si hay una llave duplicada o un registro en uso, `422` si los datos no son válidos.

## Nota sobre la versión publicada en Vercel
Vercel ejecuta la API como una función *serverless*, donde la carpeta del proyecto es de solo lectura y solo se puede escribir en `/tmp`. Por eso, al publicarse, el sistema copia `tienda_videojuegos.db` a `/tmp` y trabaja sobre esa copia. Todo el CRUD funciona en línea, pero Vercel puede reiniciar esa copia cuando la función queda inactiva un rato o abre una instancia nueva. En ese caso los datos vuelven a los del repositorio. Ejecutado localmente, todos los cambios quedan guardados de forma permanente en el archivo `.db`.
