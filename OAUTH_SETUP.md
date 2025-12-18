# OAuth Integration Setup Guide

## Overview

Your Flask Subject Choice Analysis application now uses your existing HGS Index PHP/MySQL application as an OAuth 2.0 provider for authentication.

## What Was Created

### OAuth Endpoints in HGS Index (~/projects/hgs-index/oauth/)

1. **authorize.php** - Authorization endpoint
   - Users log in to HGS Index and authorize the Flask app
   - Generates authorization codes
   - Handles user consent

2. **token.php** - Token endpoint
   - Exchanges authorization codes for access tokens
   - Validates client credentials
   - Issues Bearer tokens

3. **userinfo.php** - User information endpoint
   - Returns authenticated user details
   - Provides name, email, username

### Database Tables Created Automatically

The OAuth endpoints will automatically create these tables in your `hgs_index` MySQL database:

- `oauth_authorizations` - Tracks which users have authorized which apps
- `oauth_codes` - Stores temporary authorization codes (10-minute expiry)
- `oauth_access_tokens` - Stores access tokens (1-hour expiry)

## Configuration

### Client Credentials

The Flask app is registered with these credentials:

- **Client ID**: `flask-subject-analysis-app`
- **Client Secret**: `flask-secret-key-change-in-production`
- **Allowed Redirect URIs**:
  - `http://localhost:5000/auth/callback`
  - `http://127.0.0.1:5000/auth/callback`

### OAuth Flow

1. User clicks "Login" in Flask app
2. Redirected to HGS Index authorization page
3. If not logged into HGS Index, user logs in first
4. User sees authorization prompt (first time only)
5. Upon approval, redirected back to Flask app with authorization code
6. Flask app exchanges code for access token
7. Flask app retrieves user info and creates/updates user account
8. User is logged into Flask app

## Testing the Integration

### Prerequisites

1. **HGS Index must be running** in WSL:
   ```bash
   # In WSL
   cd ~/projects/hgs-index
   # Start your PHP server (Apache/nginx)
   ```

2. **HGS Index must be accessible** at `http://hgs-index.local`
   - Make sure your hosts file or DNS resolves this
   - Or update the URLs in `.env` to use `localhost` with appropriate port

3. **Flask app must be running** on Windows:
   ```powershell
   # In PowerShell (already running)
   # The app is currently running at http://localhost:5000
   ```

### Test the OAuth Flow

1. **Open your browser** and go to: `http://localhost:5000`

2. **Click "Login"** - You should be redirected to:
   `http://hgs-index.local/oauth/authorize`

3. **Log in to HGS Index** if not already logged in
   - Use your HGS Index teacher credentials

4. **Authorize the application** - You'll see:
   - Application name: "Subject Choice Analysis Application"
   - Your HGS Index username
   - Approve/Deny buttons

5. **Click "Authorize"** - You'll be redirected back to:
   `http://localhost:5000/auth/callback`

6. **You should be logged in** to the Flask app!
   - Check the dashboard at `http://localhost:5000/dashboard`

## Troubleshooting

### "Connection refused" errors

**Problem**: Flask app can't reach HGS Index OAuth endpoints

**Solution**: 
- Verify HGS Index is running in WSL
- Check that `http://hgs-index.local` is accessible from Windows
- Try using `http://localhost:PORT` instead if hgs-index.local doesn't resolve
- Update `.env` file with correct URLs

### "Invalid client_id" error

**Problem**: Client credentials don't match

**Solution**:
- Verify `.env` has correct `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET`
- Check `oauth/authorize.php` has matching client in `$valid_clients` array

### "Invalid redirect_uri" error

**Problem**: Redirect URI not in allowed list

**Solution**:
- Verify the redirect URI in `.env` matches one in `oauth/authorize.php`
- Check for http vs https mismatch
- Ensure no trailing slashes

### Database connection errors

**Problem**: OAuth endpoints can't connect to MySQL

**Solution**:
- Verify MySQL is running in WSL
- Check database credentials in the OAuth PHP files match your HGS Index setup
- Ensure `hgs_index` database exists

### Users can't log in after OAuth

**Problem**: OAuth works but Flask app shows error

**Solution**:
- Check Flask app logs for specific errors
- Verify user email is being retrieved from HGS Index
- Check that `teacher_information` table has `Email` column

## Security Notes

### For Development

Currently configured for local development:
- Using HTTP (not HTTPS)
- Client secret is simple
- Access tokens valid for 1 hour

### For Production

**IMPORTANT**: Before deploying to production:

1. **Use HTTPS** everywhere:
   - Update all URLs to use `https://`
   - Ensure SSL certificates are valid

2. **Change client secret**:
   - Generate a strong random secret
   - Update in both `.env` and `oauth/token.php`

3. **Secure database**:
   - Don't hardcode credentials in PHP files
   - Use environment variables or config files

4. **Add rate limiting**:
   - Prevent brute force attacks on OAuth endpoints

5. **Add logging**:
   - Track OAuth authorization attempts
   - Monitor for suspicious activity

## Customization

### Adding More OAuth Clients

To allow other apps to use HGS Index OAuth:

Edit `oauth/authorize.php` and `oauth/token.php`:

```php
$valid_clients = [
    'flask-subject-analysis-app' => [
        'name' => 'Subject Choice Analysis Application',
        'secret' => 'flask-secret-key',
        'redirect_uris' => [...]
    ],
    'new-app-client-id' => [
        'name' => 'New Application Name',
        'secret' => 'new-app-secret',
        'redirect_uris' => [
            'http://localhost:3000/callback'
        ]
    ]
];
```

### Customizing User Info

Edit `oauth/userinfo.php` to return additional fields:

```php
echo json_encode([
    'sub' => $user['Username'],
    'name' => trim(($user['FirstName'] ?? '') . ' ' . ($user['LastName'] ?? '')),
    'email' => $user['Email'],
    'preferred_username' => $user['Username'],
    // Add custom fields:
    'department' => $user['Department'] ?? '',
    'role' => $user['Role'] ?? 'teacher'
]);
```

### Changing Token Expiry

In `oauth/token.php`, modify:

```php
// Current: 1 hour (3600 seconds)
$expiresAt = date('Y-m-d H:i:s', time() + 3600);

// Change to 24 hours:
$expiresAt = date('Y-m-d H:i:s', time() + 86400);
```

## Next Steps

1. **Test the OAuth flow** end-to-end
2. **Verify user data** is correctly retrieved
3. **Upload sample data** to test the subject analysis features
4. **Review security settings** before any production use

## Support

If you encounter issues:

1. Check the browser console for JavaScript errors
2. Check Flask app logs in the terminal
3. Check PHP error logs in WSL: `tail -f /var/log/apache2/error.log`
4. Verify database tables were created: 
   ```sql
   SHOW TABLES LIKE 'oauth_%';
   ```
