from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt

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

    hashed_password = bcrypt.generate_password_hash(
        password
    ).decode('utf-8')

    new_user = User(
        email=email,
        password_hash=hashed_password,
        display_name=display_name,
        avatar_url=avatar_url
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'welcome': f'welcome to devlogs+ {display_name} {hashed_password}'
    }), 201
