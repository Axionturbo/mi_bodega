from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    
    # 1. Configuración (Tasa BCV)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tasa_bcv REAL
        )
    ''')
    
    # 2. CATÁLOGO MAESTRO NACIONAL (Con enlaces de imágenes seguros y estables)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalogo_maestro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT NOT NULL,
            categoria TEXT,
            imagen_url TEXT
        )
    ''')
    
    # 3. MI INVENTARIO REAL (Empieza vacío)
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
    
    # 4. VENTAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_usd REAL,
            total_bs REAL,
            metodo_pago TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    # Configurar Tasa BCV inicial
    cursor.execute('SELECT COUNT(*) FROM configuracion')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO configuracion (tasa_bcv) VALUES (784.66)')
        conn.commit()
        
    # Precargar el Catálogo Maestro con enlaces de imágenes seguros
    cursor.execute('SELECT COUNT(*) FROM catalogo_maestro')
    if cursor.fetchone()[0] == 0:
        base_datos_nacional = [
            ('7591014101016', 'Harina PAN 1kg', 'Víveres', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&auto=format&fit=crop&q=60'),
            ('7591019000123', 'Mayonesa Mavesa 500g', 'Salsas', 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&auto=format&fit=crop&q=60'),
            ('7591104002345', 'Diablitos Underwood 115g', 'Enlatados', 'https://images.unsplash.com/photo-1544025162-d76694265947?w=300&auto=format&fit=crop&q=60'),
            ('7591193005678', 'Atún Margarita Lata 140g', 'Enlatados', 'https://images.unsplash.com/photo-1544025162-d76694265947?w=300&auto=format&fit=crop&q=60'),
            ('7591003001112', 'Arroz Primor 1kg', 'Víveres', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&auto=format&fit=crop&q=60'),
            ('7591004002223', 'Aceite Mazeína 1L', 'Aceites', 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&auto=format&fit=crop&q=60'),
            ('7591005003334', 'Refresco Coca-Cola 2L', 'Bebidas', 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=300&auto=format&fit=crop&q=60'),
            ('7591006004445', 'Pasta Sindú 500g', 'Pastas', 'https://images.unsplash.com/photo-1621996346565-e3d5d6281298?w=300&auto=format&fit=crop&q=60'),
            ('7591007005556', 'Café Fama de América 250g', 'Café', 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&auto=format&fit=crop&q=60'),
            ('7591008006667', 'Margarina Mavesa 500g', 'Lácteos', 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&auto=format&fit=crop&q=60'),
            ('7591009007778', 'Azúcar Refinada 1kg', 'Víveres', 'https://images.unsplash.com/photo-1581404476143-3fb1d6d12059?w=300&auto=format&fit=crop&q=60'),
            ('7591010008889', 'Caraotas Negras 1kg', 'Granos', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&auto=format&fit=crop&q=60'),
            ('7591011009990', 'Leche en Polvo La Campiña 400g', 'Lácteos', 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&auto=format&fit=crop&q=60'),
            ('7591012010112', 'Salsa de Tomate Heinz 397g', 'Salsas', 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&auto=format&fit=crop&q=60'),
            ('7591013012223', 'Harina de Trigo Robin Hood 1kg', 'Víveres', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&auto=format&fit=crop&q=60'),
            ('7591014013334', 'Galletas Maria Puig 200g', 'Golosinas', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&auto=format&fit=crop&q=60'),
            ('7591015014445', 'Toddy Chocolates 400g', 'Bebidas', 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=300&auto=format&fit=crop&q=60'),
            ('7591016015556', 'Avena Quaker 400g', 'Cereales', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&auto=format&fit=crop&q=60'),
            ('7591017016667', 'Detergente Las Llaves 1kg', 'Limpieza', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&auto=format&fit=crop&q=60'),
            ('7591018017778', 'Jabón de Baño Las Llaves Azul', 'Aseo Personal', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&auto=format&fit=crop&q=60'),
            ('7591019018889', 'Papel Higiénico Scott 4 Rollos', 'Aseo Personal', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&auto=format&fit=crop&q=60'),
            ('7591020019990', 'Cloro en Gel 1L', 'Limpieza', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&auto=format&fit=crop&q=60'),
            ('7591021020111', 'Sopita Maggi Pollo x2', 'Víveres', 'https://images.unsplash.com/photo-1544025162-d76694265947?w=300&auto=format&fit=crop&q=60'),
            ('7591022021222', 'Sal La Fina 500g', 'Víveres', 'https://images.unsplash.com/photo-1581404476143-3fb1d6d12059?w=300&auto=format&fit=crop&q=60'),
            ('7591023022333', 'Maltín Polar 330ml', 'Bebidas', 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=300&auto=format&fit=crop&q=60'),
            ('7591024023444', 'Cerveza Polar Pilsen 330ml', 'Bebidas Alcohólicas', 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=300&auto=format&fit=crop&q=60'),
            ('7591025024555', 'Ron Cacique 1L', 'Bebidas Alcohólicas', 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=300&auto=format&fit=crop&q=60'),
            ('7591026025666', 'Chocolates Savoy Toronto', 'Golosinas', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&auto=format&fit=crop&q=60'),
            ('7591027026777', 'Galletas Susy Savoy', 'Golosinas', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&auto=format&fit=crop&q=60'),
            ('7591028027888', 'Sardinas en Lata Margarita', 'Enlatados', 'https://images.unsplash.com/photo-1544025162-d76694265947?w=300&auto=format&fit=crop&q=60')
        ]
        cursor.executemany('INSERT INTO catalogo_maestro (codigo, nombre, categoria, imagen_url) VALUES (?, ?, ?, ?)', base_datos_nacional)
        conn.commit()
        
    conn.close()

init_db()

BASE_LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Precios Al Día - Mi Bodega</title>
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

        .btn-green { background: #2f855a; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .btn-green:hover { background: #276749; }
        
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #edf2f7; font-size: 0.9rem; }
        th { background: #f7fafc; color: #4a5568; font-weight: 600; }
        
        input, select { padding: 10px; margin: 5px 0; border: 1px solid #cbd5e0; border-radius: 6px; width: 100%; }
    </style>
</head>
<body>
    <div class="main-container">
        {% block content %}{% endblock %}
    </div>

    <div class="floating-nav">
        <a href="/" class="nav-item {% if active == 'inicio' %}active{% endif %}"><span>🏠</span>Inicio</a>
        <a href="/vender" class="nav-item {% if active == 'vender' %}active{% endif %}"><span>🛒</span>Vender</a>
        <a href="/inventario" class="nav-item {% if active == 'inventario' %}active{% endif %}"><span>📦</span>Mi Inventario</a>
        <a href="/reportes" class="nav-item {% if active == 'reportes' %}active{% endif %}"><span>📊</span>Reportes</a>
    </div>
</body>
</html>
'''

@app.route('/')
def inicio():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tasa_bcv FROM configuracion LIMIT 1')
    tasa = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM productos')
    cant_inv = cursor.fetchone()[0]
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', f'''
    <div class="header">
        <div class="logo">Precios<span>AlDía</span></div>
        <div class="bcv-box">Tasa BCV: {tasa:.2f} Bs/$</div>
    </div>
    <div style="background:white; padding:30px; border-radius:12px; text-align:center;">
        <h1 style="color:#2f855a; margin-top:0;">Mi Sistema de Bodega</h1>
        <p style="color:#718096;">Tienes <b>{cant_inv} productos</b> en tu inventario activo.</p>
        <div style="display:flex; justify-content:center; gap:15px; margin-top:20px;">
            <a href="/inventario" class="btn-green" style="text-decoration:none;">➕ Cargar Productos</a>
            <a href="/vender" style="background:#3182ce; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">🛒 Abrir Caja POS</a>
        </div>
    </div>
    ''')
    return render_template_string(html, active='inicio')

@app.route('/api/buscar_maestro/<codigo>')
def buscar_maestro(codigo):
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, categoria, imagen_url FROM catalogo_maestro WHERE codigo = ?', (codigo,))
    p = cursor.fetchone()
    conn.close()
    if p:
        return jsonify({'encontrado': True, 'nombre': p[0], 'categoria': p[1], 'imagen_url': p[2]})
    return jsonify({'encontrado': False})

@app.route('/inventario')
def inventario():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', '''
    <div style="background:white; padding:20px; border-radius:12px; margin-bottom:20px;">
        <h2 style="margin-top:0; color:#2f855a;">➕ Registrar Producto en Mi Inventario</h2>
        <p style="color:#718096; font-size:0.9rem;">Escanea o escribe el código de barras. Las imágenes cargarán de forma segura y automática.</p>
        
        <form action="/add_producto" method="POST" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:10px;">
            <div>
                <label>Código de Barras:</label>
                <input type="text" id="cod_input" name="codigo" placeholder="Ej: 7591014101016" autofocus required oninput="consultarMaestro()">
            </div>
            <div>
                <label>Nombre del Producto:</label>
                <input type="text" id="nom_input" name="nombre" placeholder="Nombre" required>
            </div>
            <div>
                <label>Categoría:</label>
                <input type="text" id="cat_input" name="categoria" placeholder="Categoría">
            </div>
            <div>
                <label>Precio Venta ($):</label>
                <input type="number" step="0.01" name="precio_venta" placeholder="Ej: 1.50" required>
            </div>
            <div>
                <label>Cantidad (Stock):</label>
                <input type="number" name="stock" placeholder="Cantidad" required>
            </div>
            <input type="hidden" id="img_input" name="imagen_url">
            <div style="grid-column: 1 / -1;">
                <button type="submit" class="btn-green" style="width:100%; margin-top:10px;">Guardar en Mi Inventario</button>
            </div>
        </form>
    </div>

    <script>
        function consultarMaestro() {
            let cod = document.getElementById('cod_input').value.trim();
            if(cod.length >= 7) {
                fetch('/api/buscar_maestro/' + cod)
                .then(r => r.json())
                .then(data => {
                    if(data.encontrado) {
                        document.getElementById('nom_input').value = data.nombre;
                        document.getElementById('cat_input').value = data.categoria;
                        document.getElementById('img_input').value = data.imagen_url;
                    }
                });
            }
        }
    </script>

    <div style="background:white; padding:20px; border-radius:12px;">
        <h2 style="margin-top:0;">Mi Inventario Actual</h2>
        {% if productos|length == 0 %}
            <p style="color:#a0aec0; text-align:center; padding:30px;">Tu inventario está vacío. Escanea o registra tu primer producto arriba.</p>
        {% else %}
            <table>
                <tr><th>Foto</th><th>Código</th><th>Producto</th><th>Categoría</th><th>Precio Venta</th><th>Stock</th></tr>
                {% for p in productos %}
                <tr>
                    <td><img src="{{ p[6] or 'https://cdn-icons-png.flaticon.com/512/3081/3081559.png' }}" width="40" height="40" style="object-fit:contain; border-radius:4px;"></td>
                    <td><code>{{ p[1] }}</code></td>
                    <td><b>{{ p[2] }}</b></td>
                    <td>{{ p[3] }}</td>
                    <td>${{ "%.2f"|format(p[4]) }}</td>
                    <td><b>{{ p[5] }} unds</b></td>
                </tr>
                {% endfor %}
            </table>
        {% endif %}
    </div>
    ''')
    return render_template_string(html, active='inventario', productos=productos)

@app.route('/add_producto', methods=['POST'])
def add_producto():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO productos (codigo, nombre, categoria, precio_venta, stock, imagen_url)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET stock = stock + excluded.stock, precio_venta = excluded.precio_venta
    ''', (request.form['codigo'], request.form['nombre'], request.form['categoria'],
          float(request.form['precio_venta']), int(request.form['stock']), request.form['imagen_url']))
    conn.commit()
    conn.close()
    return redirect(url_for('inventario'))

@app.route('/vender')
def vender():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos WHERE stock > 0')
    prods = cursor.fetchall()
    conn.close()
    
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', '''
    <div style="background:white; padding:20px; border-radius:12px;">
        <h2>🛒 POS Caja de Ventas</h2>
        {% if prods|length == 0 %}
            <p style="color:#a0aec0; text-align:center; padding:30px;">Aún no tienes productos en tu inventario con stock disponible.</p>
        {% else %}
            <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap:12px;">
                {% for p in prods %}
                <div style="border:1px solid #e2e8f0; padding:10px; border-radius:8px; text-align:center;">
                    <img src="{{ p[6] or 'https://cdn-icons-png.flaticon.com/512/3081/3081559.png' }}" width="60" height="60" style="object-fit:contain;">
                    <div style="font-size:0.8rem; font-weight:bold; height:2.4em; overflow:hidden;">{{ p[2] }}</div>
                    <div style="color:#2f855a; font-weight:bold;">${{ "%.2f"|format(p[4]) }}</div>
                    <small style="color:#718096;">Stock: {{ p[5] }}</small>
                </div>
                {% endfor %}
            </div>
        {% endif %}
    </div>
    ''')
    return render_template_string(html, active='vender', prods=prods)

@app.route('/reportes')
def reportes():
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)