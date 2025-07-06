from flask import Blueprint

breaks_bp = Blueprint('breaks', __name__)

from . import routes