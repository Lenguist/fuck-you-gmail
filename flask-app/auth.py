# auth.py
from flask import Blueprint, redirect, url_for, session, current_app
from flask_dance.contrib.google import make_google_blueprint, google
from models import db, User
from cryptography.fernet import Fernet
import json

auth_bp = Blueprint('auth', __name__)

def init_auth(app):
    # Initialize encryption cipher and Google OAuth blueprint
    cipher = Fernet(app.config['ENCRYPTION_KEY'])
    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        scope=['https://www.googleapis.com/auth/gmail.readonly', 'openid', 'email', 'profile'],
        redirect_to='auth.google_login'
    )

    # Register the Google OAuth blueprint
    app.register_blueprint(google_bp, url_prefix='/login')

    # Store cipher in the app config for access in routes
    app.config['CIPHER'] = cipher

    # Register the auth blueprint
    app.register_blueprint(auth_bp)

@auth_bp.route('/signup')
def signup():
    if not google.authorized:
        return redirect(url_for('google.login'))
    else:
        return redirect(url_for('auth.google_login'))

@auth_bp.route('/signup/google/authorized')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))

    resp = google.get('/oauth2/v2/userinfo')
    if not resp.ok:
        return "Failed to fetch user info from Google."

    user_info = resp.json()
    user_email = user_info['email']

    # Access the cipher from the app config
    cipher = current_app.config['CIPHER']

    # Get credentials
    token = google.token['access_token']
    refresh_token = google.token.get('refresh_token')
    token_uri = google_bp.session.token_url
    client_id = google_bp.client_id
    client_secret = google_bp.client_secret
    scopes = google_bp.scope

    creds_dict = {
        'token': token,
        'refresh_token': refresh_token,
        'token_uri': token_uri,
        'client_id': client_id,
        'client_secret': client_secret,
        'scopes': scopes
    }

    # Encrypt the OAuth token
    encrypted_token = cipher.encrypt(json.dumps(creds_dict).encode())

    # Store or update the user in the database
    user = User.query.filter_by(email=user_email).first()
    if user:
        user.oauth_token = encrypted_token.decode()
        user.active = True
    else:
        user = User(
            email=user_email,
            oauth_token=encrypted_token.decode(),
            active=True
        )
        db.session.add(user)
    db.session.commit()

    # Store user email in session
    session['user_email'] = user_email

    return redirect(url_for('main.confirmation', user_email=user_email))
