"""
Main application routes
"""
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp
from app.models import DataUpload, SubjectChoice
from app import db
from sqlalchemy import func


@main_bp.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get user's uploads
    uploads = DataUpload.query.filter_by(user_id=current_user.id)\
        .order_by(DataUpload.upload_date.desc()).all()
    
    # Get summary statistics
    total_uploads = len(uploads)
    processed_uploads = sum(1 for u in uploads if u.processed)
    
    # Get subject choice summary
    subject_stats = db.session.query(
        SubjectChoice.year_group,
        func.count(SubjectChoice.id).label('subject_count'),
        func.sum(SubjectChoice.choice_count).label('total_choices')
    ).group_by(SubjectChoice.year_group).all()
    
    return render_template('dashboard.html',
                         uploads=uploads,
                         total_uploads=total_uploads,
                         processed_uploads=processed_uploads,
                         subject_stats=subject_stats)
