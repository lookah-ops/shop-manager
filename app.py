from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'shopkey2026'

DB = 'shop.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS tblUsers (
        UserID INTEGER PRIMARY KEY,
        Username TEXT,
        Password TEXT,
        Role TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tblProducts (
        ProductID INTEGER PRIMARY KEY,
        ProductName TEXT,
        Category TEXT,
        Price REAL,
        StockQty INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tblSales (
        SaleID INTEGER PRIMARY KEY,
        SaleDate TEXT,
        TotalAmount REAL,
        PaymentMethod TEXT,
        ServedBy TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tblSaleItems (
        SaleItemID INTEGER PRIMARY KEY,
        SaleID INTEGER,
        ProductID INTEGER,
        Quantity INTEGER,
        UnitPrice REAL
    )''')

    # Default users
    c.execute("SELECT COUNT(*) FROM tblUsers")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO tblUsers VALUES (1, 'admin', 'admin123', 'Admin')")
        c.execute("INSERT INTO tblUsers VALUES (2, 'staff', 'staff123', 'Staff')")

    # Sample products
    c.execute("SELECT COUNT(*) FROM tblProducts")
    if c.fetchone()[0] == 0:
        products = [
            (1, 'Bread', 'Bakery', 1.20, 50),
            (2, 'Milk', 'Dairy', 0.95, 80),
            (3, 'Sugar', 'Groceries', 2.50, 30),
            (4, 'Cooking Oil', 'Groceries', 3.80, 25),
            (5, 'Rice', 'Groceries', 4.00, 40),
            (6, 'Soap', 'Toiletries', 0.75, 60),
        ]
        c.executemany("INSERT INTO tblProducts VALUES (?,?,?,?,?)", products)

    conn.commit()
    conn.close()

# ── LOGIN ──
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM tblUsers WHERE Username=? AND Password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session['user'] = user['Username']
            session['role'] = user['Role']
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
    items = conn.execute("SELECT * FROM tblProducts ORDER BY Category, ProductName").fetchall()
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
        conn.execute("INSERT INTO tblProducts (ProductName, Category, Price, StockQty) VALUES (?,?,?,?)", (name, category, price, stock))
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
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        conn.execute("UPDATE tblProducts SET ProductName=?, Category=?, Price=?, StockQty=? WHERE ProductID=?", (name, category, price, stock, pid))
        conn.commit()
        conn.close()
        flash('Product updated!')
        return redirect(url_for('products'))
    product = conn.execute("SELECT * FROM tblProducts WHERE ProductID=?", (pid,)).fetchone()
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:pid>')
def delete_product(pid):
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    conn.execute("DELETE FROM tblProducts WHERE ProductID=?", (pid,))
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
            product = conn.execute("SELECT * FROM tblProducts WHERE ProductID=?", (pid,)).fetchone()
            if product:
                line_total = product['Price'] * qty
                total += line_total
                items.append((int(pid), qty, product['Price']))
        if items:
            sale_date = datetime.now().strftime('%Y-%m-%d %H:%M')
            conn.execute("INSERT INTO tblSales (SaleDate, TotalAmount, PaymentMethod, ServedBy) VALUES (?,?,?,?)",
                         (sale_date, total, payment, session['user']))
            sale_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for pid, qty, price in items:
                conn.execute("INSERT INTO tblSaleItems (SaleID, ProductID, Quantity, UnitPrice) VALUES (?,?,?,?)",
                             (sale_id, pid, qty, price))
                conn.execute("UPDATE tblProducts SET StockQty = StockQty - ? WHERE ProductID=?", (qty, pid))
            conn.commit()
            conn.close()
            flash(f'Sale recorded! Total: ${total:.2f}')
            return redirect(url_for('sale_receipt', sid=sale_id))
        else:
            flash('Please enter at least one item.')
    products = conn.execute("SELECT * FROM tblProducts WHERE StockQty > 0 ORDER BY Category, ProductName").fetchall()
    conn.close()
    return render_template('new_sale.html', products=products)

@app.route('/sale/receipt/<int:sid>')
def sale_receipt(sid):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    sale = conn.execute("SELECT * FROM tblSales WHERE SaleID=?", (sid,)).fetchone()
    items = conn.execute("""
        SELECT p.ProductName, si.Quantity, si.UnitPrice, (si.Quantity * si.UnitPrice) AS LineTotal
        FROM tblSaleItems si JOIN tblProducts p ON si.ProductID = p.ProductID
        WHERE si.SaleID=?
    """, (sid,)).fetchall()
    conn.close()
    return render_template('receipt.html', sale=sale, items=items)

# ── SALES HISTORY ──
@app.route('/history')
def history():
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    sales = conn.execute("SELECT * FROM tblSales ORDER BY SaleDate DESC LIMIT 50").fetchall()
    conn.close()
    return render_template('history.html', sales=sales)

@app.route('/history/<int:sid>')
def sale_detail(sid):
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    sale = conn.execute("SELECT * FROM tblSales WHERE SaleID=?", (sid,)).fetchone()
    items = conn.execute("""
        SELECT p.ProductName, si.Quantity, si.UnitPrice, (si.Quantity * si.UnitPrice) AS LineTotal
        FROM tblSaleItems si JOIN tblProducts p ON si.ProductID = p.ProductID
        WHERE si.SaleID=?
    """, (sid,)).fetchall()
    conn.close()
    return render_template('sale_detail.html', sale=sale, items=items)

# ── REPORTS ──
@app.route('/reports')
def reports():
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('menu'))
    conn = get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    daily = conn.execute("SELECT COUNT(*) as count, SUM(TotalAmount) as total FROM tblSales WHERE SaleDate LIKE ?", (today + '%',)).fetchone()
    low_stock = conn.execute("SELECT * FROM tblProducts WHERE StockQty < 10 ORDER BY StockQty").fetchall()
    top_products = conn.execute("""
        SELECT p.ProductName, SUM(si.Quantity) as TotalSold
        FROM tblSaleItems si JOIN tblProducts p ON si.ProductID = p.ProductID
        GROUP BY p.ProductName ORDER BY TotalSold DESC LIMIT 5
    """).fetchall()
    conn.close()
    return render_template('reports.html', daily=daily, low_stock=low_stock, top_products=top_products, today=today)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
