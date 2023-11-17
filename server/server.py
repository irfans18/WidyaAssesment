from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://simple931:jw8s0F4@localhost:5432/simple_crud'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

# Define routes for CRUD operations

@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    new_product = Product(name=data['name'], price=data['price'], description=data.get('description', ''))
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created successfully'}), 201

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'description': product.description
        })
    return jsonify(result), 200

# Add routes for other CRUD operations (GET specific product, UPDATE product, DELETE product)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
