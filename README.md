# Scottish School Subject Choice Analysis System

A Flask web application for analyzing student subject choices across S3, S4, and S5-6 year groups in Scottish Secondary Schools. Features OAuth authentication and data visualization.

## Features

- **OAuth Authentication**: Secure login integration
- **Data Upload**: Support for CSV and Excel files
- **Year Group Analysis**: Analyze S3, S4, and S5-6 subject choices
- **Subject Statistics**: Count and rank subject popularity
- **Comparison Tools**: Compare trends across year groups
- **User Dashboard**: Track uploads and view statistics

## Project Structure

```
python-flask-options-data/
├── app/
│   ├── __init__.py           # Application factory
│   ├── models.py             # Database models
│   ├── auth/                 # Authentication blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── main/                 # Main application blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── analysis/             # Data analysis blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── utils/                # Utility modules
│   │   ├── __init__.py
│   │   └── data_processor.py
│   └── templates/            # HTML templates
│       ├── base.html
│       ├── index.html
│       ├── dashboard.html
│       ├── upload.html
│       ├── results.html
│       └── compare.html
├── data/
│   ├── uploads/              # Uploaded data files
│   └── processed/            # Processed data
├── instance/                 # Instance-specific files (created on first run)
│   └── app.db               # SQLite database
├── app.py                   # Application entry point
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore
└── README.md

```

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Windows Setup Instructions

### 1. Install Python

If Python is not installed:
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer and check "Add Python to PATH"
3. Verify installation: `python --version`

### 2. Set Up the Project

Open PowerShell in the project directory:

```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env file with your OAuth credentials
notepad .env
```

Update the following in `.env`:
- `SECRET_KEY`: Generate a secure random key
- `OAUTH_CLIENT_ID`: Your OAuth client ID
- `OAUTH_CLIENT_SECRET`: Your OAuth client secret
- `OAUTH_AUTHORIZATION_URL`: OAuth provider's authorization URL
- `OAUTH_TOKEN_URL`: OAuth provider's token URL
- `OAUTH_USERINFO_URL`: OAuth provider's userinfo URL

### 5. Initialize the Database

```powershell
# The database will be created automatically on first run
python app.py
```

### 6. Run the Application

```powershell
# Development mode
python app.py
```

Visit `http://localhost:5000` in your browser.

## WSL Integration

Since you're running a PHP/MySQL project on WSL, you can also run this Flask app on WSL:

### WSL Setup

```bash
# In WSL terminal, navigate to project
cd /mnt/c/Users/colin/Documents/dev/python-flask-options-data

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The app will be accessible from both WSL and Windows at `http://localhost:5000`.

## Data File Format

### Expected CSV/Excel Structure

Your data files should contain student subject choices. Example formats:

**Option 1: Wide Format**
```csv
StudentID,Subject1,Subject2,Subject3,Subject4
001,Mathematics,Physics,Chemistry,English
002,History,Geography,English,Art
```

**Option 2: Long Format**
```csv
StudentID,Subject
001,Mathematics
001,Physics
002,History
002,Geography
```

The application will automatically detect columns containing subject data.

## OAuth Configuration

### Using HGS Index as OAuth Provider

This application is configured to use your existing HGS Index PHP/MySQL application as the OAuth provider.

**Quick Setup:**

1. Ensure HGS Index is running in WSL at `http://hgs-index.local`
2. The OAuth endpoints are already configured at:
   - Authorization: `http://hgs-index.local/oauth/authorize`
   - Token: `http://hgs-index.local/oauth/token`
   - User Info: `http://hgs-index.local/oauth/userinfo`

3. **Credentials are pre-configured** in `.env`:
   - Client ID: `flask-subject-analysis-app`
   - Client Secret: `flask-secret-key-change-in-production`

**Testing OAuth:**

1. Start the Flask app (already running at http://localhost:5000)
2. Click "Login"
3. Log in with your HGS Index teacher credentials
4. Authorize the application
5. You'll be redirected back and logged in!

For detailed OAuth setup and troubleshooting, see [OAUTH_SETUP.md](OAUTH_SETUP.md)

### Setting Up OAuth (General Instructions)

1. **Choose an OAuth Provider** (e.g., Google, Microsoft, GitHub)
2. **Register your application**:
   - Set redirect URI to: `http://localhost:5000/auth/callback`
   - Note your Client ID and Client Secret
3. **Update `.env` file** with provider details

### Example: Google OAuth

```env
OAUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
OAUTH_CLIENT_SECRET=your-google-client-secret
OAUTH_AUTHORIZATION_URL=https://accounts.google.com/o/oauth2/v2/auth
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
OAUTH_USERINFO_URL=https://www.googleapis.com/oauth2/v2/userinfo
```

## Usage

1. **Login**: Click "Login" and authenticate via OAuth
2. **Upload Data**: Navigate to "Upload Data" and select:
   - Year group (S3, S4, or S5-6)
   - Data file (CSV or Excel)
3. **View Results**: See subject choice statistics and rankings
4. **Compare**: Use the comparison tool to view trends across year groups

## Development

### Adding Features

The application uses Flask blueprints for modular development:

- **Authentication**: `app/auth/`
- **Main routes**: `app/main/`
- **Data analysis**: `app/analysis/`

### Database Models

- **User**: OAuth user information
- **DataUpload**: Tracking uploaded files
- **SubjectChoice**: Analyzed subject data

### Customization

Edit `app/utils/data_processor.py` to customize how data files are processed based on your specific data format.

## Troubleshooting

### Virtual Environment Issues

**PowerShell execution policy error**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Virtual environment not activating**:
- Ensure you're in the project directory
- Use the full path: `C:\Users\colin\Documents\dev\python-flask-options-data\venv\Scripts\Activate.ps1`

### Database Issues

If the database has issues:
```powershell
# Delete the database and restart
Remove-Item instance\app.db
python app.py
```

### Port Already in Use

If port 5000 is busy:
```python
# In app.py, change the port number:
app.run(debug=True, host='0.0.0.0', port=5001)
```

## Security Notes

- Never commit `.env` file to version control
- Use strong SECRET_KEY in production
- Keep OAuth credentials secure
- Use HTTPS in production environment

## Future Enhancements

- Data visualization charts
- Export analysis results to PDF
- Historical trend analysis
- Multi-school comparison
- Advanced filtering options
- API endpoints for integration

## License

This project is created for educational data analysis purposes.

## Support

For issues or questions, please refer to the documentation or create an issue in the project repository.
