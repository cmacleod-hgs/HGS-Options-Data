# Scottish School Subject Choice Analysis System

A Flask web application for analyzing student subject choices across S3, S4, and S5-6 year groups in Scottish Secondary Schools. Features OAuth authentication and data visualization.

## Features

- **OAuth Authentication**: Secure login integration
- **Data Upload**: Support for CSV and Excel files
- **Year Group Analysis**: Analyze S3, S4, and S5-6 subject choices
- **Subject Statistics**: Count and rank subject popularity
- **Comparison Tools**: Compare trends across year groups
- **User Dashboard**: Track uploads and view statistics
- **Subject Coincidence Matrix**: Analyze which subject combinations students choose
- **Database-Backed Subject Mappings**: Persistent friendly names for subjects

## Quick Start

1. Clone this repository
2. Create virtual environment: `python -m venv .venv`
3. Activate: `.\.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure OAuth credentials
6. Run: `python app.py`
7. Visit `http://localhost:5000`

## Documentation

- [Full Setup Instructions](README.md)
- [OAuth Configuration](OAUTH_SETUP.md)
- [OAuth Quick Reference](OAUTH_QUICK_REF.md)
- [Subject Mapping Guide](SUBJECT_MAPPINGS_GUIDE.md)

## Technology Stack

- Flask 3.0.0
- SQLAlchemy 3.1.1
- pandas
- jQuery + DataTables
- Chart.js

## License

Educational data analysis tool for Scottish Secondary Schools.
