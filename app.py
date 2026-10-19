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

# Ejecutar la creación de la base de datos al iniciar la app
init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    
    cursor.execute('''
        SELECT ventas.id, productos.nombre, ventas.cantidad, ventas.total, ventas.fecha 
        FROM ventas JOIN productos ON ventas.producto_id = productos.id 
        ORDER BY ventas.fecha DESC LIMIT 10
    ''')
    ventas = cursor.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control de Bodega</title>
        <style>
            * { box-sizing: border-box; }
            body { font-family: system-ui, -apple-system, sans-serif; margin: 10px; background: #f0f2f5; color: #1c1e21; }
            .container { max-width: 800px; margin: auto; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
            h1 { text-align: center; color: #1877f2; font-size: 1.6rem; }
            h2 { color: #333; font-size: 1.2rem; border-bottom: 2px solid #1877f2; padding-bottom: 5px; }
            .table-container { overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
            th, td { padding: 10px; border-bottom: 1px solid #e4e6eb; text-align: left; }
            th { background-color: #f7f8fa; color: #65676b; }
            form { margin-top: 15px; background: #f7f8fa; padding: 15px; border-radius: 8px; }
            input, select { padding: 10px; margin: 6px 0; width: 100%; border: 1px solid #ccc; border-radius: 6px; font-size: 0.95rem; }
            button { background: #42b72a; color: white; border: none; padding: 12px; width: 100%; cursor: pointer; border-radius: 6px; font-weight: bold; font-size: 1rem; margin-top: 8px; }
            button.venta { background: #ff7a00; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏬 Control de Bodega</h1>
            
            <h2>📦 Inventario Actual</h2>
            <div class="table-container">
                <table>
                    <tr><th>ID</th><th>Nombre</th><th>P. Venta</th><th>Stock</th></tr>
                    {% for p in productos %}
                    <tr>
                        <td>{{ p[0] }}</td>
                        <td><strong>{{ p[1] }}</strong></td>
                        <td>${{ "%.2f"|format(p[4]) }}</td>
                        <td><span style="color: {% if p[5] < 5 %}red{% else %}green{% endif %}">{{ p[5] }}</span></td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            
            <form action="/add_product" method="POST">
                <h3>➕ Agregar Producto</h3>
                <input type="text" name="nombre" placeholder="Nombre del producto" required>
                <input type="text" name="categoria" placeholder="Categoría">
                <input type="number" step="0.01" name="precio_compra" placeholder="Precio Compra ($)" required>
                <input type="number" step="0.01" name="precio_venta" placeholder="Precio Venta ($)" required>
                <input type="number" name="stock" placeholder="Cantidad Inicial" required>
                <button type="submit">Guardar Producto</button>
            </form>

            <form action="/registrar_venta" method="POST">
                <h3>🛒 Registrar Venta</h3>
                <select name="producto_id" required>
                    <option value="">Seleccione Producto...</option>
                    {% for p in productos %}
                    <option value="{{ p[0] }}">{{ p[1] }} (Disponibles: {{ p[5] }})</option>
                    {% endfor %}
                </select>
                <input type="number" name="cantidad" placeholder="Cantidad vendida" min="1" required>
                <button type="submit" class="venta">Registrar Venta</button>
            </form>
            
            <h2>📊 Últimas Ventas</h2>
            <div class="table-container">
                <table>
                    <tr><th>Producto</th><th>Cant.</th><th>Total</th><th>Fecha</th></tr>
                    {% for v in ventas %}
                    <tr>
                        <td>{{ v[1] }}</td>
                        <td>{{ v[2] }}</td>
                        <td>${{ "%.2f"|format(v[3]) }}</td>
                        <td><small>{{ v[4] }}</small></td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, productos=productos, ventas=ventas)

@app.route('/add_product', methods=['POST'])
def add_product():
    conn = sqlite3.connect('bodega.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO productos (nombre, categoria, precio_compra, precio_venta, stock) VALUES (?, ?, ?, ?, ?)',
                   (request.form['nombre'], request.form['categoria'], float(request.form['precio_compra']), float(request.form['precio_venta']), int(request.form['stock'])))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

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
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)