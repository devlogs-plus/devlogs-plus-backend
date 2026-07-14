from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from utils import require_project_access

from extensions import db
from models import User, Project, ProjectCollaborator, Devlog

devlog_bp = Blueprint('devlog_bp', __name__)

@devlog_bp.route('/projects/<int:project_id>/devlogs', methods=['GET'])
def get_devlogs(project_id):
    devlogs = Devlog.query.filter_by(project_id=project_id)
    return jsonify({
        'devlogs': [
            {
                'id': devlog.id,
                'project_id': project_id,
                'author_user_id': devlog.author_user_id,
                'title': devlog.title,
                'body_markdown': devlog.body_markdown,
                'published_at': devlog.published_at,
                'created_at': devlog.created_at,
                'updated_at': devlog.updated_at
            }
            for devlog in devlogs
        ]
    }), 200

@devlog_bp.route('/projects/<int:project_id>/devlogs', methods=['POST'])
@login_required
@require_project_access
def create_project(project_id):
    data = request.get_json()
    project = Project.query.get(project_id)

    required_fields = ['author_user_id', 'title', 'body_markdown']
    missing_fields = [
        field for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        return jsonify({
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400

    author_user_id = current_user.id
    title = data.get('title')
    body_markdown = data.get('body_markdown')

    devlog = Devlog(
        project_id=project_id,
        author_user_id=current_user.id,
        title=title,
        body_markdown=body_markdown
    )

    db.session.add(devlog)
    db.session.commit()

    return jsonify({'message': f'success, devlog {title} created!'}), 200