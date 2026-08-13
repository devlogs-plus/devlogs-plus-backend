import os
import secrets

import requests
from authlib.integrations.base_client import OAuthError
from flask import Blueprint, jsonify, request, url_for, redirect, session
from flask_login import login_user, logout_user, login_required, current_user

from models import User
from extensions import db
from oauth import oauth

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({
            'error': 'Request body must be valid JSON'
        }), 400

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
    new_user.set_password(password=password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'welcome': f'welcome to devlogs+ {display_name}'
    }), 201

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({
            'error': 'Request body must be valid JSON'
        }), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            'error': 'Email and password are required'
        }), 400

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

@auth_bp.route('/auth/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'id': current_user.id,
        'display_name': current_user.display_name,
        'email': current_user.email,
        'avatar_url': current_user.avatar_url
    })

@auth_bp.route('/auth/getuser/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = User.query.filter_by(id=user_id).first()

    if user is None:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'display_name': user.display_name,
        'email': user.email,
        'avatar_url': user.avatar_url
    })

@auth_bp.route('/auth/getuser', methods=['POST'])
def get_user_by_email():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({
            'error': 'Request body must be valid JSON'
        }), 400

    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'display_name': user.display_name,
        'email': user.email,
        'avatar_url': user.avatar_url
    })

@auth_bp.route('/auth/me/edit', methods=['POST'])
@login_required
def edit_own_user():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({
            'error': 'Request body must be valid JSON'
        }), 400

    display_name = data.get('display_name')
    email = data.get('email')
    avatar_url = data.get('avatar_url')

    user = User.query.get(current_user.id)

    if user is None:
        return jsonify({'error': 'User not found'}), 404

    if display_name:
        user.display_name = display_name
    if email:
        user.email = email
    if avatar_url:
        user.avatar_url = avatar_url

    db.session.commit()

    return jsonify({'message': 'profile updated successfully'}), 200

@auth_bp.route('/uploadavatar', methods=['POST'])
def upload_avatar():
    if 'file' not in request.files:
        return jsonify({'error': 'no file uploaded'}), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return jsonify({'error': 'no selected file'}), 400

    cdn_key = os.environ.get('CDN_KEY')

    response = requests.post(
        'https://cdn.hackclub.com/api/v4/upload',
        headers={'Authorization': f'Bearer {cdn_key}'},
        files={'file': (uploaded_file.filename, uploaded_file.stream, uploaded_file.mimetype)}
    )

    if not response.ok:
        return jsonify({'error': 'Failed to upload file'}), response.status_code

    cdn_data = response.json()

    return jsonify(cdn_data), 200

@auth_bp.route('/auth/github')
def github_login():
    redirect_uri = url_for('auth_bp.github_callback', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

@auth_bp.route('/auth/github/callback')
def github_callback():
    oauth_error = request.args.get('error')
    if oauth_error:
        description = request.args.get('error_description') or 'GitHub login was cancelled or denied.'
        return jsonify({
            'error': oauth_error,
            'description': description
        }), 400
    try:
        token = oauth.github.authorize_access_token()
    except OAuthError as error:
        return jsonify({
            'error': error.error,
            'description': error.description or 'GitHub OAuth authentication failed.'
        }), 400

    github_user_response = oauth.github.get('user', token=token)
    if not github_user_response.ok:
        return jsonify({'error': 'Failed to fetch GitHub user profile'}), 502
    emails_response = oauth.github.get('user/emails', token=token)
    if not emails_response.ok:
        return jsonify({'error': 'Failed to fetch GitHub account emails'}), 502

    github_user = github_user_response.json()
    emails = emails_response.json()

    primary_email = next(
        (
            email['email']
            for email in emails
            if email.get('primary') and email.get('verified')
        ),
        None
    )
    if not primary_email:
        return jsonify({'error': 'github account must have a verified primary email'}), 400

    user = User.query.filter_by(email=primary_email).first()

    if user is None:
        user = User(
            email=primary_email,
            display_name=github_user.get('name') or github_user.get('login'),
            avatar_url=github_user.get('avatar_url')
        )

        user.set_password(secrets.token_urlsafe(32))

        db.session.add(user)
        db.session.commit()

    login_user(user)

    return redirect(os.environ.get('FRONTEND_URL', 'https://localhost:5173'))

@auth_bp.route('/auth/hackclub')
def hackclub_login():
    redirect_uri = url_for('auth_bp.hackclub_callback', _external=True)
    nonce = secrets.token_urlsafe(32)
    session['hackclub_oauth_nonce'] = nonce
    return oauth.hackclub.authorize_redirect(redirect_uri, nonce=nonce)

@auth_bp.route('/auth/hackclub/callback')
def hackclub_callback():
    oauth_error = request.args.get('error')
    if oauth_error:
        session.pop('hackclub_oauth_nonce', None)
        description = request.args.get('error_description') or 'Hack Club login was cancelled or denied.'
        return jsonify({
            'error': oauth_error,
            'description': description
        }), 400

    nonce = session.pop('hackclub_oauth_nonce', None)
    if not nonce:
        return jsonify({'error': 'Missing OAuth nonce. Please try logging in again.'}), 400

    try:
        token = oauth.hackclub.authorize_access_token()
        user_info = oauth.hackclub.parse_id_token(token, nonce=nonce)
    except OAuthError as error:
        return jsonify({
            'error': error.error,
            'description': error.description or 'Hack Club OAuth authentication failed.'
        }), 400

    email = user_info.get('email')
    email_verified = user_info.get('email_verified', True)

    if not email:
        return jsonify({'error': 'HackClub account did not provide an email'}), 400

    if not email_verified:
        return jsonify({'error': 'HackClub account email must be verified'}), 400

    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            email=email,
            display_name=user_info.get('name') or user_info.get('preferred_username') or email.split('@')[0],
            avatar_url=user_info.get('picture')
        )

        user.set_password(secrets.token_urlsafe(32))

        db.session.add(user)
        db.session.commit()

    login_user(user)

    return redirect(os.environ.get('FRONTEND_URL', 'https://localhost:5173'))