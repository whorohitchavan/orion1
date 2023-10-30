from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
from flask_restful import Api, Resource

app = Flask(__name__)
app.secret_key = '1234'
api = Api(app)

app.config['MONGO_URI'] = "mongodb://localhost:27017/project"  # Update this with your MongoDB URI
mongo = PyMongo(app)

class Product:
    def __init__(self, name, description, price, discount):
        self.name = name
        self.description = description
        self.price = price
        self.discount = discount

    def save(self):
        # Store the product in your database
        mongo.db.products.insert_one({
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'discount': self.discount
        })

    @classmethod
    def get_all_products(cls):
        # Retrieve all products from the database and convert ObjectId to strings
        products = list(mongo.db.products.find())
        for product in products:
            product['_id'] = str(product['_id'])
        return products

class User:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def save(self):
        mongo.db.users.insert_one({
            'email': self.email,
            'password': self.password
        })

    @classmethod
    def find_by_email(cls, email):
        return mongo.db.users.find_one({'email': email})



@app.route('/')
def home():
    return redirect('/login')  # Redirect to the login page

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User(email, password)
        user.save()
        return  redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.find_by_email(email)

        if user and user['password'] == password:
            # You can implement session handling here
            session['user_email'] = user['email']
            return redirect(url_for('dashboard', user_email=user['email']))  # Redirect to the dashboard
        else:
            return "Login Failed"
    return render_template('login.html')




@app.route('/users', methods=['GET'])
def all_users():
    users = db.users.find()  # Retrieve all user documents from MongoDB
    return render_template('users.html', users=users)

class AllUsersResource(Resource):
    def get(self):
        users = list(db.users.find())  # Retrieve all user documents from MongoDB
        users_data = []
        for user in users:
            users_data.append({
                'email': user['email'],
                'password': user['password']
            })
        return {'users': users_data}

api.add_resource(AllUsersResource, '/api/users')

# ... Existing code ...

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "rohit" and password == "123456":
            return redirect('/admin_panel')  # Redirect to the admin dashboard
        else:
            return "Admin Login Failed"
    return render_template('admin-login.html')



@app.route('/dashboard/<user_email>', methods=['GET'])
def dashboard(user_email):
    products = Product.get_all_products()  # Fetch product data
    return render_template('dashboard.html', user_email=user_email, products=products)



@app.route('/logout', methods=['GET'])
def logout():
    # Clear the session to log the user out
    session.pop('user_email', None)

    # Add a flash message
    flash('Successfully logged in', 'success')

    return redirect('/')



from flask import render_template

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'user_email' not in session:
        return redirect('/login')

    if request.method == 'POST':
        new_email = request.form.get('new_email')
        new_password = request.form.get('new_password')

        if new_email:
            # Update the email in the MongoDB database for the logged-in user
            db.users.update_one({'email': session['user_email']}, {'$set': {'email': new_email}})

        if new_password:
            # Update the password in the MongoDB database for the logged-in user
            db.users.update_one({'email': session['user_email']}, {'$set': {'password': new_password}})

        return "Profile updated successfully"

    user_email = session['user_email']
    return render_template('update_profile.html', user_email=user_email)



@app.route('/admin_panel')
def admin_panel():
    return render_template('admin_panel.html')

@app.route('/add-product', methods=['POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        discount = float(request.form['discount'])
        product = Product ({'name': name,'description': description, 'price': price, 'discount': discount})
        product.save()
       
        return redirect('/admin-dashboard') 
        
         # Redirect to the admin dashboard

         
@app.route('/admin-dashboard')

def admin_dashboard():
    # You can fetch the products data from your database, for example:
    products = db.products.find()  # Assuming you have a collection named 'products' in your database

    # Render the 'admin_dashboard.html' template and pass the products data
    return render_template('admin-dashboard.html', products=products)


# Create a session variable for the cart
app.config['CART'] = []

# ... Other route functions ...
@app.route('/add-to-cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    # Retrieve the product details from the database
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})

    if product:
        # Convert ObjectId to string
        product['_id'] = str(product['_id'])

        # Add the product to the cart
        cart = session.get('cart', [])
        cart.append(product)
        session['cart'] = cart

        # Calculate the total price without discounts
        total_price = 0
        for item in cart:
            total_price += item['price']

        # Update the total price in the session
        session['total_price'] = total_price

        return jsonify({'success': True})

    return jsonify({'success': False})






# Remove the duplicated route function below

# ... Other route functions ...
@app.route('/cart', methods=['GET'])
def view_cart():
    # Retrieve the cart from the session
    cart = session.get('cart', [])
    total_price = session.get('total_price', 0)

    return render_template('cart.html', cart=cart, total_price=total_price)









@app.route('/remove-from-cart/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        cart = session['cart']
        updated_cart = [item for item in cart if str(item['_id']) != product_id]
        session['cart'] = updated_cart

        # Update total price and discount in the session
        total_price = 0
        total_discount = 0
        for product in updated_cart:
            total_price += product['price'] - (product['price'] * product['discount'] / 100)
            total_discount += (product['price'] * product['discount'] / 100)
        session['total_price'] = total_price
        session['total_discount'] = total_discount

    return redirect('/cart')






if __name__ == '__main__':
    app.run(debug=True, port=5000)
