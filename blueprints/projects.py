from operator import or_

import requests
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from extensions import db
from models import Project, ProjectCollaborator, TimeTrackingConnection, ProjectTimeTrackingProject

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
                'repo_url': project.repo_url,
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
    repo_url = data.get('repo_url')

    new_project = Project(
        owner_user_id=owner_user_id,
        name=name,
        short_description=short_description,
        demo_url=demo_url,
        repo_url=repo_url
    )

    db.session.add(new_project)
    db.session.commit()

    return jsonify({'message': f'success! project {name} created!'}), 200

@project_bp.route('/projects/user/<int:user_id>', methods=['GET'])
def view_users_projects(user_id):
    projects = (
        Project.query
        .outerjoin(
            ProjectCollaborator,
            Project.id == ProjectCollaborator.project_id
        )
        .filter(
            or_(
                Project.owner_user_id == user_id,
                ProjectCollaborator.user_id == user_id
            )
        )
        .distinct()
        .all()
    )
    return jsonify({
        'projects': [
            {
                'id': project.id,
                'owner_user_id': project.owner_user_id,
                'name': project.name,
                'short_description': project.short_description,
                'demo_url': project.demo_url,
                'repo_url': project.repo_url,
                'created_at': project.created_at,
                'updated_at': project.updated_at
            }
            for project in projects
        ]
    }), 200

@project_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        jsonify({'error': 'project not found'}), 404
    return jsonify(
        {
            'id': project.id,
            'owner_user_id': project.owner_user_id,
            'name': project.name,
            'short_description': project.short_description,
            'demo_url': project.demo_url,
            'repo_url': project.repo_url,
            'created_at': project.created_at,
            'updated_at': project.updated_at,
            'time_tracking_projects': [
                {
                    'id': time_project.id,
                    'name': time_project.name,
                    'provider': time_project.provider,
                    'created_at': time_project.created_at
                }
                for time_project in project.time_tracking_projects
            ]
        }), 200

@project_bp.route('/projects/<int:project_id>', methods=['PATCH'])
@login_required
def patch_project(project_id):
    project = Project.query.get(project_id)
    if current_user.id != project.owner_user_id:
        return jsonify({'message': 'current user does not own project'}), 403
    data = request.get_json()

    name = data.get('name')
    short_description = data.get('short_description')
    demo_url = data.get('demo_url')
    repo_url = data.get('repo_url')

    project.name = name
    project.short_description = short_description
    project.demo_url = demo_url
    project.repo_url = repo_url

    db.session.commit()
    return jsonify({'message': f'project {name} updated!'}), 200

@project_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    project = Project.query.get(project_id)
    if current_user.id != project.owner_user_id:
        return jsonify({'message': 'current user does not own project'}), 403
    db.session.delete(project)
    db.session.commit()

    return jsonify({'message': 'project has been deleted'})

@project_bp.route('/projects/<int:project_id>/collaborators', methods=['POST'])
@login_required
def add_collaborators(project_id):
    data = request.get_json()
    project = Project.query.get(project_id)
    if current_user.id != project.owner_user_id:
        return jsonify({'message': 'current user does not own project'}), 403

    required_fields = ['user_id']
    missing_fields = [
        field for field in required_fields
        if not data.get(field)
    ]
    if missing_fields:
        return jsonify({
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400

    existing = ProjectCollaborator.query.filter_by(
        project_id=project_id,
        user_id=data.get('user_id')
    ).first()

    if existing:
        return jsonify({'error': 'User is already a collaborator'}), 409

    collaborator = ProjectCollaborator(
        project_id=project_id,
        user_id=data.get('user_id'),
        role='collaborator'
    )

    db.session.add(collaborator)
    db.session.commit()

    return jsonify({'message': 'project collaborator added'}), 200

@project_bp.route('/projects/<int:project_id>/collaborators/<int:user_id>', methods=['DELETE'])
@login_required
def remove_collaborator(project_id, user_id):
    collaborator = ProjectCollaborator.query.filter_by(
        project_id=project_id,
        user_id=user_id
    ).first()

    if not collaborator:
        return jsonify({'error': 'Collaborator not found'}), 404

    db.session.delete(collaborator)
    db.session.commit()

    return jsonify({'message': 'Collaborator removed successfully'}), 200

@project_bp.route('/projects/<int:project_id>/collaborators', methods=['GET'])
def get_project_collaborators(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'project not found'}), 404

    collaborators = ProjectCollaborator.query.filter_by(project_id=project_id).all()
    user_ids = [c.user_id for c in collaborators]

    return jsonify({
        'project_id': project_id,
        'collaborator_user_id': user_ids
    }), 200

@project_bp.route('/projects/<int:project_id>/time', methods=['PATCH'])
@login_required
def link_time_project(project_id):
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({'error': 'request body must be valid json'}), 400

    time_tracking_project_names = data.get('time_tracking_project_names')

    if not isinstance(time_tracking_project_names, list) or not time_tracking_project_names:
        return jsonify({'error': 'time_tracking_project_names must be a non-empty list'}), 400

    project = Project.query.get(project_id)

    if not project:
        return jsonify({'error': 'project not found'}), 404
    if project.owner_user_id != current_user.id:
        return jsonify({'error': 'current user does not own project'}), 403

    ProjectTimeTrackingProject.query.filter_by(project_id=project.id).delete()

    for name in time_tracking_project_names:
        if not isinstance(name, str) or not name.strip():
            return jsonify({'error': 'each time tracking project name must be a non-empty string'}), 400
        db.session.add(ProjectTimeTrackingProject(project_id=project.id, name=name.strip()))

    db.session.commit()

    return jsonify({'message': 'time tracking project linked'}), 200

@project_bp.route('/projects/<int:project_id>/time', methods=['GET'])
def get_linked_time_projects(project_id):
    project = Project.query.get(project_id)

    if not project:
        return jsonify({'error': 'project not found'}), 404

    linked_projects = ProjectTimeTrackingProject.query.filter_by(
        project_id=project_id
    ).all()

    return jsonify({
        'time_tracking_project_names': [
            linked_project.name for linked_project in linked_projects
        ]
    }), 200