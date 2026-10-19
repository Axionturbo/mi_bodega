from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tasa_bcv REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT NOT NULL,
            categoria TEXT,
            precio_venta REAL,
            stock INTEGER,
            imagen_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_usd REAL,
            total_bs REAL,
            metodo_pago TEXT,
            operador TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    # Configurar tasa BCV inicial si no existe
    cursor.execute('SELECT COUNT(*) FROM configuracion')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO configuracion (tasa_bcv) VALUES (784.66)')
        conn.commit()
        
    # Productos de ejemplo idénticos a la referencia
    cursor.execute('SELECT COUNT(*) FROM productos')
    if cursor.fetchone()[0] == 0:
        prods = [
            ('7591014', 'Harina PAN 1kg', 'Víveres', 1.48, 87, 'https://resources.secom.shop/images/7591014101016/7591014101016-1.webp'),
            ('7591015', 'Mayonesa Mavesa 500g', 'Víveres', 2.39, 37, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZp89C5J2_fJk-7x8sQ3q5g6H8s9vQ2s8w1A&s'),
            ('7591016', 'Salsa de Tomate Pampero 397g', 'Víveres', 1.32, 109, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT7vJ8s3Q9sQ2s8w1A&s'),
            ('7591017', 'Jamon De Pierna La Montserratina 200g', 'Charcutería', 2.26, 63, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR8s3Q9sQ2s8w1A&s'),
            ('7591018', 'Detergent Ariel regular 1kg', 'Limpieza', 1.70, 54, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZp89C5J2_fJk-7x8sQ3q5g6H8s9vQ2s8w1A&s'),
            ('7591019', '7up 2l', 'Bebidas', 3.57, 89, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZp89C5J2_fJk-7x8sQ3q5g6H8s9vQ2s8w1A&s')
        ]
        cursor.executemany('INSERT INTO productos (codigo, nombre, categoria, precio_venta, stock, imagen_url) VALUES (?, ?, ?, ?, ?, ?)', prods)
        conn.commit()
        
    conn.close()

init_db()

# --- ESTILO VISUAL IDÉNTICO A PRECIOS AL DÍA ---
BASE_LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Precios Al Día</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #f4f7f6; color: #2d3748; }
        
        /* BARRA NAVEGACIÓN INFERIOR FLOTANTE */
        .floating-nav { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #1a202c; padding: 10px 20px; border-radius: 40px; display: flex; gap: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); z-index: 1000; }
        .nav-item { color: #a0aec0; text-decoration: none; display: flex; flex-direction: column; align-items: center; font-size: 0.75rem; font-weight: 500; transition: 0.2s; }
        .nav-item span { font-size: 1.2rem; margin-bottom: 2px; }
        .nav-item:hover, .nav-item.active { color: #48bb78; }

        .main-container { max-width: 1400px; margin: 0 auto; padding: 20px 20px 90px 20px; }
        
        /* HEADER */
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .logo { font-size: 1.8rem; font-weight: bold; color: #1a202c; letter-spacing: -1px; }
        .logo span { color: #2b6cb0; }
        .bcv-badge { background: #e2e8f0; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; color: #2d3748; }

        /* TARJETAS DE MÉTRICAS */
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.04); border-top: 4px solid #48bb78; }
        .metric-card h3 { margin: 0 0 8px 0; font-size: 0.85rem; color: #718096; text-transform: uppercase; }
        .metric-card .value { font-size: 1.6rem; font-weight: bold; color: #1a202c; margin: 0; }
        .metric-card .sub { font-size: 0.85rem; color: #718096; margin-top: 5px; }

        /* BOTONES DE ACCIÓN */
        .action-row { display: grid; grid-template-columns: 2fr 1fr; gap: 15px; margin-bottom: 20px; }
        .close-box { background: linear-gradient(135deg, #dd6b20, #c05621); color: white; padding: 20px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
        .expense-box { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }

        /* ESTILOS GENERALES */
        .btn-green { background: #2f855a; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .btn-green:hover { background: #276749; }
        
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #edf2f7; font-size: 0.9rem; }
        th { background: #f7fafc; color: #4a5568; font-weight: 600; }
    </style>
</head>
<body>
    <div class="main-container">
        {% block content %}{% endblock %}
    </div>

    <!-- BARRA NAVEGACIÓN FLOTANTE -->
    <div class="floating-nav">
        <a href="/" class="nav-item {% if active == 'inicio' %}active{% endif %}"><span>🏠</span>Inicio</a>
        <a href="/vender" class="nav-item {% if active == 'vender' %}active{% endif %}"><span>🛒</span>Vender</a>
        <a href="/inventario" class="nav-item {% if active == 'inventario' %}active{% endif %}"><span>📦</span>Inventario</a>
        <a href="/reportes" class="nav-item {% if active == 'reportes' %}active{% endif %}"><span>📊</span>Reportes</a>
    </div>
</body>
</html>
'''

# --- PANTALLA 1: SELECCIÓN DE OPERADOR / INICIO ---
@app.route('/')
def inicio():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tasa_bcv FROM configuracion LIMIT 1')
    tasa = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(total_usd), COUNT(*) FROM ventas')
    res = cursor.fetchone()
    total_ventas = res[0] or 0.0
    cant_ventas = res[1] or 0
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', f'''
    <div class="header">
        <div class="logo">Precios<span>AlDía</span></div>
        <div class="bcv-badge">Tasa BCV: {tasa:.2f} Bs/$</div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <h3>Ventas Totales</h3>
            <p class="value">${total_ventas:.2f}</p>
            <p class="sub">{cant_ventas} operaciones registradas</p>
        </div>
        <div class="metric-card" style="border-top-color: #3182ce;">
            <h3>Ganancia Estimada</h3>
            <p class="value" style="color: #3182ce;">+${(total_ventas * 0.3):.2f}</p>
            <p class="sub">Margen promedio 30%</p>
        </div>
        <div class="metric-card" style="border-top-color: #d69e2e;">
            <h3>Tasa Activa</h3>
            <p class="value" style="color: #d69e2e;">{tasa:.2f} Bs/$</p>
            <p class="sub">Actualizada hoy</p>
        </div>
    </div>

    <div class="action-row">
        <div class="close-box">
            <div>
                <h2 style="margin:0 0 5px 0;">Caja Operativa</h2>
                <p style="margin:0; opacity:0.9;">Control diario de ingresos y cierres</p>
            </div>
            <a href="/vender" style="background:white; color:#c05621; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">Ir a Vender ➔</a>
        </div>
        <div class="expense-box">
            <div>
                <h3 style="margin:0 0 5px 0;">Inventario</h3>
                <p style="margin:0; color:#718096; font-size:0.9rem;">Productos y stock</p>
            </div>
            <a href="/inventario" class="btn-green" style="text-decoration:none;">Gestionar</a>
        </div>
    </div>
    ''')
    return render_template_string(html, active='inicio')

# --- PANTALLA 2: PUNTO DE VENTA (VENDER) CON CARRITO LATERAL ---
@app.route('/vender')
def vender():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tasa_bcv FROM configuracion LIMIT 1')
    tasa = cursor.fetchone()[0]
    
    cursor.execute('SELECT id, nombre, precio_venta, stock, imagen_url FROM productos')
    productos = cursor.fetchall()
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', '''
    <style>
        .pos-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .catalog { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
        .cart-panel { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between; height: 75vh; }
        
        .prod-grid-catalog { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; max-height: 65vh; overflow-y: auto; margin-top: 15px; }
        .prod-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; text-align: center; cursor: pointer; background: #fff; transition: 0.15s; }
        .prod-card:hover { border-color: #3182ce; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        .prod-card img { width: 70px; height: 70px; object-fit: contain; margin-bottom: 5px; }
        .prod-card .title { font-size: 0.8rem; font-weight: bold; color: #2d3748; height: 2.4em; overflow: hidden; }
        .prod-card .price { color: #2f855a; font-weight: bold; font-size: 0.95rem; margin-top: 4px; }
        
        .cart-items { flex-grow: 1; overflow-y: auto; margin: 15px 0; border-top: 1px solid #edf2f7; border-bottom: 1px solid #edf2f7; padding: 10px 0; }
        .cart-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 0.9rem; }
    </style>

    <div class="pos-grid">
        <div class="catalog">
            <h2 style="margin-top:0;">Catálogo de Ventas</h2>
            <input type="text" id="busc" placeholder="🔍 Buscar producto..." style="width:100%; padding:12px; border:1px solid #cbd5e0; border-radius:8px; font-size:1rem;">
            
            <div class="prod-grid-catalog">
                {% for p in productos %}
                <div class="prod-card" onclick="agregarAlCarrito('{{ p[1] }}', {{ p[2] }})">
                    <img src="{{ p[4] or 'https://cdn-icons-png.flaticon.com/512/3081/3081559.png' }}" alt="">
                    <div class="title">{{ p[1] }}</div>
                    <div class="price">${{ "%.2f"|format(p[2]) }}</div>
                    <small style="color:#718096;">Stock: {{ p[3] }}</small>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="cart-panel">
            <div>
                <h3 style="margin-top:0; border-bottom:2px solid #2f855a; padding-bottom:8px;">🛒 Cesta de Compra</h3>
                <div class="cart-items" id="lista-cesta">
                    <p style="color:#a0aec0; text-align:center; margin-top:30px;">Cesta vacía</p>
                </div>
            </div>

            <div>
                <div style="display:flex; justify-content:space-between; font-size:1.2rem; font-weight:bold; margin-bottom:15px;">
                    <span>TOTAL:</span>
                    <span id="total-cesta" style="color:#2f855a;">$0.00</span>
                </div>
                <form action="/procesar_cobro" method="POST" id="form-cobro">
                    <input type="hidden" name="total_usd" id="input-total" value="0">
                    <button type="submit" class="btn-green" style="width:100%; padding:14px; font-size:1rem;">COBRAR (LISTO)</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        let total = 0;
        function agregarAlCarrito(nombre, precio) {
            total += precio;
            document.getElementById('total-cesta').innerText = '$' + total.toFixed(2);
            document.getElementById('input-total').value = total.toFixed(2);
            
            let lista = document.getElementById('lista-cesta');
            if (lista.innerHTML.includes('Cesta vacía')) { lista.innerHTML = ''; }
            lista.innerHTML += `<div class="cart-item"><span>${nombre}</span> <b>$${precio.toFixed(2)}</b></div>`;
        }
    </script>
    ''')
    return render_template_string(html, active='vender')

@app.route('/procesar_cobro', methods=['POST'])
def procesar_cobro():
    total_usd = float(request.form['total_usd'])
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tasa_bcv FROM configuracion LIMIT 1')
    tasa = cursor.fetchone()[0]
    total_bs = total_usd * tasa
    
    cursor.execute('INSERT INTO ventas (total_usd, total_bs, metodo_pago, operador) VALUES (?, ?, ?, ?)',
                   (total_usd, total_bs, 'Efectivo USD', 'Administrador'))
    conn.commit()
    conn.close()
    return redirect(url_for('vender'))

# --- PANTALLA 3: INVENTARIO VISUAL ---
@app.route('/inventario')
def inventario():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', '''
    <div style="background:white; padding:20px; border-radius:12px;">
        <h2 style="margin-top:0;">Control de Inventario</h2>
        <table>
            <tr><th>Imagen</th><th>Código</th><th>Nombre</th><th>Precio Venta</th><th>Stock</th></tr>
            {% for p in productos %}
            <tr>
                <td><img src="{{ p[6] or 'https://cdn-icons-png.flaticon.com/512/3081/3081559.png' }}" width="40" height="40" style="object-fit:contain;"></td>
                <td>{{ p[1] }}</td>
                <td><b>{{ p[2] }}</b></td>
                <td>${{ "%.2f"|format(p[4]) }}</td>
                <td>{{ p[5] }} unds</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    ''')
    return render_template_string(html, active='inventario')

# --- PANTALLA 4: REPORTES Y MÉTRICAS ---
@app.route('/reportes')
def reportes():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(total_usd), COUNT(*) FROM ventas')
    res = cursor.fetchone()
    total = res[0] or 0.0
    count = res[1] or 0
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', f'''
    <div style="background:white; padding:20px; border-radius:12px;">
        <h2 style="margin-top:0;">Reportes y Métricas</h2>
        <div style="display:flex; gap:20px; margin-top:20px;">
            <div style="background:#f7fafc; padding:20px; border-radius:8px; flex:1;">
                <h3>Total Ingresos</h3>
                <p style="font-size:1.8rem; color:#2f855a; font-weight:bold; margin:0;">${total:.2f}</p>
            </div>
            <div style="background:#f7fafc; padding:20px; border-radius:8px; flex:1;">
                <h3>Ventas Realizadas</h3>
                <p style="font-size:1.8rem; color:#3182ce; font-weight:bold; margin:0;">{count}</p>
            </div>
        </div>
    </div>
    ''')
    return render_template_string(html, active='reportes')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)