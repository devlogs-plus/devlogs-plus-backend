from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy.model import Model
from flask_sqlalchemy.session import Session

from extensions import db, login_manager, bcrypt
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)

    from models import User
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
    app.run(host='0.0.0.0', port=5000,
            ssl_context=('C:\\Certs\\localhost+2.pem',
                         'C:\\Certs\\localhost+2-key.pem'),
            debug=True)
