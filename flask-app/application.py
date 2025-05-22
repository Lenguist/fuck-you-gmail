import os
import json
import logging
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

import mysql.connector
from mysql.connector import Error

from cryptography.fernet import Fernet

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.oauth2.credentials

# Set up logging
logging.basicConfig(level=logging.INFO)

# Configuration
class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'your-encryption-key')
    AWS_SECRET_NAME = os.environ.get('AWS_SECRET_NAME', 'rds!cluster-3ccc57c2-2cb2-4732-8128-430ea57eb383')
    AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'us-east-1')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'email-summarizer-dev.cluster-cfoais5hmxcr.us-east-1.rds.amazonaws.com')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
    MYSQL_DB = os.environ.get('MYSQL_DB', 'email_summarizer')
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    SESSION_TYPE = 'filesystem'  # Or other session storage method

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
Session(app)  # Initialize the session
cipher = Fernet(app.config['ENCRYPTION_KEY'])

# Function to retrieve secrets from AWS Secrets Manager
def get_secret():
    secret_name = app.config['AWS_SECRET_NAME']
    region_name = app.config['AWS_REGION_NAME']

    # Create a Secrets Manager client
    session_boto = boto3.session.Session()
    client = session_boto.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        # Retrieve the secret from AWS Secrets Manager
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        logging.error(f"Error retrieving secret: {e}")
        raise e

    # Extract and parse the secret
    secret = json.loads(get_secret_value_response['SecretString'])

    # Extract only the username and password
    username = secret.get('username')
    password = secret.get('password')

    if not username or not password:
        raise ValueError("The secret must contain 'username' and 'password' fields.")

    return username, password

# Function to connect to MySQL database
def connect_to_mysql(username, password):
    """Establish a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            user=username,
            password=password,
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            database=app.config['MYSQL_DB']
        )
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Error connecting to MySQL: {err}")
        raise err

# Helper function to get user ID from email
def get_user_id(user_email):
    try:
        username, password = get_secret()
        connection = connect_to_mysql(username, password)
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = %s;", (user_email,))
        user_id_result = cursor.fetchone()
        if user_id_result:
            return user_id_result[0]
        else:
            return None
    except mysql.connector.Error as err:
        logging.error(f"Error: {err}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Function to authenticate with Gmail
def authenticate_gmail():
    """Authenticate the user with Gmail and return their email and OAuth token."""
    # In production, use a proper OAuth flow for web applications
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', app.config['SCOPES'])
    creds = flow.run_local_server(port=0)

    # Extract the user's email address using the Gmail API
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    user_email = profile['emailAddress']

    # Return the user's email and OAuth credentials as a dictionary
    return user_email, {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Signup page (Google OAuth)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle the signup process, including Google OAuth and database updates."""
    if request.method == 'POST':
        try:
            user_email, creds_dict = authenticate_gmail()  # Get email and credentials dictionary

            # Encrypt the OAuth token
            encrypted_token = cipher.encrypt(json.dumps(creds_dict).encode()).decode()

            username, password = get_secret()
            connection = connect_to_mysql(username, password)
            cursor = connection.cursor()

            # Insert user data into the users table or update if already exists
            cursor.execute("""
                INSERT INTO users (email, oauth_token, active)
                VALUES (%s, %s, TRUE)
                ON DUPLICATE KEY UPDATE oauth_token = %s, active = TRUE;
            """, (user_email, encrypted_token, encrypted_token))

            connection.commit()
        except mysql.connector.Error as err:
            logging.error(f"Error: {err}")
            flash("An error occurred while signing up.")
            return redirect(url_for('signup'))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        # Store user email in session for subsequent requests
        session['user_email'] = user_email

        return redirect(url_for('confirmation'))
    
    return render_template('signup.html')

# Confirmation page after sign-in
@app.route('/confirmation')
def confirmation():
    """Displays a confirmation message after successful signup."""
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('signin'))
    return render_template('confirmation.html', user_email=user_email)

# Preferences page (for selecting the time to receive summary)
@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    """Allow users to view and update their summary time preferences."""
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('signin'))

    if request.method == 'POST':
        summary_time = request.form.get('summary_time')  # Morning, Afternoon, Evening

        try:
            user_id = get_user_id(user_email)
            if user_id is None:
                flash("User not found.")
                return redirect(url_for('preferences'))

            username, password = get_secret()
            connection = connect_to_mysql(username, password)
            cursor = connection.cursor()

            cursor.execute("SELECT preference_id FROM preferences WHERE user_id = %s;", (user_id,))
            preference_exists = cursor.fetchone()

            if preference_exists:
                cursor.execute("""
                    UPDATE preferences SET summary_time = %s, prompt_last_updated = NOW() WHERE user_id = %s;
                """, (summary_time, user_id))
            else:
                cursor.execute("""
                    INSERT INTO preferences (user_id, summary_time, prompt_last_updated)
                    VALUES (%s, %s, NOW());
                """, (user_id, summary_time))

            connection.commit()
            flash("Preferences updated successfully.")
        except mysql.connector.Error as err:
            logging.error(f"Error: {err}")
            flash("An error occurred while saving preferences.")
            return redirect(url_for('preferences'))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return redirect(url_for('first_summary'))
    
    return render_template('preferences.html')

# Sign-in for returning users
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    """Authenticate returning users to access account management."""
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('signup'))

    return redirect(url_for('account_management'))

# Account management page
@app.route('/account_management')
def account_management():
    """Display options for users to manage their account."""
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('signin'))

    return render_template('account_management.html', user_email=user_email)

# Unsubscribe page
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    """Handle unsubscription and prompt users to pause instead."""
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('signin'))

    if request.method == 'POST':
        pause_duration = request.form.get('pause_duration')  # "1 week", "1 month", or "unsubscribe"

        try:
            username, password = get_secret()
            connection = connect_to_mysql(username, password)
            cursor = connection.cursor()

            if pause_duration in ['1 week', '1 month']:
                pause_end = datetime.now() + (timedelta(weeks=1) if pause_duration == '1 week' else timedelta(weeks=4))
                cursor.execute("""
                    UPDATE users SET active = FALSE, pause_end = %s WHERE email = %s;
                """, (pause_end, user_email))
                message = f"Paused for {pause_duration}."
            else:
                cursor.execute("""
                    UPDATE users SET active = FALSE, pause_end = NULL WHERE email = %s;
                """, (user_email,))
                message = "You've been unsubscribed."

            connection.commit()
            flash(message)
        except mysql.connector.Error as err:
            logging.error(f"Error: {err}")
            flash("An error occurred while processing your request.")
            return redirect(url_for('unsubscribe'))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return render_template('unsubscribe_confirmation.html', message=message)
    
    return render_template('unsubscribe.html')

# Unpause page
@app.route('/unpause', methods=['POST'])
def unpause():
    """Allow a user to reactivate their account if it's paused."""
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('signin'))

    try:
        username, password = get_secret()
        connection = connect_to_mysql(username, password)
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE users SET active = TRUE, pause_end = NULL WHERE email = %s;
        """, (user_email,))

        connection.commit()
        message = "Your account is now active again."
        flash(message)
    except mysql.connector.Error as err:
        logging.error(f"Error: {err}")
        flash("An error occurred while processing your request.")
        return redirect(url_for('account_management'))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('unpause_confirmation.html', message=message)

# First Summary page
@app.route('/first_summary')
def first_summary():
    """Display the first summary page with user email and selected summary time."""
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('signin'))

    # Retrieve summary time from preferences
    try:
        user_id = get_user_id(user_email)
        if user_id is None:
            flash("User not found.")
            return redirect(url_for('preferences'))

        username, password = get_secret()
        connection = connect_to_mysql(username, password)
        cursor = connection.cursor()
        cursor.execute("SELECT summary_time FROM preferences WHERE user_id = %s;", (user_id,))
        result = cursor.fetchone()
        if result:
            summary_time = result[0]
        else:
            summary_time = None
    except mysql.connector.Error as err:
        logging.error(f"Error: {err}")
        flash("An error occurred while retrieving preferences.")
        summary_time = None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('first_summary.html', user_email=user_email, summary_time=summary_time)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
