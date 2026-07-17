from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy.model import Model
from flask_sqlalchemy.session import Session

from extensions import db, login_manager, bcrypt
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/*": {"origins": "*"}})

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

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

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)