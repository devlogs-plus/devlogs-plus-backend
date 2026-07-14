from functools import wraps

from flask import jsonify
from flask_login import current_user

from models import ProjectCollaborator, Project


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

def require_project_access(f):
    @wraps(f)
    def decorated_function(project_id, *args, **kwargs):
        if not is_user_authorized_for_project(current_user.id,project_id):
            return jsonify({'error': 'unauthorized'}), 403
        return f(project_id, *args, **kwargs)
    return decorated_function