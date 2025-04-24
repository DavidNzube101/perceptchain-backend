from flask import Flask, jsonify, redirect, send_from_directory
from flask_cors import CORS

def create_app(config_object="app.config.Config"):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Initialize extensions
    CORS(app)
    
    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp)
    
    
    @app.route('/')
    def index():
        return redirect("/docs")
    
    @app.route('/health')
    def health():
        return jsonify({"message": {"status": "healthy", "description": "PerceptChain Backend is running!"}}), 200
    
    @app.route('/docs')
    def docs():
        return send_from_directory(app.static_folder, 'swagger-ui.html')
    
    @app.route("/get-docs-json")
    def get_docs_json():
        return send_from_directory(app.static_folder, 'swagger.json')
    
    # Register error handlers
    register_error_handlers(app)
    
    app.logger.info(f"Backend configured to use Helius RPC endpoint: {app.config['HELIUS_RPC_URL']}")
    return app

def register_error_handlers(app):
    
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"Server error: {error}")
        return {"error": "Internal server error"}, 500