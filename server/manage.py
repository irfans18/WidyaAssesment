from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS, cross_origin

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://simple931:jw8s0F4@localhost:5432/simple_crud'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # Set the token expiration time to 1 hour (3600 seconds)

jwt = JWTManager(app)
db = SQLAlchemy(app)
CORS(app) 

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    products = db.relationship('Product', backref='user', lazy=True)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    img_path = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# RevokedToken model
class RevokedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

# Registration endpoint
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists!'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    access_token = create_access_token(identity=username)
    return jsonify({'message': 'User created successfully!','access_token': access_token}), 201
   #  return jsonify({'message': 'User created successfully!'}), 201


# Login endpoint
@app.route('/api/login', methods=['POST'])
@cross_origin()
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=username)
    return jsonify({'access_token': access_token}), 200

# Token revocation endpoint
@app.route('/api/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']  # Extracting JWT ID
    revoked_token = RevokedToken(jti=jti)
    db.session.add(revoked_token)
    db.session.commit()
    return jsonify({'message': 'Successfully logged out'}), 200


# Custom function to check if a token is revoked
def is_token_revoked():
    jti = get_jwt()['jti']
    return RevokedToken.query.filter_by(jti=jti).first() is not None

# Protected route example
@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    if is_token_revoked():
        return jsonify({'message': 'Token has been revoked'}), 401

    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# Create a new product associated with the authenticated user
@app.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    new_product = Product(
        name=data.get('name'), 
        description=data.get('description'), 
        price=data.get('price'), 
        user=current_user
   )

    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created successfully!'}), 201

# Retrieve all products with their owner's username
@app.route('/api/all-products', methods=['GET'])
@jwt_required()
def get_all_products_with_owners():
    products_with_owners = db.session.query(
        Product.id,
        Product.name,
        Product.description,
        Product.price,
        User.username.label('owner_username')
    ).join(User).all()

    if not products_with_owners:
        return jsonify({'message': 'No products found'}), 404

    products_list = []
    for product in products_with_owners:
        product_info = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'owner_username': product.owner_username
        }
        products_list.append(product_info)

    return jsonify(products_list), 200

# Get all products associated with the authenticated user
@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_user_products():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user:
        return jsonify({'message': 'User not found'}), 404

    products = [{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price
    } for product in current_user.products]

    return jsonify(products), 200

# Update a product
@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user:
        return jsonify({'message': 'User not found'}), 404

    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first()
    if not product:
        return jsonify({'message': 'Product not found or does not belong to the user'}), 404

    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)

    db.session.commit()
    return jsonify({'message': 'Product updated successfully!'}), 200

# Delete a product
@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user:
        return jsonify({'message': 'User not found'}), 404

    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first()
    if not product:
        return jsonify({'message': 'Product not found or does not belong to the user'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully!'}), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)