from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="abarrotes_db"
    )

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s AND contraseña = %s", (usuario, contraseña))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['usuario'] = usuario
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('dashboard.html', usuario=session['usuario'])

@app.route('/productos')
def productos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return render_template('productos.html', productos=productos)

@app.route('/productos/agregar', methods=['POST'])
def agregar_producto():
    nombre = request.form['nombre']
    precio = request.form['precio']
    stock = request.form['stock']
    codigo = request.form['codigo']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE codigo = %s", (codigo,))
    if cursor.fetchone():
        flash('Código de producto ya existente.')
        conn.close()
        return redirect('/productos')

    cursor.execute("INSERT INTO productos (nombre, precio, stock, codigo) VALUES (%s, %s, %s, %s)",
                   (nombre, precio, stock, codigo))
    conn.commit()
    conn.close()
    return redirect('/productos')

@app.route('/productos/eliminar/<int:id>')
def eliminar_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect('/productos')

@app.route('/ventas')
def ventas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, fecha, total FROM ventas")
    ventas = cursor.fetchall()
    conn.close()
    return render_template('ventas.html', ventas=ventas)

@app.route('/ventas/nueva', methods=['GET', 'POST'])
def nueva_venta():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    if request.method == 'POST':
        total = 0
        productos_seleccionados = request.form.getlist('productos')
        cantidades = request.form.getlist('cantidades')

        productos_venta = []
        for i in range(len(productos_seleccionados)):
            id_producto = int(productos_seleccionados[i])
            cantidad = int(cantidades[i])
            cursor.execute("SELECT precio, stock FROM productos WHERE id = %s", (id_producto,))
            result = cursor.fetchone()
            if not result:
                flash("Producto no encontrado")
                return redirect('/ventas/nueva')
            precio, stock_actual = result
            if cantidad > stock_actual:
                flash("Cantidad mayor al stock disponible")
                return redirect('/ventas/nueva')
            total += precio * cantidad
            productos_venta.append((id_producto, cantidad))

        cursor.execute("INSERT INTO ventas (fecha, total) VALUES (NOW(), %s)", (total,))
        venta_id = cursor.lastrowid

        for id_producto, cantidad in productos_venta:
            cursor.execute("INSERT INTO detalle_ventas (id_venta, id_producto, cantidad) VALUES (%s, %s, %s)",
                           (venta_id, id_producto, cantidad))
            cursor.execute("UPDATE productos SET stock = stock - %s WHERE id = %s", (cantidad, id_producto))

        conn.commit()
        conn.close()
        return redirect('/ventas')

    conn.close()
    return render_template('nueva_venta.html', productos=productos)

if __name__ == '__main__':
    app.run(debug=True)