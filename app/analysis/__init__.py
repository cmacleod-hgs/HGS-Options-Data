"""
Analysis blueprint for data processing and analysis
"""
from flask import Blueprint

analysis_bp = Blueprint('analysis', __name__)

from app.analysis import routes
