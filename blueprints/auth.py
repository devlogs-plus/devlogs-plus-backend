from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, current_user

import app
from models import User
from extensions import db, bcrypt

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}

    required_fields = ['email', 'password', 'display_name']
    missing_fields = [
        field for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        return jsonify({
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400

    email = data.get('email')
    password = data.get('password')
    display_name = data.get('display_name')
    avatar_url = data.get('avatar_url')

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            'error': 'A user with this email already exists'
        }), 409

    new_user = User(
        email=email,
        display_name=display_name,
        avatar_url=avatar_url
    )
    hashed_password = new_user.set_password(password=password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'welcome': f'welcome to devlogs+ {display_name} {hashed_password}'
    }), 201

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password=password):
        return jsonify({'error': 'invalid email or password'}), 401

    login_user(user)
    return jsonify({'id': user.id, 'email': user.email}), 200

@auth_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'successfully logged out'})