from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from utils import require_project_access

from extensions import db
from models import User, Project, ProjectCollaborator, Devlog

devlog_bp = Blueprint('devlog_bp', __name__)

@devlog_bp.route('/projects/<int:project_id>/devlogs', methods=['GET'])
def get_devlogs(project_id):
    devlogs = Devlog.query.filter_by(project_id=project_id).filter(Devlog.published_at.isnot(None))
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
def create_devlog(project_id):
    data = request.get_json()
    project = Project.query.get(project_id)

    required_fields = ['title', 'body_markdown']
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

    return jsonify(devlog.to_dict()), 201

@devlog_bp.route('/projects/<int:project_id>/devlogs/<int:devlog_id>', methods=['GET'])
def get_devlog(project_id, devlog_id):
    devlog = Devlog.query.get(devlog_id)
    if not devlog:
        return jsonify({'error': 'devlog not found'}), 404
    if devlog.published_at is None and (not current_user.is_authenticated or current_user.id != devlog.author_user_id):
        return jsonify({'error': 'devlog not found'}), 404
    return jsonify(
        {
            'id': devlog.id,
            'project_id': devlog.project_id,
            'author_user_id': devlog.author_user_id,
            'title': devlog.title,
            'body_markdown': devlog.body_markdown,
            'published_at': devlog.published_at,
            'created_at': devlog.created_at,
            'updated_at': devlog.updated_at
        }
    ), 200

@devlog_bp.route('/projects/<int:project_id>/devlogs/<int:devlog_id>', methods=['PATCH'])
@login_required
@require_project_access
def patch_devlog(project_id, devlog_id):
    devlog = Devlog.query.get(devlog_id)
    data = request.get_json()
    if not devlog:
        return jsonify({'error': 'devlog does not exist'}), 404

    title = data.get('title')
    body_markdown = data.get('body_markdown')

    devlog.title = title
    devlog.body_markdown = body_markdown

    db.session.commit()
    return jsonify({'message': f'devlog {title} updated'}), 200

@devlog_bp.route('/projects/<int:project_id>/devlogs/<int:devlog_id>/publish', methods=['POST'])
@login_required
@require_project_access
def publish_devlog(project_id, devlog_id):
    devlog = Devlog.query.get(devlog_id)
    if not devlog:
        return jsonify({'error': 'devlog does not exist'}), 404
    data = request.get_json()

    devlog.published_at = datetime.utcnow()
    title = devlog.title

    db.session.commit()
    return jsonify({'message': f'devlog {title} published!'}), 200

@devlog_bp.route('/projects/<int:project_id>/devlogs/<int:devlog_id>/unpublish', methods=['POST'])
@login_required
@require_project_access
def unpublish_devlog(project_id, devlog_id):
    devlog = Devlog.query.get(devlog_id)
    data = request.get_json()
    if not devlog:
        return jsonify({'error': 'devlog does not exist'}), 404

    devlog.published_at = None
    title = devlog.title

    db.session.commit()
    return jsonify({'message': f'devlog {title} unpublished'}), 200

@devlog_bp.route('/users/devlogs/unpublished', methods=['GET'])
@login_required
def get_user_unpublished_devlogs():
    devlogs = Devlog.query.filter_by(author_user_id=current_user.id).filter(Devlog.published_at.is_(None))

    return jsonify({'devlogs': [devlog.to_dict() for devlog in devlogs]}), 200

@devlog_bp.route('/feed', methods=['GET'])
def get_feed():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    per_page = min(max(1, per_page), 100)

    q = db.session.query(Devlog, User, Project) \
        .join(User, Devlog.author_user_id == User.id) \
        .join(Project, Devlog.project_id == Project.id) \
        .filter(Devlog.published_at.isnot(None)) \
        .order_by(Devlog.published_at.desc(), Devlog.created_at.desc())

    total = q.count()
    items = q.limit(per_page).offset((page - 1) * per_page).all()

    devlogs = []
    for devlog, user, project in items:
        d = devlog.to_dict()
        d['author'] = {
            'id': user.id,
            'display_name': user.display_name,
            'avatar_url': user.avatar_url
        }
        d['project'] = {
            'id': project.id,
            'name': project.name,
            'short_description': project.short_description
        }
        devlogs.append(d)

    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'devlogs': devlogs
    }), 200