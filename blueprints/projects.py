from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from extensions import db
from models import User, Project, ProjectCollaborator

project_bp = Blueprint('project_bp', __name__)

@project_bp.route('/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify({
        'projects': [
            {
                'id': project.id,
                'owner_user_id': project.owner_user_id,
                'name': project.name,
                'short_description': project.short_description,
                'demo_url': project.demo_url,
                'created_at': project.created_at,
                'updated_at': project.updated_at
            }
            for project in projects
        ]
    }), 200

@project_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    data = request.get_json()

    required_fields = ['name']
    missing_fields = [
        field for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        return jsonify({
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400

    owner_user_id = current_user.id
    name = data.get('name')
    short_description = data.get('short_description')
    demo_url = data.get('demo_url')

    new_project = Project(
        owner_user_id=owner_user_id,
        name=name,
        short_description=short_description,
        demo_url=demo_url
    )

    db.session.add(new_project)
    db.session.commit()

    return jsonify({'message': f'success! project {name} created!'}), 200