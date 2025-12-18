# Quick OAuth Reference

## URLs
- **Flask App**: http://localhost:5000
- **HGS Index**: http://hgs-index.local
- **Authorization**: http://hgs-index.local/oauth/authorize
- **Token**: http://hgs-index.local/oauth/token  
- **User Info**: http://hgs-index.local/oauth/userinfo

## Client Credentials
- **Client ID**: flask-subject-analysis-app
- **Client Secret**: flask-secret-key-change-in-production

## Test Login Flow
1. Go to http://localhost:5000
2. Click "Login"
3. Log in to HGS Index with teacher credentials
4. Authorize the app
5. You'll be redirected back and logged in!

## Database Tables (MySQL: hgs_index)
- `oauth_authorizations` - User consents
- `oauth_codes` - Temporary codes (10 min)
- `oauth_access_tokens` - Access tokens (1 hour)

## Quick Troubleshoot
- **Can't reach OAuth endpoints?** → Make sure HGS Index is running in WSL
- **Invalid client?** → Check CLIENT_ID and CLIENT_SECRET in .env
- **Database errors?** → Verify MySQL is running, tables will auto-create
