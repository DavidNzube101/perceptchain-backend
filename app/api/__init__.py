from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes after creating blueprint to avoid circular imports
from app.api import routes