from flask import Blueprint, jsonify, request

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'error': 'email is required'}), 400
    return jsonify({'welcome': f'welcome {email}'}), 200
