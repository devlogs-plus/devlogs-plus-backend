from datetime import datetime

from sqlalchemy.orm import backref

from extensions import db, bcrypt
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class TimeTrackingConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(200))
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text)
    token_type = db.Column(db.String(50), default='Bearer')
    expires_at = db.Column(db.DateTime)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint(
            'user_id',
            'provider',
            name='unique_user_time_tracking_provider'
        ),
    )

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    short_description = db.Column(db.Text)
    demo_url = db.Column(db.String(500))
    repo_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    time_tracking_projects = db.relationship(
        'ProjectTimeTrackingProject',
        backref='project',
        cascade='all, delete-orphan'
    )

class ProjectTimeTrackingProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint(
            'project_id',
            'name',
            'provider',
            name='unique_project_time_tracking_name'
        ),
    )

class ProjectCollaborator(db.Model):
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    role = db.Column(db.String(20), default='owner')

class Devlog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    author_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300))
    body_markdown = db.Column(db.Text)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    seconds_spent = db.Column(db.String(500))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'author_user_id': self.author_user_id,
            'title': self.title,
            'body_markdown': self.body_markdown,
            'published_at': self.published_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'seconds_spent': self.seconds_spent
        }