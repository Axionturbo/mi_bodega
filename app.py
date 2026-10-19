from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
import os

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
            stock INTEGER,
            imagen_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            cantidad INTEGER,
            total REAL,
            metodo_pago TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fiados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            telefono TEXT,
            monto_deuda REAL,
            estado TEXT DEFAULT 'PENDIENTE',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

LAYOUT_HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema POS Bodega Pro</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #f0f2f5; color: #1c1e21; }
        .navbar { background: #0d6efd; padding: 12px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
        .navbar a { color: white; text-decoration: none; padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 0.95rem; background: rgba(255,255,255,0.15); }
        .navbar a:hover, .navbar a.active { background: rgba(255,255,255,0.35); }
        .container { max-width: 1050px; margin: 15px auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        h1 { color: #0d6efd; font-size: 1.4rem; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85rem; }
        th, td { padding: 8px; border-bottom: 1px solid #e4e6eb; text-align: left; }
        th { background-color: #f7f8fa; color: #65676b; }
        form { margin-top: 10px; background: #f8f9fa; padding: 12px; border-radius: 8px; border: 1px solid #dee2e6; }
        input, select { padding: 9px; margin: 5px 0; width: 100%; border: 1px solid #ccc; border-radius: 6px; font-size: 0.9rem; }
        button { background: #198754; color: white; border: none; padding: 10px; width: 100%; cursor: pointer; border-radius: 6px; font-weight: bold; font-size: 0.95rem; margin-top: 5px; }
        button.venta { background: #fd7e14; }
        
        /* DISEÑO DE TARJETAS TÁCTILES CON IMAGEN */
        .products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-top: 15px; max-height: 400px; overflow-y: auto; padding: 5px; }
        .product-card { background: #fff; border: 1px solid #e0e0e0; border-radius: 10px; padding: 10px; text-align: center; cursor: pointer; transition: transform 0.1s, box-shadow 0.1s; display: flex; flex-direction: column; justify-content: space-between; align-items: center; }
        .product-card:hover { transform: translateY(-3px); box-shadow: 0 4px 10px rgba(0,0,0,0.12); border-color: #0d6efd; }
        .product-card img { width: 80px; height: 80px; object-fit: contain; border-radius: 6px; margin-bottom: 6px; }
        .product-card .title { font-size: 0.85rem; font-weight: bold; color: #333; line-height: 1.1; height: 2.2em; overflow: hidden; }
        .product-card .price { color: #198754; font-weight: bold; font-size: 1rem; margin-top: 4px; }
        .product-card .stock { font-size: 0.75rem; color: #666; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin-top: 10px; }
        .stat-card { background: #e7f1ff; padding: 12px; border-radius: 8px; border-left: 4px solid #0d6efd; }
        .stat-card h3 { margin: 0 0 5px 0; font-size: 0.85rem; color: #495057; }
        .stat-card p { margin: 0; font-size: 1.2rem; font-weight: bold; color: #0d6efd; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/ventas" class="{% if active == 'ventas' %}active{% endif %}">🛒 POS Ventas Visual</a>
        <a href="/inventario" class="{% if active == 'inventario' %}active{% endif %}">📦 Inventario</a>
        <a href="/fiados" class="{% if active == 'fiados' %}active{% endif %}">📋 Fiados</a>
        <a href="/resumen" class="{% if active == 'resumen' %}active{% endif %}">📊 Cierre de Caja</a>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
'''

# --- VENTANA 1: VENTAS VISUALES CON TARJETAS E IMÁGENES ---
@app.route('/')
@app.route('/ventas')
def ventas():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, codigo, nombre, precio_venta, stock, imagen_url FROM productos')
    productos = cursor.fetchall()
    
    cursor.execute('''
        SELECT ventas.id, productos.nombre, ventas.cantidad, ventas.total, ventas.metodo_pago, ventas.fecha 
        FROM ventas JOIN productos ON ventas.producto_id = productos.id 
        ORDER BY ventas.fecha DESC LIMIT 8
    ''')
    ultimas_ventas = cursor.fetchall()
    conn.close()
    
    html = LAYOUT_HTML.replace('{% block content %}{% endblock %}', '''
    <h1>🛒 Punto de Venta Visual (Toca para seleccionar)</h1>
    
    <label><b>🔍 Buscar o Escanear Código:</b></label>
    <input type="text" id="buscador" placeholder="Pasa el lector o escribe el producto..." autofocus autocomplete="off">
    
    <!-- CATALOGO EN GRID CON FOTOS -->
    <div class="products-grid" id="grid_productos">
        {% for p in productos %}
        <div class="product-card" onclick="seleccionarProducto('{{ p[0] }}', '{{ p[2] }}')" data-codigo="{{ p[1] }}" data-nombre="{{ p[2] }}">
            <img src="{{ p[5] or 'https://cdn-icons-png.flaticon.com/512/3081/3081559.png' }}" alt="{{ p[2] }}">
            <div class="title">{{ p[2] }}</div>
            <div class="price">${{ "%.2f"|format(p[3]) }}</div>
            <div class="stock">Disponibles: {{ p[4] }}</div>
        </div>
        {% endfor %}
    </div>

    <form action="/registrar_venta" method="POST" style="margin-top: 15px; background: #eef5ff; border-color: #0d6efd;">
        <h3 style="margin: 0 0 8px 0; color: #0d6efd;">Cobrar Producto Seleccionado:</h3>
        
        <select name="producto_id" id="select_producto" required>
            <option value="">-- Seleccione un producto arriba o escanee --</option>
            {% for p in productos %}
            <option value="{{ p[0] }}">
                {{ p[2] }} - ${{ "%.2f"|format(p[3]) }}
            </option>
            {% endfor %}
        </select>
        
        <div style="display: flex; gap: 10px; margin-top: 8px;">
            <div style="flex: 1;">
                <label>Cantidad:</label>
                <input type="number" name="cantidad" value="1" min="1" required>
            </div>
            <div style="flex: 2;">
                <label>Método de Pago:</label>
                <select name="metodo_pago" required>
                    <option value="Efectivo USD">Efectivo USD ($)</option>
                    <option value="Pago Móvil">Pago Móvil (Bs)</option>
                    <option value="Punto de Venta">Punto de Venta</option>
                    <option value="Efectivo Bs">Efectivo Bolívares (Bs)</option>
                </select>
            </div>
        </div>
        
        <button type="submit" class="venta"> Registrar Venta</button>
    </form>

    <script>
        function seleccionarProducto(id, nombre) {
            document.getElementById('select_producto').value = id;
        }

        const buscador = document.getElementById('buscador');
        const cards = document.querySelectorAll('.product-card');

        buscador.addEventListener('input', function() {
            const texto = buscador.value.toLowerCase();
            cards.forEach(card => {
                const codigo = card.getAttribute('data-codigo') ? card.getAttribute('data-codigo').toLowerCase() : '';
                const nombre = card.getAttribute('data-nombre') ? card.getAttribute('data-nombre').toLowerCase() : '';
                
                if (codigo.includes(texto) || nombre.includes(texto)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    </script>

    <h2 style="margin-top: 20px;">Últimas Ventas</h2>
    <table>
        <tr><th>Producto</th><th>Cant</th><th>Total</th><th>Pago</th><th>Fecha</th></tr>
        {% for v in ultimas_ventas %}
        <tr>
            <td><strong>{{ v[1] }}</strong></td>
            <td>{{ v[2] }}</td>
            <td>${{ "%.2f"|format(v[3]) }}</td>
            <td><small>{{ v[4] }}</small></td>
            <td><small>{{ v[5] }}</small></td>
        </tr>
        {% endfor %}
    </table>
    ''')
    return render_template_string(html, active='ventas', productos=productos, ultimas_ventas=ultimas_ventas)

@app.route('/registrar_venta', methods=['POST'])
def registrar_venta():
    producto_id = int(request.form['producto_id'])
    cantidad = int(request.form['cantidad'])
    metodo_pago = request.form['metodo_pago']
    
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT precio_venta, stock FROM productos WHERE id = ?', (producto_id,))
    prod = cursor.fetchone()
    if prod and prod[1] >= cantidad:
        total = prod[0] * cantidad
        cursor.execute('INSERT INTO ventas (producto_id, cantidad, total, metodo_pago) VALUES (?, ?, ?, ?)', 
                       (producto_id, cantidad, total, metodo_pago))
        cursor.execute('UPDATE productos SET stock = ? WHERE id = ?', (prod[1] - cantidad, producto_id))
        conn.commit()
    conn.close()
    return redirect(url_for('ventas'))

# --- VENTANA 2: INVENTARIO CON REGISTRO DE FOTOS ---
@app.route('/inventario')
def inventario():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()
    
    html = LAYOUT_HTML.replace('{% block content %}{% endblock %}', '''
    <h1>📦 Gestión de Inventario</h1>
    
    <form action="/add_product" method="POST">
        <h3>➕ Registrar Nuevo Producto</h3>
        <input type="text" name="codigo" placeholder="Código de barras (opcional)">
        <input type="text" name="nombre" placeholder="Nombre del producto" required>
        <input type="text" name="categoria" placeholder="Categoría">
        <input type="text" name="imagen_url" placeholder="URL de la Foto del Producto (ej. Link de Google o Web)">
        <div style="display: flex; gap: 10px;">
            <input type="number" step="0.01" name="precio_compra" placeholder="Precio Compra ($)" required>
            <input type="number" step="0.01" name="precio_venta" placeholder="Precio Venta ($)" required>
            <input type="number" name="stock" placeholder="Stock Inicial" required>
        </div>
        <button type="submit">Guardar Producto</button>
    </form>

    <h2>Inventario Actual</h2>
    <table>
        <tr><th>Foto</th><th>Código</th><th>Nombre</th><th>P. Venta</th><th>Stock</th></tr>
        {% for p in productos %}
        <tr>
            <td><img src="{{ p[7] or 'https://cdn-icons-png.flaticon.com/512/3081/3081559.png' }}" width="40" height="40" style="object-fit:contain;"></td>
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
    cursor.execute('INSERT INTO productos (codigo, nombre, categoria, precio_compra, precio_venta, stock, imagen_url) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (request.form['codigo'], request.form['nombre'], request.form['categoria'], 
                    float(request.form['precio_compra']), float(request.form['precio_venta']), int(request.form['stock']), request.form['imagen_url']))
    conn.commit()
    conn.close()
    return redirect(url_for('inventario'))

# --- VENTANA 3: CONTROL DE FIADOS ---
@app.route('/fiados')
def fiados():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM fiados ORDER BY fecha DESC')
    lista_fiados = cursor.fetchall()
    conn.close()
    
    html = LAYOUT_HTML.replace('{% block content %}{% endblock %}', '''
    <h1>📋 Control de Fiados (Cuentas por Cobrar)</h1>
    
    <form action="/add_fiado" method="POST">
        <h3>Registrar Nuevo Fiado</h3>
        <input type="text" name="cliente" placeholder="Nombre y Apellido del Cliente" required>
        <input type="text" name="telefono" placeholder="Número de Teléfono">
        <input type="number" step="0.01" name="monto_deuda" placeholder="Monto Total Deuda ($)" required>
        <button type="submit" style="background: #dc3545;">Registrar Fiado</button>
    </form>

    <h2>Clientes con Deudas Pendientes</h2>
    <table>
        <tr><th>Cliente</th><th>Teléfono</th><th>Deuda ($)</th><th>Estado</th><th>Fecha</th></tr>
        <%- for f in lista_fiados %}
        <tr>
            <td><strong>{{ f[1] }}</strong></td>
            <td>{{ f[2] }}</td>
            <td>${{ "%.2f"|format(f[3]) }}</td>
            <td>{{ f[4] }}</td>
            <td><small>{{ f[5] }}</small></td>
        </tr>
        {% endfor %}
    </table>
    ''').replace('<%- for', '{% for')
    return render_template_string(html, active='fiados', lista_fiados=lista_fiados)

@app.route('/add_fiado', methods=['POST'])
def add_fiado():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO fiados (cliente, telefono, monto_deuda) VALUES (?, ?, ?)',
                   (request.form['cliente'], request.form['telefono'], float(request.form['monto_deuda'])))
    conn.commit()
    conn.close()
    return redirect(url_for('fiados'))

# --- VENTANA 4: CIERRE DE CAJA ---
@app.route('/resumen')
def resumen():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(total) FROM ventas WHERE DATE(fecha) = DATE('now', 'localtime')")
    total_dia = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha >= datetime('now', '-7 days')")
    total_sem = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(total) FROM ventas WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')")
    total_mes = cursor.fetchone()[0] or 0.0
    
    conn.close()
    
    html = LAYOUT_HTML.replace('{% block content %}{% endblock %}', f'''
    <h1>📊 Resumen y Cierre de Caja</h1>
    
    <div class="stats-grid">
        <div class="stat-card">
            <h3>Ventas de Hoy</h3>
            <p>${total_dia:.2f}</p>
        </div>
        <div class="stat-card">
            <h3>Ventas Semanales</h3>
            <p>${total_sem:.2f}</p>
        </div>
        <div class="stat-card">
            <h3>Ventas del Mes</h3>
            <p>${total_mes:.2f}</p>
        </div>
    </div>
    ''')
    return render_template_string(html, active='resumen')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)