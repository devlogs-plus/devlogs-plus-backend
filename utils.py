from datetime import datetime, timedelta
from functools import wraps
from multiprocessing import connection
from urllib.parse import quote

import requests
from flask import jsonify, current_app
from flask_login import current_user
from flask_sqlalchemy.model import Model
from itsdangerous import URLSafeTimedSerializer

from extensions import db

from models import ProjectCollaborator, Project, Devlog, TimeTrackingConnection, User
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

def get_wakatime_time_since(time, project):
    if not current_user.is_authenticated:
        raise RuntimeError('a signed-in user is required to query WakaTime')

    connection = TimeTrackingConnection.query.filter_by(
        user_id=current_user.id,
        provider='wakatime'
    ).first()
    if connection is None:
        raise RuntimeError('no WakaTime connection found for the current user')

    response = oauth.wakatime.get(
        'users/current/summaries',
        token={'access_token': connection.access_token},
        params={
            'start': time.date().isoformat(),
            'end': datetime.utcnow().date().isoformat(),
            'project': project
        },
        timeout=10
    )
    response.raise_for_status()

    summaries = response.json().get('data')
    if not isinstance(summaries, list):
        raise ValueError('WakaTime returned an invalid summaries response')

    total_seconds = 0
    for summary in summaries:
        if not isinstance(summary, dict):
            raise ValueError('WakaTime returned an invalid summary')

        projects = summary.get('projects')
        if projects is None:
            continue
        if not isinstance(projects, list):
            raise ValueError('WakaTime returned an invalid project summary')

        total_seconds += sum(
            item['total_seconds']
            for item in projects
            if item.get('name') == project
        )

    return total_seconds

def get_hackatime_time_since(time, project):
    if not current_user.is_authenticated:
        raise RuntimeError('you must be signed in')

    connection = TimeTrackingConnection.query.filter_by(
        user_id=current_user.id,
        provider='hackatime'
    ).first()
    if connection is None:
        raise RuntimeError('no hackatime connect found')

    hackatime_info = get_users_hackatime_info(current_user.id)
    if hackatime_info is None:
        raise RuntimeError('no hackatime user info found')

    hackatime_user_id, hackatime_api_key = hackatime_info

    response = requests.get(
        f'https://hackatime.hackclub.com/api/hackatime/v1/users/{hackatime_user_id}/summaries',
        headers={'Authorization': f'Bearer {hackatime_api_key}'},
        timeout=10,
        params={
            'start': time.date().isoformat(),
            'end': datetime.utcnow().date().isoformat(),
            'project': project,
        }
    )
    response.raise_for_status()

    summaries = response.json().get('data')
    if not isinstance(summaries, list):
        raise ValueError('hackatime returned an invalid summaries response')

    total_seconds = 0
    for summary in summaries:
        if not isinstance(summary, dict):
            raise ValueError('WakaTime returned an invalid summary')

        projects = summary.get('projects')
        if projects is None:
            continue
        if not isinstance(projects, list):
            raise ValueError('WakaTime returned an invalid project summary')

        total_seconds += sum(
            item['total_seconds']
            for item in projects
            if item.get('name') == project
        )

    return total_seconds

def get_time_since_last_devlog(project_id):
    latest_devlog = (
        Devlog.query
        .filter_by(project_id=project_id)
        .filter(Devlog.published_at.isnot(None))
        .order_by(Devlog.published_at.desc())
        .first()
    )
    if latest_devlog:
        last_published_at = latest_devlog.published_at
    else:
        last_published_at = None
    return last_published_at

def get_users_hackatime_info(user_id):
    connection = TimeTrackingConnection.query.filter_by(user_id=user_id, provider='hackatime').first()
    if not connection:
        return None
    hackatime_user_id = connection.provider_user_id
    hackatime_api_key = connection.provider_api_key

    return hackatime_user_id, hackatime_api_key

def set_hackatime_user_id(user_id):
    connection = TimeTrackingConnection.query.filter_by(user_id=user_id, provider='hackatime').first()

    response = requests.get(
        "https://hackatime.hackclub.com/api/v1/authenticated/me",
        headers={
            "Authorization": f"Bearer {connection.access_token}"
        },
        timeout=10
    )

    connection.provider_user_id = str(response.json()["id"])
    db.session.commit()

def set_hackatime_api_key(user_id):
    connection = TimeTrackingConnection.query.filter_by(user_id=user_id, provider='hackatime').first()

    response = requests.get(
        "https://hackatime.hackclub.com/api/v1/authenticated/api_keys",
        headers={
            "Authorization": f"Bearer {connection.access_token}"
        },
        timeout=10
    )

    connection.provider_api_key = str(response.json()["token"])
    db.session.commit()