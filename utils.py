from datetime import datetime, timedelta
from functools import wraps

from flask import jsonify, current_app
from flask_login import current_user
from flask_sqlalchemy.model import Model
from itsdangerous import URLSafeTimedSerializer

from extensions import db

from models import ProjectCollaborator, Project, Devlog
from oauth import oauth


def is_user_authorized_for_project(user_id, project_id):
    project = Project.query.get(project_id)

    if not project:
        return False

    return (
            user_id == project.owner_user_id or
            ProjectCollaborator.query.filter_by(
                project_id=project_id,
                user_id=user_id
            ).first() is not None
    )

def anonymize_and_delete_user(user):
    # Deleted user id is 0
    Project.query.filter_by(owner_user_id=user.id).update({
        'owner_user_id': 0
    })
    Devlog.query.filter_by(author_user_id=user.id).update({
        'author_user_id': 0
    })
    ProjectCollaborator.query.filter_by(user_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()

def require_project_access(f):
    @wraps(f)
    def decorated_function(project_id, *args, **kwargs):
        if not is_user_authorized_for_project(current_user.id,project_id):
            return jsonify({'error': 'unauthorized'}), 403
        return f(project_id, *args, **kwargs)
    return decorated_function

def generate_verification_code(user):
    verification_code = URLSafeTimedSerializer(current_app.config['SECRET_KEY']).dumps(user.id)
    return verification_code

def refresh_wakatime_token(connection):
    if not connection.refresh_token:
        return None
    new_token = oauth.wakatime.refresh_token(
        token_url='https://wakatime.com/oauth/token',
        refresh_token=connection.refresh_token,
        client_id=current_app.config['WAKATIME_CLIENT_ID'],
        client_secret=current_app.config['WAKATIME_CLIENT_SECRET']
    )
    if not new_token or 'access_token' not in new_token:
        return None
    connection.access_token = new_token.get('access_token')
    connection.refresh_token = new_token.get('refresh_token', connection.refresh_token)
    expires_in = new_token.get('expires_in')
    connection.expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None
    db.session.commit()
    return new_token