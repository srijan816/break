from flask import Blueprint

recommendations_bp = Blueprint('recommendations', __name__)

from . import routes