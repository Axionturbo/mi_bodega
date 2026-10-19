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
    
    # Tasa BCV por defecto
    cursor.execute('SELECT COUNT(*) FROM configuracion')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO configuracion (tasa_bcv) VALUES (784.66)')
        conn.commit()
        
    # Catálogo precargado masivo con productos populares en Venezuela
    cursor.execute('SELECT COUNT(*) FROM productos')
    if cursor.fetchone()[0] == 0:
        prods_venezuela = [
            ('7591014101016', 'Harina PAN 1kg', 'Víveres', 1.48, 80, 'https://resources.secom.shop/images/7591014101016/7591014101016-1.webp'),
            ('7591019000123', 'Mayonesa Mavesa 500g', 'Víveres', 2.39, 45, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZp89C5J2_fJk-7x8sQ3q5g6H8s9vQ2s8w1A&s'),
            ('7591104002345', 'Diablitos Underwood 115g', 'Embutidos', 1.85, 60, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT7vJ8s3Q9sQ2s8w1A&s'),
            ('7591193005678', 'Atún Margarita Lata 140g', 'Enlatados', 1.65, 50, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR8s3Q9sQ2s8w1A&s'),
            ('7591003001112', 'Arroz Primor 1kg', 'Víveres', 1.15, 90, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZp89C5J2_fJk-7x8sQ3q5g6H8s9vQ2s8w1A&s'),
            ('7591004002223', 'Aceite Mazeína 1L', 'Víveres', 2.80, 35, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZp89C5J2_fJk-7x8sQ3q5g6H8s9vQ2s8w1A&s'),
            ('7591005003334', 'Refresco Coca-Cola 2L', 'Bebidas', 2.50, 40, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZp89C5J2_fJk-7x8sQ3q5g6H8s9vQ2s8w1A&s'),
            ('7591006004445', 'Pasta Sindú 500g', 'Víveres', 0.95, 70, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZp89C5J2_fJk-7x8sQ3q5g6H8s9vQ2s8w1A&s')
        ]
        cursor.executemany('INSERT INTO productos (codigo, nombre, categoria, precio_venta, stock, imagen_url) VALUES (?, ?, ?, ?, ?, ?)', prods_venezuela)
        conn.commit()
        
    conn.close()

init_db()

# --- DISEÑO IDÉNTICO A PRECIOS AL DÍA ---
BASE_LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Precios Al Día - Venezuela</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #f4f7f6; color: #2d3748; }
        
        .floating-nav { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #1a202c; padding: 10px 25px; border-radius: 40px; display: flex; gap: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.25); z-index: 1000; }
        .nav-item { color: #a0aec0; text-decoration: none; display: flex; flex-direction: column; align-items: center; font-size: 0.75rem; font-weight: 500; transition: 0.2s; }
        .nav-item span { font-size: 1.2rem; margin-bottom: 2px; }
        .nav-item:hover, .nav-item.active { color: #48bb78; }

        .main-container { max-width: 1400px; margin: 0 auto; padding: 20px 20px 90px 20px; }
        
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .logo { font-size: 1.8rem; font-weight: bold; color: #1a202c; letter-spacing: -1px; }
        .logo span { color: #2f855a; }
        .bcv-box { display: flex; align-items: center; gap: 10px; background: #e2e8f0; padding: 6px 15px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; }

        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.04); border-top: 4px solid #48bb78; }
        .metric-card h3 { margin: 0 0 8px 0; font-size: 0.85rem; color: #718096; text-transform: uppercase; }
        .metric-card .value { font-size: 1.6rem; font-weight: bold; color: #1a202c; margin: 0; }
        .metric-card .sub { font-size: 0.85rem; color: #718096; margin-top: 5px; }

        .action-row { display: grid; grid-template-columns: 2fr 1fr; gap: 15px; margin-bottom: 20px; }
        .close-box { background: linear-gradient(135deg, #2f855a, #276749); color: white; padding: 20px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
        .expense-box { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }

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

    <div class="floating-nav">
        <a href="/" class="nav-item {% if active == 'inicio' %}active{% endif %}"><span>🏠</span>Inicio</a>
        <a href="/vender" class="nav-item {% if active == 'vender' %}active{% endif %}"><span>🛒</span>Vender</a>
        <a href="/inventario" class="nav-item {% if active == 'inventario' %}active{% endif %}"><span>📦</span>Inventario</a>
        <a href="/reportes" class="nav-item {% if active == 'reportes' %}active{% endif %}"><span>📊</span>Reportes</a>
    </div>
</body>
</html>
'''

# --- PANTALLA 1: INICIO ---
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
        <div class="bcv-box">
            <span>Tasa BCV: {tasa:.2f} Bs/$</span>
            <form action="/actualizar_tasa" method="POST" style="margin:0; display:inline;">
                <input type="number" step="0.01" name="nueva_tasa" value="{tasa}" style="width:90px; padding:4px;">
                <button type="submit" style="padding:4px 8px; background:#2f855a; color:white; border:none; border-radius:4px; cursor:pointer;">Actualizar</button>
            </form>
        </div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <h3>Ventas Totales</h3>
            <p class="value">${total_ventas:.2f}</p>
            <p class="sub">{cant_ventas} operaciones</p>
        </div>
        <div class="metric-card" style="border-top-color: #3182ce;">
            <h3>Ganancia Estimada</h3>
            <p class="value" style="color: #3182ce;">+${(total_ventas * 0.3):.2f}</p>
            <p class="sub">Margen de referencia</p>
        </div>
        <div class="metric-card" style="border-top-color: #d69e2e;">
            <h3>Productos Precargados</h3>
            <p class="value" style="color: #d69e2e;">Listos</p>
            <p class="sub">Con códigos de barra y fotos</p>
        </div>
    </div>

    <div class="action-row">
        <div class="close-box">
            <div>
                <h2 style="margin:0 0 5px 0;">Caja Rápida</h2>
                <p style="margin:0; opacity:0.9;">Venta con escáner y cálculo multimoneda</p>
            </div>
            <a href="/vender" style="background:white; color:#276749; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">Ir a Vender ➔</a>
        </div>
        <div class="expense-box">
            <div>
                <h3 style="margin:0 0 5px 0;">Inventario</h3>
                <p style="margin:0; color:#718096; font-size:0.9rem;">Catálogo activo</p>
            </div>
            <a href="/inventario" class="btn-green" style="text-decoration:none;">Ver stock</a>
        </div>
    </div>
    ''')
    return render_template_string(html, active='inicio')

@app.route('/actualizar_tasa', methods=['POST'])
def actualizar_tasa():
    nueva_tasa = float(request.form['nueva_tasa'])
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE configuracion SET tasa_bcv = ?', (nueva_tasa,))
    conn.commit()
    conn.close()
    return redirect(url_for('inicio'))

# --- PANTALLA 2: VENDER (CON ESCÁNER Y MULTIMONEDA) ---
@app.route('/vender')
def vender():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tasa_bcv FROM configuracion LIMIT 1')
    tasa = cursor.fetchone()[0]
    
    cursor.execute('SELECT id, codigo, nombre, precio_venta, stock, imagen_url FROM productos')
    productos = cursor.fetchall()
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', f'''
    <style>
        .pos-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }}
        .catalog {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }}
        .cart-panel {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between; }}
        
        .prod-grid-catalog {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 12px; max-height: 60vh; overflow-y: auto; margin-top: 15px; }}
        .prod-card {{ border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; text-align: center; cursor: pointer; background: #fff; transition: 0.15s; }}
        .prod-card:hover {{ border-color: #2f855a; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
        .prod-card img {{ width: 65px; height: 65px; object-fit: contain; margin-bottom: 5px; }}
        .prod-card .title {{ font-size: 0.75rem; font-weight: bold; color: #2d3748; height: 2.4em; overflow: hidden; }}
        .prod-card .price {{ color: #2f855a; font-weight: bold; font-size: 0.9rem; margin-top: 4px; }}
    </style>

    <div class="pos-grid">
        <div class="catalog">
            <h2 style="margin-top:0;">Punto de Venta (Escáner y Catálogo)</h2>
            <input type="text" id="busc" placeholder="🔍 Pase el escáner de barras o escriba el producto..." autofocus autocomplete="off" style="width:100%; padding:12px; border:1px solid #cbd5e0; border-radius:8px; font-size:1rem;">
            
            <div class="prod-grid-catalog" id="grid-productos">
                {{% for p in productos %}}
                <div class="prod-card" onclick="agregarAlCarrito('{{ p[2] }}', {{ p[3] }})" data-codigo="{{ p[1] }}" data-nombre="{{ p[2] }}">
                    <img src="{{ p[5] or 'https://cdn-icons-png.flaticon.com/512/3081/3081559.png' }}" alt="">
                    <div class="title">{{ p[2] }}</div>
                    <div class="price">${{ "%.2f"|format(p[3]) }}</div>
                    <small style="color:#718096;">Bs. {{ "%.2f"|format(p[3] * {tasa}) }}</small>
                </div>
                {{% endfor %}}
            </div>
        </div>

        <div class="cart-panel">
            <div>
                <h3 style="margin-top:0; border-bottom:2px solid #2f855a; padding-bottom:8px;">🛒 Cesta de Compra</h3>
                <div id="lista-cesta" style="min-height: 200px; max-height: 300px; overflow-y: auto; margin: 15px 0;">
                    <p style="color:#a0aec0; text-align:center; margin-top:40px;">Cesta vacía</p>
                </div>
            </div>

            <div>
                <div style="font-size:1.1rem; font-weight:bold; margin-bottom:5px; display:flex; justify-content:space-between;">
                    <span>TOTAL USD:</span>
                    <span id="total-usd" style="color:#2f855a;">$0.00</span>
                </div>
                <div style="font-size:0.95rem; color:#718096; margin-bottom:15px; display:flex; justify-content:space-between;">
                    <span>TOTAL BS:</span>
                    <span id="total-bs">Bs. 0.00</span>
                </div>
                
                <form action="/procesar_cobro" method="POST">
                    <input type="hidden" name="total_usd" id="input-total-usd" value="0">
                    <button type="submit" class="btn-green" style="width:100%; padding:14px; font-size:1rem;">COBRAR (LISTO)</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        const tasaBCV = {tasa};
        let totalUSD = 0;

        function agregarAlCarrito(nombre, precio) {{
            totalUSD += precio;
            let totalBs = totalUSD * tasaBCV;
            
            document.getElementById('total-usd').innerText = '$' + totalUSD.toFixed(2);
            document.getElementById('total-bs').innerText = 'Bs. ' + totalBs.toFixed(2);
            document.getElementById('input-total-usd').value = totalUSD.toFixed(2);
            
            let lista = document.getElementById('lista-cesta');
            if (lista.innerHTML.includes('Cesta vacía')) {{ lista.innerHTML = ''; }}
            lista.innerHTML += `<div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.9rem;"><span>${{nombre}}</span> <b>${{precio.toFixed(2)}} USD</b></div>`;
        }}

        // Buscador y lector de códigos de barras en tiempo real
        const busc = document.getElementById('busc');
        const cards = document.querySelectorAll('.prod-card');

        busc.addEventListener('input', function() {{
            const texto = busc.value.toLowerCase();
            cards.forEach(card => {{
                const cod = card.getAttribute('data-codigo').toLowerCase();
                const nom = card.getAttribute('data-nombre').toLowerCase();
                if (cod.includes(texto) || nom.includes(texto)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }});
    </script>
    ''')
    return render_template_string(html, active='vender', productos=productos, tasa=tasa)

@app.route('/procesar_cobro', methods=['POST'])
def procesar_cobro():
    total_usd = float(request.form['total_usd'])
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tasa_bcv FROM configuracion LIMIT 1')
    tasa = cursor.fetchone()[0]
    total_bs = total_usd * tasa
    
    cursor.execute('INSERT INTO ventas (total_usd, total_bs, metodo_pago, operador) VALUES (?, ?, ?, ?)',
                   (total_usd, total_bs, 'Efectivo/Multimoneda', 'Administrador'))
    conn.commit()
    conn.close()
    return redirect(url_for('vender'))

# --- PANTALLA 3: INVENTARIO ---
@app.route('/inventario')
def inventario():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', '''
    <div style="background:white; padding:20px; border-radius:12px;">
        <h2 style="margin-top:0;">Catálogo e Inventario Precargado</h2>
        <table>
            <tr><th>Imagen</th><th>Código de Barras</th><th>Producto</th><th>Categoría</th><th>Precio Venta</th><th>Stock</th></tr>
            {% for p in productos %}
            <tr>
                <td><img src="{{ p[6] or 'https://cdn-icons-png.flaticon.com/512/3081/3081559.png' }}" width="40" height="40" style="object-fit:contain;"></td>
                <td><code>{{ p[1] }}</code></td>
                <td><b>{{ p[2] }}</b></td>
                <td>{{ p[3] }}</td>
                <td>${{ "%.2f"|format(p[4]) }}</td>
                <td>{{ p[5] }} unds</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    ''')
    return render_template_string(html, active='inventario', productos=productos)

# --- PANTALLA 4: REPORTES ---
@app.route('/reportes')
def reportes():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(total_usd), SUM(total_bs), COUNT(*) FROM ventas')
    res = cursor.fetchone()
    total_usd = res[0] or 0.0
    total_bs = res[1] or 0.0
    count = res[2] or 0
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', f'''
    <div style="background:white; padding:20px; border-radius:12px;">
        <h2 style="margin-top:0;">Reportes y Cierre</h2>
        <div style="display:flex; gap:20px; margin-top:20px;">
            <div style="background:#f7fafc; padding:20px; border-radius:8px; flex:1;">
                <h3>Total en Dólares ($)</h3>
                <p style="font-size:1.8rem; color:#2f855a; font-weight:bold; margin:0;">${total_usd:.2f}</p>
            </div>
            <div style="background:#f7fafc; padding:20px; border-radius:8px; flex:1;">
                <h3>Total en Bolívares (Bs)</h3>
                <p style="font-size:1.8rem; color:#3182ce; font-weight:bold; margin:0;">Bs. {total_bs:,.2f}</p>
            </div>
            <div style="background:#f7fafc; padding:20px; border-radius:8px; flex:1;">
                <h3>Ventas Realizadas</h3>
                <p style="font-size:1.8rem; color:#d69e2e; font-weight:bold; margin:0;">{count}</p>
            </div>
        </div>
    </div>
    ''')
    return render_template_string(html, active='reportes')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)