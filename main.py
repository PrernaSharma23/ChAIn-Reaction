from flask import Flask
from src.controller.project_controller import project_blueprint

def create_app():
    app = Flask(__name__)
    app.register_blueprint(project_blueprint, url_prefix="/api/project")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)