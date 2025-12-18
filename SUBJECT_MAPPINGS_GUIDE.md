# Subject Name Mapping Guide

## Overview
The subject name mapping system allows you to convert unfriendly subject codes/names from uploaded files into friendly, readable names for display and analysis.

## How It Works

1. **Upload Processing**: When a file is processed, each subject name is checked against the mapping for that year group
2. **Normalization**: If a mapping exists, the subject name is converted to the friendly version
3. **Storage**: Both the StudentChoice records and aggregated SubjectChoice records store the friendly names
4. **Year-Specific**: Different mappings can be defined for S3, S4, and S5-6

## Adding Mappings

### Method 1: Via Web Interface (Runtime Only)
1. Navigate to Dashboard → "Manage Subject Mappings"
2. Fill in the form with:
   - **Year Group**: S3, S4, or S5-6
   - **Unfriendly Name**: The exact text from your uploaded file (e.g., `MATH_ADV`)
   - **Friendly Name**: How you want it displayed (e.g., `Mathematics Advanced`)
3. Click "Add Mapping"

**Note**: These mappings only last for the current session. To make them permanent, use Method 2.

### Method 2: Edit Configuration File (Permanent)
Edit `app/utils/subject_mappings.py`:

```python
# S4 Subject Mappings (example)
S4_SUBJECT_MAPPINGS = {
    'ENG_LIT': 'English Literature',
    'MATH_ADV': 'Mathematics Advanced',
    'SCI_PHY': 'Physics',
    'SCI_CHEM': 'Chemistry',
    'SCI_BIO': 'Biology',
    'HIST': 'History',
    'GEOG': 'Geography',
    'MOD_LANG_FR': 'French',
    'MOD_LANG_ES': 'Spanish',
    'ART_DES': 'Art & Design',
    'MUS': 'Music',
    'PE': 'Physical Education',
    'BUS_MAN': 'Business Management',
    'COMP_SCI': 'Computing Science',
}
```

After editing, restart the Flask application:
```bash
# Stop the current server (Ctrl+C)
# Then restart:
.\.venv\Scripts\python.exe app.py
```

## Example Workflow

1. **Upload a file** with subject codes like:
   ```
   Student    | A           | B         | C
   John Doe   | MATH_ADV    | ENG_LIT   | SCI_PHY
   ```

2. **Add mappings** for your year group

3. **Re-process** the file (or just view the results if already processed)

4. **See friendly names** in all reports:
   ```
   Student    | A                        | B                    | C
   John Doe   | Mathematics Advanced     | English Literature   | Physics
   ```

## Features

- **Case-Insensitive**: Matching works regardless of case
- **Whitespace Trimming**: Extra spaces are automatically removed
- **Year-Specific**: S3, S4, and S5-6 can have completely different mappings
- **Fallback**: If no mapping exists, the original name is used unchanged
- **Automatic Application**: Applies during import and when recalculating totals

## Best Practices

1. **Be Consistent**: Use the same friendly names across all year groups for the same subject
2. **Document Codes**: Keep notes of what codes mean from your source systems
3. **Test First**: Upload a small sample file to see what codes are present
4. **Update Gradually**: Add mappings as you encounter new codes
5. **Back Up**: Keep a copy of your `subject_mappings.py` file

## Technical Details

- Mappings are stored in `app/utils/subject_mappings.py`
- The `normalize_subject_name()` function handles the conversion
- Applied during:
  - StudentChoice record creation (import)
  - SubjectChoice aggregation calculation
  - Recalculation when students are included/excluded
- Matching uses `.upper()` for case-insensitive comparison

## Troubleshooting

**Q: My mappings aren't showing up**  
A: If you added them via the web interface, they're only in memory. Edit the file directly and restart the app.

**Q: Some subjects are still showing unfriendly names**  
A: Check that the unfriendly name in your mapping exactly matches what's in the file (including spaces, underscores, etc.). Check the spelling and case.

**Q: Can I change a mapping after importing data?**  
A: Yes, but you'll need to re-process the upload to update the stored names. The mapping system applies during import.

## File Location
`app/utils/subject_mappings.py` - Edit this file to add permanent mappings
