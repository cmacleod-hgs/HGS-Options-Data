"""
Data analysis routes
"""
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.analysis import analysis_bp
from app.models import DataUpload, SubjectChoice, StudentChoice
from app import db
from app.utils.data_processor import (process_data_file, allowed_file, 
                                     read_subject_choices_file, 
                                     calculate_subject_totals,
                                     extract_academic_year_from_filename)
from app.utils.subject_mappings import normalize_subject_name
import os
from datetime import datetime


@analysis_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload data file for analysis"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        year_group = request.form.get('year_group')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not year_group:
            flash('Please select a year group', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            filename = secure_filename(file.filename)
            
            # Create unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Create database record
            file_ext = filename.rsplit('.', 1)[1].lower()
            upload = DataUpload(
                filename=unique_filename,
                original_filename=filename,
                file_type=file_ext,
                year_group=year_group,
                user_id=current_user.id
            )
            db.session.add(upload)
            db.session.commit()
            
            flash('File uploaded successfully! Processing...', 'success')
            return redirect(url_for('analysis.process', upload_id=upload.id))
        else:
            flash('Invalid file type. Please upload CSV or Excel files.', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')


@analysis_bp.route('/process/<int:upload_id>')
@login_required
def process(upload_id):
    """Process uploaded data file"""
    upload = DataUpload.query.get_or_404(upload_id)    
    # Check if we need to review mappings first
    if not upload.processed and not request.args.get('skip_review'):
        # Redirect to review mappings page
        return redirect(url_for('analysis.review_mappings', upload_id=upload_id))    
    # Verify ownership
    if upload.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
    
    if upload.processed:
        flash('This file has already been processed', 'info')
        return redirect(url_for('analysis.view_data', upload_id=upload_id))
    
    try:
        # Process the file
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], upload.filename)
        df = read_subject_choices_file(filepath, upload.year_group)
        
        # Extract academic year from filename if not set
        academic_year = extract_academic_year_from_filename(upload.original_filename)
        
        # Import into StudentChoice staging table
        for _, row in df.iterrows():
            student = StudentChoice(
                upload_id=upload.id,
                forename=row.get('forename', ''),
                surname=row.get('surname', ''),
                reg_class=row.get('reg_class', ''),
                year_group=upload.year_group,
                academic_year=academic_year,
                choice_a=normalize_subject_name(row.get('choice_a', ''), upload.year_group),
                choice_b=normalize_subject_name(row.get('choice_b', ''), upload.year_group),
                choice_c=normalize_subject_name(row.get('choice_c', ''), upload.year_group),
                choice_d=normalize_subject_name(row.get('choice_d', ''), upload.year_group),
                choice_e=normalize_subject_name(row.get('choice_e', ''), upload.year_group),
                choice_f=normalize_subject_name(row.get('choice_f', ''), upload.year_group),
                choice_g=normalize_subject_name(row.get('choice_g', ''), upload.year_group),
                choice_h=normalize_subject_name(row.get('choice_h', ''), upload.year_group),
                included_in_analysis=True
            )
            db.session.add(student)
        
        # Calculate subject totals
        db.session.flush()  # Get IDs for student records
        students = StudentChoice.query.filter_by(upload_id=upload.id).all()
        subject_counts = calculate_subject_totals(students, year_group=upload.year_group)
        
        # Store aggregated results
        for subject, count in subject_counts.items():
            subject_choice = SubjectChoice(
                year_group=upload.year_group,
                subject_name=subject,
                choice_count=count,
                academic_year=academic_year,
                upload_id=upload.id
            )
            db.session.add(subject_choice)
        
        # Update upload record
        upload.processed = True
        upload.record_count = len(students)
        db.session.commit()
        
        flash(f'Successfully imported {len(students)} student records!', 'success')
        return redirect(url_for('analysis.view_data', upload_id=upload_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error processing file: {str(e)}')
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))


@analysis_bp.route('/results/<int:upload_id>')
@login_required
def results(upload_id):
    """Display analysis results"""
    upload = DataUpload.query.get_or_404(upload_id)
    
    # Verify ownership
    if upload.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get subject choices for this upload
    subject_choices = SubjectChoice.query.filter_by(upload_id=upload_id)\
        .order_by(SubjectChoice.choice_count.desc()).all()
    
    return render_template('results.html',
                         upload=upload,
                         subject_choices=subject_choices)


@analysis_bp.route('/compare')
@login_required
def compare():
    """Compare data across year groups"""
    # Get all subject choices grouped by year
    from sqlalchemy import func
    
    comparison_data = db.session.query(
        SubjectChoice.year_group,
        SubjectChoice.subject_name,
        func.sum(SubjectChoice.choice_count).label('total_count')
    ).group_by(SubjectChoice.year_group, SubjectChoice.subject_name)\
     .order_by(SubjectChoice.subject_name, SubjectChoice.year_group).all()
    
    # Organize data for display
    subjects = {}
    for year_group, subject, count in comparison_data:
        if subject not in subjects:
            subjects[subject] = {'S3': 0, 'S4': 0, 'S5-6': 0}
        subjects[subject][year_group] = count
    
    return render_template('compare.html', subjects=subjects)


@analysis_bp.route('/view/<int:upload_id>')
@login_required
def view_data(upload_id):
    """View student data from upload with ability to include/exclude"""
    upload = DataUpload.query.get_or_404(upload_id)
    
    # Verify ownership
    if upload.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get student choices
    students = StudentChoice.query.filter_by(upload_id=upload_id)\
        .order_by(StudentChoice.surname, StudentChoice.forename).all()
    
    # Get current totals
    subject_choices = SubjectChoice.query.filter_by(upload_id=upload_id)\
        .order_by(SubjectChoice.choice_count.desc()).all()
    
    # Calculate statistics
    total_students = len(students)
    included_students = sum(1 for s in students if s.included_in_analysis)
    excluded_students = total_students - included_students
    
    return render_template('view_data.html',
                         upload=upload,
                         students=students,
                         subject_choices=subject_choices,
                         total_students=total_students,
                         included_students=included_students,
                         excluded_students=excluded_students)


@analysis_bp.route('/toggle_student/<int:student_id>', methods=['POST'])
@login_required
def toggle_student(student_id):
    """Toggle student inclusion in analysis"""
    student = StudentChoice.query.get_or_404(student_id)
    
    # Verify ownership through upload
    upload = DataUpload.query.get(student.upload_id)
    if not upload or upload.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Toggle inclusion
    student.included_in_analysis = not student.included_in_analysis
    db.session.commit()
    
    # Recalculate totals
    recalculate_totals(student.upload_id)
    
    return jsonify({
        'success': True,
        'included': student.included_in_analysis
    })


@analysis_bp.route('/summary/<year_group>')
@login_required
def year_summary(year_group):
    """View summary and year-on-year comparison for a year group"""
    from sqlalchemy import func
    
    # Get all uploads for this year group
    uploads = DataUpload.query.filter_by(
        user_id=current_user.id,
        year_group=year_group, 
        processed=True
    ).order_by(DataUpload.upload_date.desc()).all()
    
    # Build detailed comparison data
    upload_data = []
    for upload in uploads:
        # Get total included students for this upload
        total_included = StudentChoice.query.filter_by(
            upload_id=upload.id,
            included_in_analysis=True
        ).count()
        
        # Get subject choices with counts and percentages
        subjects = SubjectChoice.query.filter_by(upload_id=upload.id)\
            .order_by(SubjectChoice.choice_count.desc()).all()
        
        subject_list = []
        for subject in subjects:
            subject_list.append({
                'name': subject.subject_name,
                'count': subject.choice_count,
                'percentage': round((subject.choice_count / total_included * 100) if total_included > 0 else 0, 1)
            })
        
        upload_data.append({
            'id': upload.id,
            'filename': upload.original_filename,
            'upload_date': upload.upload_date,
            'academic_year': upload.original_filename,  # Extract from filename
            'total_students': upload.record_count,
            'included_students': total_included,
            'subjects': subject_list
        })
    
    # Build comparison matrix (all unique subjects across all uploads)
    all_subjects = set()
    for data in upload_data:
        for subject in data['subjects']:
            all_subjects.add(subject['name'])
    
    # Create comparison table
    comparison_data = []
    for subject_name in sorted(all_subjects):
        row = {'subject': subject_name, 'uploads': []}
        
        for data in upload_data:
            # Find this subject in this upload
            subject_info = next((s for s in data['subjects'] if s['name'] == subject_name), None)
            if subject_info:
                row['uploads'].append({
                    'count': subject_info['count'],
                    'percentage': subject_info['percentage']
                })
            else:
                row['uploads'].append({
                    'count': 0,
                    'percentage': 0.0
                })
        
        comparison_data.append(row)
    
    # Calculate trends (if we have 2+ uploads)
    if len(upload_data) >= 2:
        for row in comparison_data:
            if len(row['uploads']) >= 2:
                # Calculate change from most recent to previous
                latest = row['uploads'][0]['count']
                previous = row['uploads'][1]['count']
                if previous > 0:
                    row['change'] = round(((latest - previous) / previous) * 100, 1)
                else:
                    row['change'] = 100.0 if latest > 0 else 0.0
    
    return render_template('year_summary.html',
                         year_group=year_group,
                         upload_data=upload_data,
                         comparison_data=comparison_data)


@analysis_bp.route('/subject-coincidence/<int:upload_id>')
@login_required
def subject_coincidence(upload_id):
    """Show subject combination/coincidence matrix for an upload"""
    upload = DataUpload.query.get_or_404(upload_id)
    
    # Verify ownership
    if upload.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get all included students
    students = StudentChoice.query.filter_by(
        upload_id=upload_id,
        included_in_analysis=True
    ).all()
    
    # Get all unique subjects from this upload
    all_subjects = set()
    for student in students:
        for choice in student.get_choices():
            if choice and choice.strip():
                all_subjects.add(choice.strip())
    
    all_subjects = sorted(list(all_subjects))
    
    # Build coincidence matrix
    # For each pair of subjects, count how many students take both
    coincidence_matrix = {}
    
    for subject1 in all_subjects:
        coincidence_matrix[subject1] = {}
        for subject2 in all_subjects:
            # Count students taking both subject1 and subject2
            count = 0
            for student in students:
                choices = [c.strip() for c in student.get_choices() if c and c.strip()]
                if subject1 in choices and subject2 in choices:
                    count += 1
            coincidence_matrix[subject1][subject2] = count
    
    # Calculate total students per subject (for diagonal and reference)
    subject_totals = {}
    for subject in all_subjects:
        count = 0
        for student in students:
            choices = [c.strip() for c in student.get_choices() if c and c.strip()]
            if subject in choices:
                count += 1
        subject_totals[subject] = count
    
    return render_template('subject_coincidence.html',
                         upload=upload,
                         all_subjects=all_subjects,
                         coincidence_matrix=coincidence_matrix,
                         subject_totals=subject_totals,
                         total_students=len(students))


def recalculate_totals(upload_id):
    """Recalculate subject totals based on included students"""
    # Delete existing totals
    SubjectChoice.query.filter_by(upload_id=upload_id).delete()
    
    # Get included students
    students = StudentChoice.query.filter_by(
        upload_id=upload_id,
        included_in_analysis=True
    ).all()
    
    # Get upload details
    upload = DataUpload.query.get(upload_id)
    
    # Calculate new totals with year group for normalization
    subject_counts = calculate_subject_totals(students, year_group=upload.year_group)
    
    # Store new totals
    for subject, count in subject_counts.items():
        subject_choice = SubjectChoice(
            year_group=upload.year_group,
            subject_name=subject,
            choice_count=count,
            academic_year=StudentChoice.query.filter_by(upload_id=upload_id).first().academic_year,
            upload_id=upload_id
        )
        db.session.add(subject_choice)
    
    db.session.commit()


@analysis_bp.route('/subject-mappings')
@login_required
def subject_mappings():
    """View all subject mappings from database"""
    # Get all mappings from database
    db_mappings = SubjectMapping.query.order_by(
        SubjectMapping.year_group,
        SubjectMapping.friendly_name
    ).all()
    
    # Organize by year group
    mappings_by_year = {
        'S3': [],
        'S4': [],
        'S5-6': []
    }
    
    for mapping in db_mappings:
        if mapping.year_group in mappings_by_year:
            mappings_by_year[mapping.year_group].append(mapping)
    
    return render_template('subject_mappings.html', mappings_by_year=mappings_by_year)


@analysis_bp.route('/subject-mappings/add', methods=['POST'])
@login_required
def add_subject_mapping():
    """Add or update a subject mapping"""
    year_group = request.form.get('year_group')
    unfriendly_name = request.form.get('unfriendly_name', '').strip()
    friendly_name = request.form.get('friendly_name', '').strip()
    
    if not all([year_group, unfriendly_name, friendly_name]):
        flash('All fields are required', 'error')
        return redirect(url_for('analysis.subject_mappings'))
    
    if year_group not in ['S3', 'S4', 'S5-6']:
        flash('Invalid year group', 'error')
        return redirect(url_for('analysis.subject_mappings'))
    
    try:
        # Check if mapping exists
        existing = SubjectMapping.query.filter_by(
            year_group=year_group,
            unfriendly_name=unfriendly_name
        ).first()
        
        if existing:
            existing.friendly_name = friendly_name
            existing.updated_at = db.func.now()
            flash(f'Updated mapping for "{unfriendly_name}"', 'success')
        else:
            new_mapping = SubjectMapping(
                year_group=year_group,
                unfriendly_name=unfriendly_name,
                friendly_name=friendly_name
            )
            db.session.add(new_mapping)
            flash(f'Added mapping: "{unfriendly_name}" → "{friendly_name}"', 'success')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving mapping: {str(e)}', 'error')
    
    return redirect(url_for('analysis.subject_mappings'))


@analysis_bp.route('/subject-mappings/delete/<int:mapping_id>', methods=['POST'])
@login_required
def delete_subject_mapping(mapping_id):
    """Delete a subject mapping"""
    mapping = SubjectMapping.query.get_or_404(mapping_id)
    
    try:
        unfriendly = mapping.unfriendly_name
        db.session.delete(mapping)
        db.session.commit()
        flash(f'Deleted mapping for "{unfriendly}"', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting mapping: {str(e)}', 'error')
    
    return redirect(url_for('analysis.subject_mappings'))


@analysis_bp.route('/subject-mappings-old')
@login_required
def subject_mappings_OLD():
    """View and manage subject name mappings"""
    from app.utils.subject_mappings import get_all_mappings
    
    mappings = get_all_mappings()
    
    return render_template('subject_mappings.html', mappings=mappings)


@analysis_bp.route('/add-mapping', methods=['POST'])
@login_required
def add_subject_mapping_OLD():
    """Add a new subject mapping - OLD VERSION"""
    from app.utils.subject_mappings import add_mapping
    
    year_group = request.form.get('year_group')
    unfriendly_name = request.form.get('unfriendly_name', '').strip()
    friendly_name = request.form.get('friendly_name', '').strip()
    
    if not all([year_group, unfriendly_name, friendly_name]):
        flash('All fields are required', 'error')
        return redirect(url_for('analysis.subject_mappings'))
    
    try:
        add_mapping(year_group, unfriendly_name, friendly_name)
        flash(f'Added mapping: {unfriendly_name} → {friendly_name} for {year_group}', 'success')
    except Exception as e:
        flash(f'Error adding mapping: {str(e)}', 'error')
    
    return redirect(url_for('analysis.subject_mappings'))


@analysis_bp.route('/delete/<int:upload_id>', methods=['POST'])
@login_required
def delete_upload(upload_id):
    """Delete an upload and all associated data"""
    upload = DataUpload.query.get_or_404(upload_id)
    
    # Verify ownership
    if upload.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Delete associated student choices
        StudentChoice.query.filter_by(upload_id=upload_id).delete()
        
        # Delete associated subject choices
        SubjectChoice.query.filter_by(upload_id=upload_id).delete()
        
        # Delete the file if it exists
        if upload.filename:
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], upload.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        # Delete the upload record
        filename = upload.original_filename
        db.session.delete(upload)
        db.session.commit()
        
        flash(f'Successfully deleted {filename} and all associated data', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting upload: {str(e)}')
        flash(f'Error deleting upload: {str(e)}', 'error')
    
    return redirect(url_for('main.dashboard'))


@analysis_bp.route('/review-mappings/<int:upload_id>', methods=['GET', 'POST'])
@login_required
def review_mappings(upload_id):
    """Review and set friendly names for subjects before final processing"""
    from app.utils.subject_mappings import get_all_mappings, normalize_subject_name, save_mappings_to_file
    
    upload = DataUpload.query.get_or_404(upload_id)
    
    # Verify ownership
    if upload.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # User has submitted their mapping choices
        new_mappings = {}
        
        # Get all form data for mappings
        for key in request.form:
            if key.startswith('friendly_'):
                original_name = key.replace('friendly_', '')
                friendly_name = request.form[key].strip()
                if friendly_name:
                    new_mappings[original_name] = friendly_name
        
        # Save new mappings if user chose to
        if request.form.get('save_mappings') == 'yes' and new_mappings:
            try:
                save_mappings_to_file(upload.year_group, new_mappings)
                flash(f'Saved {len(new_mappings)} new mappings for {upload.year_group}', 'success')
            except Exception as e:
                flash(f'Could not save mappings to file: {str(e)}', 'info')
        
        # Continue with processing using the chosen names
        return redirect(url_for('analysis.process', upload_id=upload_id, skip_review=1))
    
    # GET request - show the review page
    # Read the file to find all unique subjects
    try:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], upload.filename)
        df = read_subject_choices_file(filepath, upload.year_group)
        
        # Collect all unique subject names from the file
        all_subjects = set()
        for letter in ['choice_a', 'choice_b', 'choice_c', 'choice_d', 'choice_e', 'choice_f', 'choice_g', 'choice_h']:
            if letter in df.columns:
                subjects = df[letter].dropna().astype(str).str.strip()
                subjects = subjects[subjects != '']
                all_subjects.update(subjects.unique())
        
        # Check which ones need mapping
        current_mappings = get_all_mappings(upload.year_group)
        unmapped_subjects = []
        mapped_subjects = []
        
        for subject in sorted(all_subjects):
            normalized = normalize_subject_name(subject, upload.year_group)
            if normalized == subject:
                # No mapping exists
                unmapped_subjects.append(subject)
            else:
                # Already mapped
                mapped_subjects.append({'original': subject, 'friendly': normalized})
        
        if not unmapped_subjects:
            # All subjects already mapped, proceed directly to processing
            flash('All subjects already have friendly names!', 'info')
            return redirect(url_for('analysis.process', upload_id=upload_id, skip_review=1))
        
        return render_template('review_mappings.html',
                             upload=upload,
                             unmapped_subjects=unmapped_subjects,
                             mapped_subjects=mapped_subjects)
    
    except Exception as e:
        current_app.logger.error(f'Error reviewing mappings: {str(e)}')
        flash(f'Error reading file: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))
