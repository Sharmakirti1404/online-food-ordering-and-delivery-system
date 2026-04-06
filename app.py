from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "foodgo"

# ================= DATABASE =================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sharmaKirti142005@#",
    database="foodgo"
)
@app.route('/')
def landing():
    return render_template("landing.html")

# ================= HOME =================

@app.route('/')
def home():
    return redirect('/login')


# ================= LOGIN =================

@app.route('/login', methods=['GET','POST'])
def login():

    # Show login page first
    if request.method == 'GET':
        return render_template("login.html")

    # Process login after form submit
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    cur = db.cursor(dictionary=True)

    cur.execute(
    "SELECT * FROM users WHERE email=%s AND password=%s AND role=%s",
    (email,password,role)
    )

    user = cur.fetchone()

    if user:

        session['user'] = user['name']
        session['role'] = role

        if role == "admin":
            return redirect('/admin')

        elif role == "restaurant":
            return redirect('/restaurant_dashboard')

        elif role == "delivery":
            return redirect('/delivery_dashboard')

        else:
            return redirect('/menu')

    else:
        return "Invalid login details"


# ================= REGISTER =================

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        cur = db.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cur.fetchone()

        if user:
            return "Email already registered"

        cur.execute(
        "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
        (name,email,password,role)
        )

        db.commit()

        return redirect('/login')

    return render_template("register.html")


# ================= MENU =================

@app.route('/menu')
def menu():

    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM food")

    foods = cur.fetchall()

    return render_template("menu.html", foods=foods)


# ================= ADD TO CART =================

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM food WHERE id=%s",(id,))
    food = cur.fetchone()

    cart_item = {
        "id": food['id'],
        "name": food['name'],
        "price": food['price'],
        "restaurant": food['restaurant']
    }

    if "cart" not in session:
        session["cart"] = []

    session["cart"].append(cart_item)
    session.modified = True

    return redirect('/cart')


# ================= CART =================

@app.route('/cart')
def cart():

    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)

    return render_template("cart.html", cart=cart, total=total)


# ================= PLACE ORDER =================

@app.route('/place_order', methods=['POST'])
def place_order():

    address = request.form.get('address')
    payment = request.form.get('payment')

    cart = session.get("cart", [])

    cur = db.cursor()

    for item in cart:

        cur.execute(
        """
        INSERT INTO orders (restaurant, food_name, qty, status, address)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (item['restaurant'], item['name'], 1, "Ordered", address)
        )

    db.commit()

    session.pop("cart", None)

    if payment == "online":
        return redirect('/payment')
    else:
        return redirect('/orders')


# ================= PAYMENT PAGE =================

@app.route('/payment')
def payment():
    return render_template("payment.html")




# ================= COMPLETE PAYMENT =================

@app.route('/complete_payment', methods=['GET','POST'])
def complete_payment():
    return render_template("payment_success.html")


# ================= CUSTOMER ORDERS =================

@app.route('/orders')
def orders():

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM orders ORDER BY id DESC")

    orders = cur.fetchall()

    return render_template("orders.html", orders=orders)


# ================= ADMIN DASHBOARD =================

@app.route('/admin')
def admin():

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM orders")
    orders = cur.fetchall()

    cur.execute("SELECT COUNT(*) as total FROM orders")
    total = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) as ordered FROM orders WHERE status='Ordered'")
    ordered = cur.fetchone()['ordered']

    cur.execute("SELECT COUNT(*) as preparing FROM orders WHERE status='Preparing'")
    preparing = cur.fetchone()['preparing']

    cur.execute("SELECT COUNT(*) as delivered FROM orders WHERE status='Delivered'")
    delivered = cur.fetchone()['delivered']

    return render_template(
        "admin.html",
        orders=orders,
        total=total,
        ordered=ordered,
        preparing=preparing,
        delivered=delivered
    )


# ================= DELETE ORDER =================

@app.route('/admin_delete_order/<int:id>')
def admin_delete_order(id):

    cur = db.cursor()

    cur.execute("DELETE FROM orders WHERE id=%s",(id,))

    db.commit()

    return redirect('/admin')


# ================= RESTAURANT DASHBOARD =================

@app.route('/restaurant_dashboard')
def restaurant_dashboard():

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM orders WHERE status='Ordered'")
    orders = cur.fetchall()

    return render_template("restaurant_dashboard.html", orders=orders)


# ================= PREPARE ORDER =================

@app.route('/prepare/<int:id>')
def prepare(id):

    cur = db.cursor()

    cur.execute(
    "UPDATE orders SET status='Preparing' WHERE id=%s",
    (id,)
    )

    db.commit()

    return redirect('/restaurant_dashboard')


# ================= RESTAURANT DELETE ORDER =================

@app.route('/restaurant_delete_order/<int:id>')
def restaurant_delete_order(id):

    cur = db.cursor()

    cur.execute("DELETE FROM orders WHERE id=%s",(id,))

    db.commit()

    return redirect('/restaurant_dashboard')


# ================= DELIVERY DASHBOARD =================

@app.route('/delivery_dashboard')
def delivery_dashboard():

    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM orders WHERE status='Preparing'")
    orders = cur.fetchall()

    return render_template("delivery_dashboard.html", orders=orders)


# ================= DELIVER ORDER =================

@app.route('/deliver/<int:id>')
def deliver(id):

    cur = db.cursor()

    cur.execute(
    "UPDATE orders SET status='Delivered' WHERE id=%s",
    (id,)
    )

    db.commit()

    return redirect('/delivery_dashboard')


# ================= DELIVERED ORDER =================

@app.route('/delivered/<int:id>')
def delivered(id):

    cur = db.cursor()

    cur.execute(
        "UPDATE orders SET status='Delivered' WHERE id=%s",
        (id,)
    )

    db.commit()

    return redirect('/delivery_dashboard')


# ================= LOGOUT =================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# ================= RUN APP =================

if __name__ == "__main__":
    app.run(debug=True)