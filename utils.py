from functools import wraps

from flask import jsonify, current_app
from flask_login import current_user
from flask_sqlalchemy.model import Model
from itsdangerous import URLSafeTimedSerializer

from extensions import db

from models import ProjectCollaborator, Project, Devlog


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