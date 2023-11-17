from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production

# Configure the database URI for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://simple931:jw8s0F4@localhost/simple_crud'

# Silence the deprecation warning
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

jwt = JWTManager(app)
db = SQLAlchemy(app)

# Sample user data (for testing purposes)
users = {
    'user1': {
        'username': 'user1',
        'password': 'pos'
    }
}

products = [
    {
        'id': 1,
        'name': 'Product 1',
        'description': 'Description of Product 1',
        'price': 29.99
    },
    {
        'id': 2,
        'name': 'Product 2',
        'description': 'Description of Product 2',
        'price': 49.99
    }
]


# Registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in users:
        return jsonify({'message': 'User already exists!'}), 400

    users[username] = {
        'username': username,
        'password': password
    }
    access_token = create_access_token(identity=username)

    return jsonify({'message': 'User created successfully!','access_token': access_token}), 201

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username not in users or users[username]['password'] != password:
        return jsonify({'message': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=username)
    return jsonify({'access_token': access_token}), 200

# Protected endpoint for testing with JWT
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# Create a new product
@app.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    if not request.is_json:
        return jsonify({'message': 'Missing JSON in request'}), 400

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')

    if not name or not description or not price:
        return jsonify({'message': 'Missing required fields'}), 400

    new_product = {
        'id': len(products) + 1,
        'name': name,
        'description': description,
        'price': price
    }
    products.append(new_product)
    return jsonify(new_product), 201

# Get all products
@app.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    return jsonify(products), 200

# Get a specific product by ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    for product in products:
        if product['id'] == product_id:
            return jsonify(product), 200
    return jsonify({'message': 'Product not found'}), 404

# Update a product by ID
@app.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    if not request.is_json:
        return jsonify({'message': 'Missing JSON in request'}), 400

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')

    for product in products:
        if product['id'] == product_id:
            product['name'] = name if name else product['name']
            product['description'] = description if description else product['description']
            product['price'] = price if price else product['price']
            return jsonify(product), 200

    return jsonify({'message': 'Product not found'}), 404

# Delete a product by ID
@app.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    for index, product in enumerate(products):
        if product['id'] == product_id:
            del products[index]
            return jsonify({'message': 'Product deleted'}), 200

    return jsonify({'message': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
