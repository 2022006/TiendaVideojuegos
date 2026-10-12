// Describe cada entidad: texto visible, grupo del menú y campos del formulario.
// "fk" indica que el campo es llave foránea: se muestra como lista desplegable.
// "pk" indica cuántos campos forman la llave primaria (2 en las tablas de relación).
const entities = {
  persona: { label: 'Personas', group: 'Personas', fields: ['cedula', 'nombre', 'apellidos', 'correo', 'telefono'] },
  cliente: { label: 'Clientes', group: 'Personas', fields: ['cedula', 'nivel'], fk: { cedula: 'persona' } },
  empleado: { label: 'Empleados', group: 'Personas', fields: ['cedula', 'puesto', 'salario_x_hora'], fk: { cedula: 'persona' } },
  videojuego: { label: 'Videojuegos', group: 'Juegos', fields: ['identificador', 'titulo', 'anno_lanzamiento', 'clasificacion', 'precio', 'stock', 'desarrolladora'], fk: { desarrolladora: 'desarrolladora' } },
  genero: { label: 'Géneros', group: 'Juegos', fields: ['identificador', 'nombre'] },
  plataforma: { label: 'Plataformas', group: 'Juegos', fields: ['identificador', 'nombre', 'fabricante'] },
  desarrolladora: { label: 'Desarrolladoras', group: 'Juegos', fields: ['identificador', 'nombre', 'pais'] },
  videojuego_genero: { label: 'Juego-género', group: 'Juegos', pk: 2, fields: ['identificador_videojuego', 'identificador_genero'], fk: { identificador_videojuego: 'videojuego', identificador_genero: 'genero' } },
  videojuego_plataforma: { label: 'Juego-plataforma', group: 'Juegos', pk: 2, fields: ['identificador_videojuego', 'identificador_plataforma'], fk: { identificador_videojuego: 'videojuego', identificador_plataforma: 'plataforma' } },
  venta: { label: 'Ventas', group: 'Ventas', fields: ['identificador', 'fecha', 'metodo_pago', 'cliente', 'atendido_por'], fk: { cliente: 'cliente', atendido_por: 'empleado' } },
  venta_videojuego: { label: 'Venta-juego', group: 'Ventas', pk: 2, fields: ['identificador_venta', 'identificador_videojuego', 'cantidad', 'precio_unitario'], fk: { identificador_venta: 'venta', identificador_videojuego: 'videojuego' } }
};

// Campos numéricos: enteros y decimales.
const INTEGER = ['anno_lanzamiento', 'stock', 'cantidad'];
const DECIMAL = ['precio', 'salario_x_hora', 'precio_unitario'];
// Color del "lomo" de la caja según el primer género del juego.
const GENRE_COLORS = { Shooter: '#d7263d', Indie: '#2ba84a', Historia: '#c9822b', RPG: '#7b3fe4', Plataformas: '#1f9bd1', 'Mundo abierto': '#2f8f83', 'Acción': '#e2572b', 'Simulación': '#8a9a2b' };

let current = 'catalogo';   // Pestaña activa.
let editing = null;         // Fila que se está editando (o null si se está creando).
let filtroGenero = '';      // Género elegido en el catálogo.

const $ = id => document.getElementById(id);
const label = text => text.replaceAll('_', ' ').replace('anno', 'año');
const colones = n => '₡' + Number(n).toLocaleString('es-CR');
// Evita que texto escrito por el usuario se interprete como HTML.
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const pkFields = entity => entities[entity].fields.slice(0, entities[entity].pk || 1);
const keyOf = (entity, row) => pkFields(entity).map(f => encodeURIComponent(row[f])).join('/');

async function api(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map(d => `${d.loc.at(-1)}: ${d.msg}`).join('; ') : body.detail;
    throw new Error(detail || 'Error ' + response.status);
  }
  return response.status === 204 ? null : response.json();
}

// ---------- Navegación ----------
function nav() {
  const groups = { Tienda: [['catalogo', 'Catálogo']] };
  for (const [key, e] of Object.entries(entities)) (groups[e.group] ||= []).push([key, e.label]);
  $('tabs').innerHTML = Object.entries(groups).map(([name, items]) =>
    `<div class="grupo"><span>${name}</span><div>${items.map(([key, text]) =>
      `<button class="${key === current ? 'active' : ''}" onclick="choose('${key}')">${text}</button>`).join('')}</div></div>`
  ).join('');
}

function choose(entity) {
  current = entity;
  editing = null;
  nav();
  const isCatalog = entity === 'catalogo';
  $('catalogo-view').hidden = !isCatalog;
  $('crud-view').hidden = isCatalog;
  if (isCatalog) return loadCatalog();
  $('message').textContent = '';
  $('detalle').innerHTML = '';
  render().then(load);
}

// ---------- Catálogo ----------
async function loadCatalog() {
  const generos = await api('/api/genero');
  $('filtros').innerHTML = [['', 'Todos'], ...generos.map(g => [g.identificador, g.nombre])].map(([id, nombre]) =>
    `<button class="${id === filtroGenero ? 'active' : ''}" onclick="filtrar('${id}')">${esc(nombre)}</button>`).join('');
  const juegos = await api('/api/catalogo' + (filtroGenero ? '?genero=' + filtroGenero : ''));
  $('juegos').innerHTML = juegos.length ? juegos.map(j => {
    const generosJuego = (j.generos || '').split(', ').filter(Boolean);
    const color = GENRE_COLORS[generosJuego[0]] || '#3d3bf3';
    return `<article class="caja" style="--lomo:${color}">
      <h3>${esc(j.titulo)}</h3>
      <p class="meta">${esc(j.desarrolladora_nombre)}, ${j.anno_lanzamiento}</p>
      <div class="tags">${generosJuego.map(g => `<span>${esc(g)}</span>`).join('')}</div>
      <p class="meta">${esc(j.plataformas || 'Sin plataformas asignadas')}</p>
      <div class="pie"><span class="precio">${colones(j.precio)}</span>
        ${j.stock > 0 ? `<span class="meta">${j.stock} en stock</span>` : '<span class="agotado">Agotado</span>'}
        <span class="edad" title="Clasificación ESRB">${esc(j.clasificacion)}</span></div>
    </article>`;
  }).join('') : '<p>No hay juegos de este género todavía. Agréguelos en Juegos → Juego-género.</p>';
}

function filtrar(id) { filtroGenero = id; loadCatalog(); }

// ---------- Administración (CRUD) ----------
// Construye el formulario; las llaves foráneas se llenan con datos de su tabla.
async function render() {
  const entity = entities[current];
  $('title').textContent = entity.label;
  const options = {};
  for (const [field, table] of Object.entries(entity.fk || {})) options[field] = await api('/api/' + table);
  // Para clientes y empleados se muestra el nombre de la persona en vez de solo la cédula.
  const personas = Object.values(entity.fk || {}).some(t => t === 'cliente' || t === 'empleado')
    ? Object.fromEntries((await api('/api/persona')).map(p => [p.cedula, p.nombre + ' ' + p.apellidos])) : {};

  $('form').innerHTML = entity.fields.map(field => {
    const locked = editing && pkFields(current).includes(field) ? 'readonly' : '';
    if (options[field]) {
      const opts = options[field].map(r => {
        const id = Object.values(r)[0];
        const text = r.titulo || r.nombre || personas[id] || r.cedula || id;
        return `<option value="${esc(id)}">${esc(id)} · ${esc(text)}</option>`;
      }).join('');
      // Un select no admite readonly; si está bloqueado, se desactiva y se envía con un input oculto.
      return `<label>${label(field)}<select name="${field}" ${locked ? 'disabled' : ''} required>${opts}</select>
        ${locked ? `<input type="hidden" name="${field}">` : ''}</label>`;
    }
    let type = 'text';
    if (field === 'fecha') type = 'date';
    if (field === 'correo') type = 'email';
    if (INTEGER.includes(field)) type = 'number" step="1" min="0';
    if (DECIMAL.includes(field)) type = 'number" step="0.01" min="0';
    return `<label>${label(field)}<input name="${field}" type="${type}" ${locked} required></label>`;
  }).join('') + `<button class="primary">${editing ? 'Guardar cambios' : 'Crear'}</button>`
    + (editing ? '<button type="button" onclick="cancelEdit()">Cancelar</button>' : '');

  $('form').onsubmit = save;
  $('head').innerHTML = '<tr>' + entity.fields.map(f => `<th>${label(f)}</th>`).join('') + '<th>Acciones</th></tr>';
}

async function load() {
  const rows = await api('/api/' + current);
  const entity = entities[current];
  const canEdit = entity.fields.length > (entity.pk || 1);  // Las relaciones sin datos extra no se editan.
  $('body').innerHTML = rows.length ? rows.map(row => '<tr>' +
    entity.fields.map(f => `<td>${DECIMAL.includes(f) ? colones(row[f]) : esc(row[f])}</td>`).join('') +
    `<td class="actions">
      ${current === 'venta' ? `<button onclick="verVenta('${encodeURIComponent(row.identificador)}')">Ver detalle</button>` : ''}
      ${canEdit ? `<button onclick='edit(${esc(JSON.stringify(row))})'>Editar</button>` : ''}
      <button class="danger" onclick="removeRow('${keyOf(current, row)}')">Borrar</button></td></tr>`
  ).join('') : `<tr><td colspan="${entity.fields.length + 1}">Sin registros. Use el formulario de arriba para crear el primero.</td></tr>`;
}

// Envía el formulario como JSON: POST para crear y PUT para actualizar.
async function save(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  for (const f of entities[current].fields) {
    if (INTEGER.includes(f) || DECIMAL.includes(f)) data[f] = Number(data[f]);
  }
  try {
    await api('/api/' + current + (editing ? '/' + keyOf(current, data) : ''), {
      method: editing ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    showMessage(editing ? 'Cambios guardados.' : 'Registro creado.', true);
    editing = null;
    await render();
    load();
  } catch (err) { showMessage(err.message, false); }
}

async function edit(row) {
  editing = row;
  await render();
  for (const [key, value] of Object.entries(row)) {
    for (const el of $('form').querySelectorAll(`[name="${key}"]`)) el.value = value;
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function cancelEdit() { editing = null; render(); }

async function removeRow(key) {
  if (!confirm('¿Eliminar este registro?')) return;
  try {
    await api('/api/' + current + '/' + key, { method: 'DELETE' });
    showMessage('Registro eliminado.', true);
    load();
  } catch (err) { showMessage(err.message, false); }
}

// Muestra el recibo de una venta usando el endpoint /detalle.
async function verVenta(id) {
  const d = await api('/api/venta/' + id + '/detalle');
  $('detalle').innerHTML = `<div class="recibo">
    <h3>Venta ${esc(d.venta.identificador)}</h3>
    <p class="meta">${esc(d.venta.fecha)}, ${esc(d.venta.cliente_nombre)}, pagó con ${esc(d.venta.metodo_pago)}</p>
    <table><tr><th>Juego</th><th>Cant.</th><th>Subtotal</th></tr>
      ${d.videojuegos.map(v => `<tr><td>${esc(v.titulo)}</td><td>${v.cantidad}</td><td>${colones(v.subtotal)}</td></tr>`).join('')}
    </table>
    <p class="total">Total: ${colones(d.total)}</p></div>`;
}

function showMessage(text, ok) {
  $('message').textContent = text;
  $('message').className = ok ? 'ok' : 'error';
}

// Arranque: muestra el catálogo.
choose('catalogo');
