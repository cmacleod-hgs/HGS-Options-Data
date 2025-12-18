"""
Database models
"""
from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class SubjectMapping(db.Model):
    """Store subject name mappings in database for persistence"""
    __tablename__ = 'subject_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    year_group = db.Column(db.String(10), nullable=False, index=True)
    unfriendly_name = db.Column(db.String(200), nullable=False)
    friendly_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one mapping per (year_group, unfriendly_name) pair
    __table_args__ = (
        db.UniqueConstraint('year_group', 'unfriendly_name', name='_year_unfriendly_uc'),
    )
    
    def __repr__(self):
        return f'<SubjectMapping {self.year_group}: {self.unfriendly_name} -> {self.friendly_name}>'


class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    oauth_provider = db.Column(db.String(50))
    oauth_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    uploads = db.relationship('DataUpload', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'


class DataUpload(db.Model):
    """Model for tracking uploaded data files"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    year_group = db.Column(db.String(10))  # S3, S4, S5-6
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    record_count = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<DataUpload {self.original_filename}>'


class SubjectChoice(db.Model):
    """Model for storing analyzed subject choice data"""
    id = db.Column(db.Integer, primary_key=True)
    year_group = db.Column(db.String(10), nullable=False)  # S3, S4, S5-6
    subject_name = db.Column(db.String(100), nullable=False)
    choice_count = db.Column(db.Integer, default=0)
    academic_year = db.Column(db.String(20))
    upload_id = db.Column(db.Integer, db.ForeignKey('data_upload.id'))
    
    def __repr__(self):
        return f'<SubjectChoice {self.year_group} - {self.subject_name}: {self.choice_count}>'


class StudentChoice(db.Model):
    """Staging table for individual student choices"""
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('data_upload.id'), nullable=False)
    forename = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    reg_class = db.Column(db.String(50))  # Registration class
    year_group = db.Column(db.String(10))  # S3, S4, S5-6
    academic_year = db.Column(db.String(20))  # e.g., "2024-25"
    
    # Subject choices (A-H for S3, A-G for S4, A-F for S5-6)
    choice_a = db.Column(db.String(100))
    choice_b = db.Column(db.String(100))
    choice_c = db.Column(db.String(100))
    choice_d = db.Column(db.String(100))
    choice_e = db.Column(db.String(100))
    choice_f = db.Column(db.String(100))
    choice_g = db.Column(db.String(100))
    choice_h = db.Column(db.String(100))
    
    # Flag to include/exclude from analysis
    included_in_analysis = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    upload = db.relationship('DataUpload', backref='student_choices')
    
    def __repr__(self):
        return f'<StudentChoice {self.forename} {self.surname} - {self.year_group}>'
    
    def get_choices(self):
        """Return list of non-null choices"""
        choices = []
        for choice in [self.choice_a, self.choice_b, self.choice_c, self.choice_d,
                      self.choice_e, self.choice_f, self.choice_g, self.choice_h]:
            if choice and choice.strip():
                choices.append(choice.strip())
        return choices
