from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'shopkey2026'

def get_db():
    conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS tblUsers (
        UserID SERIAL PRIMARY KEY,
        Username TEXT,
        Password TEXT,
        Role TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tblProducts (
        ProductID SERIAL PRIMARY KEY,
        ProductName TEXT,
        Category TEXT,
        Price REAL,
        StockQty INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tblSales (
        SaleID SERIAL PRIMARY KEY,
        SaleDate TEXT,
        TotalAmount REAL,
        PaymentMethod TEXT,
        ServedBy TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tblSaleItems (
        SaleItemID SERIAL PRIMARY KEY,
        SaleID INTEGER,
        ProductID INTEGER,
        Quantity INTEGER,
        UnitPrice REAL
    )''')

    # Default users
    c.execute("SELECT COUNT(*) FROM tblUsers")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO tblUsers (Username, Password, Role) VALUES ('admin', 'admin123', 'Admin')")
        c.execute("INSERT INTO tblUsers (Username, Password, Role) VALUES ('staff', 'staff123', 'Staff')")

    # Sample products
    c.execute("SELECT COUNT(*) FROM tblProducts")
    if c.fetchone()[0] == 0:
        products = [
            ('Bread', 'Bakery', 1.20, 50),
            ('Milk', 'Dairy', 0.95, 80),
            ('Sugar', 'Groceries', 2.50, 30),
            ('Cooking Oil', 'Groceries', 3.80, 25),
            ('Rice', 'Groceries', 4.00, 40),
            ('Soap', 'Toiletries', 0.75, 60),
        ]
        c.executemany("INSERT INTO tblProducts (ProductName, Category, Price, StockQty) VALUES (%s,%s,%s,%s)", products)

    conn.commit()
    conn.close()

# ── LOGIN ──
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("SELECT * FROM tblUsers WHERE Username=%s AND Password=%s", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('menu'))
        else:
            flash('Wrong username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── MAIN MENU ──
@app.route('/menu')
def menu():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html', role=session['role'], user=session['user'])

# ── PRODUCTS ──
@app.route('/products')
def products():
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM tblProducts ORDER BY Category, ProductName")
    items = c.fetchall()
    conn.close()
    return render_template('products.html', products=items)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO tblProducts (ProductName, Category, Price, StockQty) VALUES (%s,%s,%s,%s)", (name, category, price, stock))
        conn.commit()
        conn.close()
        flash('Product added!')
        return redirect(url_for('products'))
    return render_template('add_product.html')

@app.route('/products/edit/<int:pid>', methods=['GET', 'POST'])
def edit_product(pid):
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        c.execute("UPDATE tblProducts SET ProductName=%s, Category=%s, Price=%s, StockQty=%s WHERE ProductID=%s", (name, category, price, stock, pid))
        conn.commit()
        conn.close()
        flash('Product updated!')
        return redirect(url_for('products'))
    c.execute("SELECT * FROM tblProducts WHERE ProductID=%s", (pid,))
    product = c.fetchone()
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:pid>')
def delete_product(pid):
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM tblProducts WHERE ProductID=%s", (pid,))
    conn.commit()
    conn.close()
    flash('Product deleted.')
    return redirect(url_for('products'))

# ── NEW SALE ──
@app.route('/sale', methods=['GET', 'POST'])
def new_sale():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        payment = request.form['payment']
        product_ids = request.form.getlist('product_id')
        quantities = request.form.getlist('quantity')
        total = 0
        items = []
        for pid, qty in zip(product_ids, quantities):
            qty = int(qty)
            if qty <= 0:
                continue
            c.execute("SELECT * FROM tblProducts WHERE ProductID=%s", (pid,))
            product = c.fetchone()
            if product:
                line_total = product['price'] * qty
                total += line_total
                items.append((int(pid), qty, product['price']))
        if items:
            sale_date = datetime.now().strftime('%Y-%m-%d %H:%M')
            c.execute("INSERT INTO tblSales (SaleDate, TotalAmount, PaymentMethod, ServedBy) VALUES (%s,%s,%s,%s) RETURNING SaleID",
                      (sale_date, total, payment, session['user']))
            sale_id = c.fetchone()['saleid']
            for pid, qty, price in items:
                c.execute("INSERT INTO tblSaleItems (SaleID, ProductID, Quantity, UnitPrice) VALUES (%s,%s,%s,%s)",
                          (sale_id, pid, qty, price))
                c.execute("UPDATE tblProducts SET StockQty = StockQty - %s WHERE ProductID=%s", (qty, pid))
            conn.commit()
            conn.close()
            flash(f'Sale recorded! Total: ${total:.2f}')
            return redirect(url_for('sale_receipt', sid=sale_id))
        else:
            flash('Please enter at least one item.')
    c.execute("SELECT * FROM tblProducts WHERE StockQty > 0 ORDER BY Category, ProductName")
    products = c.fetchall()
    conn.close()
    return render_template('new_sale.html', products=products)

@app.route('/sale/receipt/<int:sid>')
def sale_receipt(sid):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM tblSales WHERE SaleID=%s", (sid,))
    sale = c.fetchone()
    c.execute("""
        SELECT p.ProductName, si.Quantity, si.UnitPrice, (si.Quantity * si.UnitPrice) AS LineTotal
        FROM tblSaleItems si JOIN tblProducts p ON si.ProductID = p.ProductID
        WHERE si.SaleID=%s
    """, (sid,))
    items = c.fetchall()
    conn.close()
    return render_template('receipt.html', sale=sale, items=items)

# ── SALES HISTORY ──
@app.route('/history')
def history():
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM tblSales ORDER BY SaleDate DESC LIMIT 50")
    sales = c.fetchall()
    conn.close()
    return render_template('history.html', sales=sales)

@app.route('/history/<int:sid>')
def sale_detail(sid):
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM tblSales WHERE SaleID=%s", (sid,))
    sale = c.fetchone()
    c.execute("""
        SELECT p.ProductName, si.Quantity, si.UnitPrice, (si.Quantity * si.UnitPrice) AS LineTotal
        FROM tblSaleItems si JOIN tblProducts p ON si.ProductID = p.ProductID
        WHERE si.SaleID=%s
    """, (sid,))
    items = c.fetchall()
    conn.close()
    return render_template('sale_detail.html', sale=sale, items=items)

# ── REPORTS ──
@app.route('/reports')
def reports():
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) as count, SUM(TotalAmount) as total FROM tblSales WHERE SaleDate LIKE %s", (today + '%',))
    daily = c.fetchone()
    c.execute("SELECT * FROM tblProducts WHERE StockQty < 10 ORDER BY StockQty")
    low_stock = c.fetchall()
    c.execute("""
        SELECT p.ProductName, SUM(si.Quantity) as TotalSold
        FROM tblSaleItems si JOIN tblProducts p ON si.ProductID = p.ProductID
        GROUP BY p.ProductName ORDER BY TotalSold DESC LIMIT 5
    """)
    top_products = c.fetchall()
    conn.close()
    return render_template('reports.html', daily=daily, low_stock=low_stock, top_products=top_products, today=today)

if __name__ == '__main__':
    init
