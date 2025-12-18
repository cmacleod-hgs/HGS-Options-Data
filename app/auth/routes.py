"""
Authentication routes
"""
from flask import render_template, redirect, url_for, request, session, flash, current_app
from flask_login import login_user, logout_user, login_required
from app.auth import auth_bp
from app.models import User
from app import db
from authlib.integrations.requests_client import OAuth2Session
from datetime import datetime
import secrets


@auth_bp.route('/login')
def login():
    """Initiate OAuth login"""
    # Create OAuth session
    oauth = OAuth2Session(
        current_app.config['OAUTH_CLIENT_ID'],
        current_app.config['OAUTH_CLIENT_SECRET'],
        redirect_uri=current_app.config['OAUTH_REDIRECT_URI']
    )
    
    # Get authorization URL (authlib generates the state token)
    authorization_url, state = oauth.create_authorization_url(
        current_app.config['OAUTH_AUTHORIZATION_URL']
    )
    
    # Store the state token that authlib actually uses
    session['oauth_state'] = state
    
    return redirect(authorization_url)


@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback"""
    current_app.logger.info("=== CALLBACK CALLED ===")
    current_app.logger.info(f"Request URL: {request.url}")
    current_app.logger.info(f"Request args: {dict(request.args)}")
    
    # Verify state token
    received_state = request.args.get('state')
    stored_state = session.get('oauth_state')
    
    current_app.logger.info(f"Received state: {received_state}")
    current_app.logger.info(f"Stored state: {stored_state}")
    
    if received_state != stored_state:
        flash(f'Invalid state token. Received: {received_state}, Expected: {stored_state}', 'error')
        return redirect(url_for('main.index'))
    
    # Exchange code for token
    oauth = OAuth2Session(
        current_app.config['OAUTH_CLIENT_ID'],
        current_app.config['OAUTH_CLIENT_SECRET'],
        redirect_uri=current_app.config['OAUTH_REDIRECT_URI']
    )
    
    try:
        # Get the authorization code from callback
        code = request.args.get('code')
        current_app.logger.info(f"Authorization code: {code}")
        
        # Manually prepare token request
        import requests
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': current_app.config['OAUTH_REDIRECT_URI'],
            'client_id': current_app.config['OAUTH_CLIENT_ID'],
            'client_secret': current_app.config['OAUTH_CLIENT_SECRET']
        }
        
        current_app.logger.info(f"Token URL: {current_app.config['OAUTH_TOKEN_URL']}")
        current_app.logger.info(f"Token data: {token_data}")
        
        # Make POST request to token endpoint
        token_response = requests.post(
            current_app.config['OAUTH_TOKEN_URL'],
            data=token_data
        )
        
        current_app.logger.info(f"Token response status: {token_response.status_code}")
        current_app.logger.info(f"Token response body: {token_response.text[:500]}")  # First 500 chars
        
        if token_response.status_code != 200:
            current_app.logger.error(f"Token request failed: {token_response.text}")
            raise Exception(f"Token request failed: {token_response.text}")
        
        token = token_response.json()
        current_app.logger.info(f"Token received: {token}")
        
        # Get user info using the access token
        user_info_response = requests.get(
            current_app.config['OAUTH_USERINFO_URL'],
            headers={'Authorization': f"Bearer {token['access_token']}"}
        )
        
        current_app.logger.info(f"Userinfo response status: {user_info_response.status_code}")
        current_app.logger.info(f"Userinfo response body: {user_info_response.text[:500]}")
        
        if user_info_response.status_code != 200:
            error_body = user_info_response.text if user_info_response.text else '(empty response)'
            raise Exception(f"Userinfo request failed ({user_info_response.status_code}): {error_body}")
        
        if not user_info_response.text.strip():
            raise Exception("Userinfo endpoint returned empty response")
            
        user_info = user_info_response.json()
        
        print(f"DEBUG - User info: {user_info}")
        
        # Find or create user
        user = User.query.filter_by(email=user_info.get('email')).first()
        if not user:
            user = User(
                email=user_info.get('email'),
                name=user_info.get('name'),
                oauth_provider='oauth',
                oauth_id=user_info.get('sub')
            )
            db.session.add(user)
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log user in
        login_user(user)
        flash('Successfully logged in!', 'success')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        import traceback
        error_msg = f"""
=== OAuth Error ===
Time: {datetime.utcnow()}
Exception type: {type(e).__name__}
Exception message: {str(e)}
Traceback:
{traceback.format_exc()}
"""
        # Write to file
        with open('oauth_error.log', 'w') as f:
            f.write(error_msg)
        
        current_app.logger.error(f'OAuth error: {str(e)}')
        flash(f'Authentication failed: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
