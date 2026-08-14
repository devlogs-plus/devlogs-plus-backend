import os
import secrets

from flask import Flask
from flask_cors import CORS

from extensions import db, login_manager, bcrypt
from config import Config
from models import User
from oauth import init_oauth


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID')
    app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET')
    app.config['HACKCLUB_CLIENT_ID'] = os.environ.get('HACKCLUB_CLIENT_ID')
    app.config['HACKCLUB_CLIENT_SECRET'] = os.environ.get('HACKCLUB_CLIENT_SECRET')

    db.init_app(app)
    init_oauth(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except (TypeError, ValueError):
            return None

    from blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)
    from blueprints.projects import project_bp
    app.register_blueprint(project_bp)
    from blueprints.devlogs import devlog_bp
    app.register_blueprint(devlog_bp)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        deleted_user = User(
            id=0,
            email='',
            display_name='Deleted User',
            avatar_url=''
        )
        deleted_user.set_password(secrets.token_urlsafe(32))
        db.session.add(deleted_user)
        db.session.commit()
    app.run(host='0.0.0.0', port=5000,
            ssl_context=('C:\\Certs\\localhost+2.pem',
                         'C:\\Certs\\localhost+2-key.pem'),
            debug=True)
