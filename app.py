from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

# ======================
# DATABASE CONFIG
# ======================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======================
# USER MODEL
# ======================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    reset_token = db.Column(db.String(200))
    token_expiry = db.Column(db.DateTime)

# ======================
# OPPORTUNITY MODEL
# ======================
class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    start_date = db.Column(db.String(50))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer)

# Create DB
with app.app_context():
    db.create_all()

# ======================
# SIGNUP
# ======================
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json

    if not data.get('fullname') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "All fields required"}), 400

    if len(data['password']) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Account already exists"}), 400

    user = User(
        fullname=data['fullname'],
        email=data['email'],
        password=data['password']
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Signup successful"})

# ======================
# LOGIN
# ======================
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    user = User.query.filter_by(
        email=data['email'],
        password=data['password']
    ).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({
        "message": "Login successful",
        "user_id": user.id
    })

# ======================
# FORGOT PASSWORD
# ======================
@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    user = User.query.filter_by(email=email).first()

    if user:
        token = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(hours=1)

        user.reset_token = token
        user.token_expiry = expiry

        db.session.commit()

        print(f"Reset Link: http://127.0.0.1:5000/reset_password/{token}")

    return jsonify({"message": "If email exists, reset link sent"})

# ======================
# RESET PASSWORD
# ======================
@app.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    data = request.json
    new_password = data.get('password')

    user = User.query.filter_by(reset_token=token).first()

    if not user:
        return jsonify({"error": "Invalid token"}), 400

    if datetime.utcnow() > user.token_expiry:
        return jsonify({"error": "Token expired"}), 400

    user.password = new_password
    user.reset_token = None
    user.token_expiry = None

    db.session.commit()

    return jsonify({"message": "Password reset successful"})

# ======================
# ADD OPPORTUNITY
# ======================
@app.route('/add_opportunity', methods=['POST'])
def add_opportunity():
    data = request.json

    opp = Opportunity(
        name=data['name'],
        category=data['category'],
        duration=data['duration'],
        start_date=data['start_date'],
        description=data['description'],
        user_id=data['user_id']
    )

    db.session.add(opp)
    db.session.commit()

    return jsonify({"message": "Opportunity added", "id": opp.id})

# ======================
# VIEW ALL OPPORTUNITIES
# ======================
@app.route('/opportunities/<int:user_id>', methods=['GET'])
def get_opportunities(user_id):
    opps = Opportunity.query.filter_by(user_id=user_id).all()

    result = []
    for o in opps:
        result.append({
            "id": o.id,
            "name": o.name,
            "category": o.category,
            "duration": o.duration,
            "start_date": o.start_date,
            "description": o.description
        })

    return jsonify(result)

# ======================
# VIEW SINGLE OPPORTUNITY  ✅ (IMPORTANT ADDED)
# ======================
@app.route('/opportunity/<int:id>', methods=['GET'])
def get_single_opportunity(id):
    opp = Opportunity.query.get(id)

    if not opp:
        return jsonify({"error": "Opportunity not found"}), 404

    return jsonify({
        "id": opp.id,
        "name": opp.name,
        "category": opp.category,
        "duration": opp.duration,
        "start_date": opp.start_date,
        "description": opp.description,
        "user_id": opp.user_id
    })

# ======================
# UPDATE OPPORTUNITY
# ======================
@app.route('/update_opportunity/<int:id>', methods=['PUT'])
def update_opportunity(id):
    data = request.json
    opp = Opportunity.query.get(id)

    if not opp:
        return jsonify({"error": "Opportunity not found"}), 404

    opp.name = data.get('name', opp.name)
    opp.category = data.get('category', opp.category)
    opp.duration = data.get('duration', opp.duration)
    opp.start_date = data.get('start_date', opp.start_date)
    opp.description = data.get('description', opp.description)

    db.session.commit()

    return jsonify({"message": "Opportunity updated"})

# ======================
# DELETE OPPORTUNITY
# ======================
@app.route('/delete_opportunity/<int:id>', methods=['DELETE'])
def delete_opportunity(id):
    opp = Opportunity.query.get(id)

    if not opp:
        return jsonify({"error": "Opportunity not found"}), 404

    db.session.delete(opp)
    db.session.commit()

    return jsonify({"message": "Opportunity deleted"})

# ======================
# HOME
# ======================
@app.route('/')
def home():
    return "Backend is running"

# ======================
# RUN SERVER
# ======================
if __name__ == '__main__':
    app.run(debug=True)