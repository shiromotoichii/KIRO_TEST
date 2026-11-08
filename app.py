from flask import Flask
from config import Config
from extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Расширения инициализируются после создания приложения
    db.init_app(app)
    login_manager.init_app(app)

    # Blueprint registration (models imported here to avoid circular import)
    from routes.auth import auth_bp
    from routes.todos import todos_bp
    from routes.categories import categories_bp
    from routes.recurrence import recurrence_bp
    from routes.projects import projects_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(todos_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(recurrence_bp)
    app.register_blueprint(projects_bp)

    # User loader (defined inside to avoid circular import)
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Create tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)