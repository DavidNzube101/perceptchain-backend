from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
from .config import Config
from .routes.health import health_bp
from .routes.balances import balances_bp
from .routes.queries import queries_bp

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)
    CORS(app)

    
    app.register_blueprint(health_bp)
    app.register_blueprint(balances_bp)
    app.register_blueprint(queries_bp)
    
    @app.route('/docs')
    def docs():
        return send_from_directory(app.static_folder, 'swagger-ui.html')
    
    @app.route('/')
    def default():
        return redirect('/docs', code=302)

    return app
