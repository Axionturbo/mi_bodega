from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT NOT NULL,
            categoria TEXT,
            precio_compra REAL,
            precio_venta REAL,
            stock INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            cantidad INTEGER,
            total REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- DISEÑO BASE CON PESTAÑAS (VENTANAS) ---
LAYOUT_HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Bodega</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #f0f2f5; color: #1c1e21; }
        .navbar { background: #1877f2; padding: 12px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
        .navbar a { color: white; text-decoration: none; padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 0.95rem; background: rgba(255,255,255,0.1); }
        .navbar a:hover, .navbar a.active { background: rgba(255,255,255,0.3); }
        .container { max-width: 900px; margin: 20px auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        h1 { color: #1877f2; font-size: 1.5rem; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
        th, td { padding: 10px; border-bottom: 1px solid #e4e6eb; text-align: left; }
        th { background-color: #f7f8fa; color: #65676b; }
        form { margin-top: 15px; background: #f7f8fa; padding: 15px; border-radius: 8px; }
        input, select { padding: 10px; margin: 6px 0; width: 100%; border: 1px solid #ccc; border-radius: 6px; font-size: 0.95rem; }
        button { background: #42b72a; color: white; border: none; padding: 12px; width: 100%; cursor: pointer; border-radius: 6px; font-weight: bold; font-size: 1rem; margin-top: 8px; }
        button.venta { background: #ff7a00; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .stat-card { background: #e7f3ff; padding: 15px; border-radius: 8px; border-left: 5px solid #1877f2; }
        .stat-card h3 { margin: 0 0 5px 0; font-size: 0.9rem; color: #555; }
        .stat-card p { margin: 0; font-size: 1.4rem; font-weight: bold; color: #1877f2; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/ventas" class="{% if active == 'ventas' %}active{% endif %}">🛒 Ventas (Escaner)</a>
        <a href="/inventario" class="{% if active == 'inventario' %}active{% endif %}">📦 Inventario</a>
        <a href="/resumen" class="{% if active == 'resumen' %}active{% endif %}">📊 Resumen y Reportes</a>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
'''

# --- VENTANA 1: VENTAS Y ESCANER ---
@app.route('/')
@app.route('/ventas')
def ventas():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, codigo, nombre, precio_venta, stock FROM productos')
    productos = cursor.fetchall()
    
    cursor.execute('''
        SELECT ventas.id, productos.nombre, ventas.cantidad, ventas.total, ventas.fecha 
        FROM ventas JOIN productos ON ventas.producto_id = productos.id 
        ORDER BY ventas.fecha DESC LIMIT 15
    ''')
    ultimas_ventas = cursor.fetchall()
    conn.close()
    
    html = LAYOUT_HTML.replace('{% block content %}{% endblock %}', '''
    <h1>🛒 Registrar Venta (Escáner o Buscador)</h1>
    
    <form action="/registrar_venta" method="POST">
        <label><b>Escanear código de barras o buscar producto:</b></label>
        <input type="text" id="buscador" placeholder="Haz clic aquí y pasa el lector de barras o escribe el nombre..." autofocus autocomplete="off">
        
        <select name="producto_id" id="select_producto" required style="margin-top: 10px;">
            <option value="">-- Seleccione el producto --</option>
            {% for p in productos %}
            <option value="{{ p[0] }}" data-codigo="{{ p[1] }}" data-nombre="{{ p[2] }}">
                [{{ p[1] or 'Sin Código' }}] {{ p[2] }} - Stock: {{ p[4] }} - ${{ "%.2f"|format(p[3]) }}
            </option>
            {% endfor %}
        </select>
        
        <label style="margin-top: 10px; display:block;">Cantidad:</label>
        <input type="number" name="cantidad" value="1" min="1" required>
        
        <button type="submit" class="venta">Cobrar y Registrar Venta</button>
    </form>

    <script>
        // Script inteligente para lector de códigos de barras (escáner USB/Bluetooth) o búsqueda rápida
        const buscador = document.getElementById('buscador');
        const select = document.getElementById('select_producto');

        buscador.addEventListener('input', function() {
            const texto = buscador.value.toLowerCase();
            for (let option of select.options) {
                const codigo = option.getAttribute('data-codigo') ? option.getAttribute('data-codigo').toLowerCase() : '';
                const nombre = option.getAttribute('data-nombre') ? option.getAttribute('data-nombre').toLowerCase() : '';
                
                if (codigo.includes(texto) || nombre.includes(texto)) {
                    select.value = option.value;
                    break;
                }
            }
        });
    </script>

    <h2>Historial de Ventas Rápidas</h2>
    <table>
        <tr><th>Producto</th><th>Cant</th><th>Total</th><th>Fecha</th></tr>
        {% for v in ultimas_ventas %}
        <tr>
            <td>{{ v[1] }}</td>
            <td>{{ v[2] }}</td>
            <td>${{ "%.2f"|format(v[3]) }}</td>
            <td><small>{{ v[4] }}</small></td>
        </tr>
        {% endfor %}
    </table>
    ''')
    return render_template_string(html, active='ventas', productos=productos, ultimas_ventas=ultimas_ventas)

@app.route('/registrar_venta', methods=['POST'])
def registrar_venta():
    producto_id = int(request.form['producto_id'])
    cantidad = int(request.form['cantidad'])
    
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT precio_venta, stock FROM productos WHERE id = ?', (producto_id,))
    prod = cursor.fetchone()
    if prod and prod[1] >= cantidad:
        total = prod[0] * cantidad
        cursor.execute('INSERT INTO ventas (producto_id, cantidad, total) VALUES (?, ?, ?)', (producto_id, cantidad, total))
        cursor.execute('UPDATE productos SET stock = ? WHERE id = ?', (prod[1] - cantidad, producto_id))
        conn.commit()
    conn.close()
    return redirect(url_for('ventas'))

# --- VENTANA 2: INVENTARIO ---
@app.route('/inventario')
def inventario():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()
    
    html = LAYOUT_HTML.replace('{% block content %}{% endblock %}', '''
    <h1>📦 Control de Inventario y Productos</h1>
    
    <form action="/add_product" method="POST">
        <h3>Agregar Nuevo Producto</h3>
        <input type="text" name="codigo" placeholder="Código de barras (opcional)">
        <input type="text" name="nombre" placeholder="Nombre del producto" required>
        <input type="text" name="categoria" placeholder="Categoría">
        <input type="number" step="0.01" name="precio_compra" placeholder="Precio de Compra ($)" required>
        <input type="number" step="0.01" name="precio_venta" placeholder="Precio de Venta ($)" required>
        <input type="number" name="stock" placeholder="Stock Inicial" required>
        <button type="submit">Guardar en Inventario</button>
    </form>

    <h2>Lista de Productos</h2>
    <table>
        <tr><th>Código</th><th>Nombre</th><th>P. Venta</th><th>Stock</th></tr>
        {% for p in productos %}
        <tr>
            <td>{{ p[1] or 'N/D' }}</td>
            <td><strong>{{ p[2] }}</strong></td>
            <td>${{ "%.2f"|format(p[5]) }}</td>
            <td><span style="color: {% if p[6] < 5 %}red{% else %}green{% endif %}">{{ p[6] }}</span></td>
        </tr>
        {% endfor %}
    </table>
    ''')
    return render_template_string(html, active='inventario', productos=productos)

@app.route('/add_product', methods=['POST'])
def add_product():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO productos (codigo, nombre, categoria, precio_compra, precio_venta, stock) VALUES (?, ?, ?, ?, ?, ?)',
                   (request.form['codigo'], request.form['nombre'], request.form['categoria'], 
                    float(request.form['precio_compra']), float(request.form['precio_venta']), int(request.form['stock'])))
    conn.commit()
    conn.close()
    return redirect(url_for('inventario'))

# --- VENTANA 3: RESUMEN DIARIO, SEMANAL Y MENSUAL ---
@app.route('/resumen')
def resumen():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    
    # Total Diario (Hoy)
    cursor.execute("SELECT SUM(total), SUM(cantidad) FROM ventas WHERE DATE(fecha) = DATE('now', 'localtime')")
    diario = cursor.fetchone()
    total_dia = diario[0] or 0.0
    cant_dia = diario[1] or 0
    
    # Total Semanal (Últimos 7 días)
    cursor.execute("SELECT SUM(total), SUM(cantidad) FROM ventas WHERE fecha >= datetime('now', '-7 days')")
    semanal = cursor.fetchone()
    total_sem = semanal[0] or 0.0
    cant_sem = semanal[1] or 0
    
    # Total Mensual (Mes actual)
    cursor.execute("SELECT SUM(total), SUM(cantidad) FROM ventas WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')")
    mensual = cursor.fetchone()
    total_mes = mensual[0] or 0.0
    cant_mes = mensual[1] or 0
    
    conn.close()
    
    html = LAYOUT_HTML.replace('{% block content %}{% endblock %}', f'''
    <h1>📊 Resumen de Ventas y Finanzas</h1>
    
    <div class="stats-grid">
        <div class="stat-card">
            <h3>Hoy (Diario)</h3>
            <p>${total_dia:.2f}</p>
            <small>{{ cant_dia }} productos vendidos</small>
        </div>
        <div class="stat-card">
            <h3>Últimos 7 Días (Semanal)</h3>
            <p>${total_sem:.2f}</p>
            <small>{{ cant_sem }} productos vendidos</small>
        </div>
        <div class="stat-card">
            <h3>Mes Actual (Mensual)</h3>
            <p>${total_mes:.2f}</p>
            <small>{{ cant_mes }} productos vendidos</small>
        </div>
    </div>
    ''')
    return render_template_string(html, active='resumen', cant_dia=cant_dia, cant_sem=cant_sem, cant_mes=cant_mes)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)