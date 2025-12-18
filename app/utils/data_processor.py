"""
Data processing utilities for analyzing subject choice data
"""
import pandas as pd
from collections import Counter
import os
from .subject_mappings import normalize_subject_name


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def extract_academic_year_from_filename(filename):
    """
    Extract academic year from filename
    e.g., "S3_2024-25.xlsx" -> "2024-25"
    """
    # Try to find a pattern like 2024-25 or 202425
    import re
    match = re.search(r'20\d{2}[-_]?\d{2}', filename)
    if match:
        year_str = match.group()
        if '-' not in year_str and '_' not in year_str:
            # Convert 202425 to 2024-25
            return f"{year_str[:4]}-{year_str[4:]}"
        return year_str.replace('_', '-')
    return None


def read_subject_choices_file(filepath, year_group):
    """
    Read subject choices file and return structured data
    
    Expected format:
    - Forename column
    - Surname column  
    - Reg (registration class)
    - Columns A-H (S3), A-G (S4), A-F (S5-6)
    
    Args:
        filepath: Path to the file
        year_group: S3, S4, or S5-6
        
    Returns:
        pandas.DataFrame with standardized columns
    """
    # Read file
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:  # Excel
        df = pd.read_excel(filepath)
    
    # Normalize column names (remove leading/trailing spaces, convert to lowercase)
    df.columns = df.columns.str.strip().str.lower()
    
    # Find the key columns
    forename_col = next((col for col in df.columns if 'forename' in col or 'first' in col), None)
    surname_col = next((col for col in df.columns if 'surname' in col or 'last' in col), None)
    reg_col = next((col for col in df.columns if 'reg' in col), None)
    
    if not forename_col or not surname_col:
        raise ValueError("Could not find Forename and Surname columns in file")
    
    # Find choice columns (A, B, C, etc.)
    choice_columns = {}
    for letter in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
        # Look for columns named exactly like the letter or containing it
        col = next((c for c in df.columns if c == letter or f'choice {letter}' in c or f'column {letter}' in c), None)
        if col:
            choice_columns[letter] = col
    
    # If no lettered columns found, try to find subject/choice columns
    if not choice_columns:
        subject_cols = [col for col in df.columns 
                       if col not in [forename_col, surname_col, reg_col] 
                       and not any(x in col for x in ['id', 'number', 'date'])]
        # Map first 8 columns to A-H
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        for i, col in enumerate(subject_cols[:8]):
            if i < len(letters):
                choice_columns[letters[i]] = col
    
    # Build standardized dataframe
    result = pd.DataFrame()
    result['forename'] = df[forename_col]
    result['surname'] = df[surname_col]
    result['reg_class'] = df[reg_col] if reg_col else ''
    
    # Add choice columns
    for letter in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
        if letter in choice_columns:
            result[f'choice_{letter}'] = df[choice_columns[letter]].fillna('')
        else:
            result[f'choice_{letter}'] = ''
    
    # Remove completely empty rows
    result = result[result['forename'].notna() & (result['forename'] != '')]
    
    return result


def calculate_subject_totals(student_choices, include_excluded=False, year_group=None):
    """
    Calculate subject totals from student choice records
    
    Args:
        student_choices: List of StudentChoice objects
        include_excluded: Whether to include students marked as excluded
        year_group: Year group for applying subject name normalization
        
    Returns:
        dict: {subject_name: count}
    """
    subject_counts = Counter()
    
    for student in student_choices:
        if not include_excluded and not student.included_in_analysis:
            continue
            
        for choice in student.get_choices():
            if choice:
                # Normalize the subject name if year_group is provided
                subject_name = normalize_subject_name(choice, year_group) if year_group else choice
                if subject_name:
                    subject_counts[subject_name] += 1
    
    return dict(subject_counts)


def process_data_file(filepath, year_group):
    """
    Process uploaded data file and count subject choices
    
    Args:
        filepath: Path to the uploaded file
        year_group: Year group (S3, S4, S5-6)
    
    Returns:
        dict: Dictionary with subject names as keys and counts as values
    """
    df = read_subject_choices_file(filepath, year_group)
    
    subject_counts = Counter()
    
    # Count all subjects from choice columns
    choice_cols = [f'choice_{letter}' for letter in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']]
    
    for col in choice_cols:
        if col in df.columns:
            subjects = df[col].dropna()
            for subject in subjects:
                if subject and str(subject).strip():
                    subject_name = str(subject).strip()
                    subject_counts[subject_name] += 1
    
    return dict(subject_counts)


def generate_summary_statistics(subject_choices):
    """
    Generate summary statistics from subject choice data
    
    Args:
        subject_choices: List of SubjectChoice objects
    
    Returns:
        dict: Summary statistics
    """
    if not subject_choices:
        return {
            'total_choices': 0,
            'unique_subjects': 0,
            'most_popular': None,
            'least_popular': None,
            'average_choices': 0
        }
    
    total_choices = sum(sc.choice_count for sc in subject_choices)
    unique_subjects = len(subject_choices)
    
    sorted_choices = sorted(subject_choices, key=lambda x: x.choice_count, reverse=True)
    most_popular = sorted_choices[0] if sorted_choices else None
    least_popular = sorted_choices[-1] if sorted_choices else None
    
    average_choices = total_choices / unique_subjects if unique_subjects > 0 else 0
    
    return {
        'total_choices': total_choices,
        'unique_subjects': unique_subjects,
        'most_popular': most_popular,
        'least_popular': least_popular,
        'average_choices': round(average_choices, 2)
    }
