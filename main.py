from flask import Flask
from src.controller.project_controller import project_blueprint
from src.controller.pull_request_controller import pr_bp
from src.controller.user_controller import user_blueprint

def create_app():
    app = Flask(__name__)
    app.register_blueprint(project_blueprint, url_prefix="/api/project")
    app.register_blueprint(pr_bp)
    app.register_blueprint(user_blueprint, url_prefix="/api/user")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)