from flask import Flask, render_template, request, redirect, url_for, session, make_response
from datetime import datetime, timedelta
# from flask_apscheduler import APScheduler
# from gmail_auth import authenticate_gmail
# import mysql.connector
import json
# from cryptography.fernet import Fernet
# import google.oauth2.credentials
# from google.auth.transport.requests import Request
# from database_connect import get_secret
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Store this securely

# APScheduler for scheduling daily tasks
# scheduler = APScheduler()

# Setup encryption for sensitive data
# cipher = Fernet(os.getenv('ENCRYPTION_KEY'))  # Store your encryption key securely

# Database connection setup
'''
def connect_to_mysql(username, password, dbname='email_summarizer'):
    """Establish a connection to the MySQL database."""
    host = "email-summarizer-dev.cluster-cfoais5hmxcr.us-east-1.rds.amazonaws.com"
    port = 3306
    connection = mysql.connector.connect(
        user=username,
        password=password,
        host=host,
        port=port,
        database=dbname
    )
    return connection
'''

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Signup page (Google OAuth)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle the signup process."""
    if request.method == 'POST':
        # For demo purposes, simulate a user email
        user_email = request.form.get('email', 'user@example.com')
        # Store user email in session for subsequent requests
        session['user_email'] = user_email

        return redirect(url_for('confirmation', user_email=user_email))
    
    return render_template('signup.html')

# Confirmation page after sign-in
@app.route('/confirmation')
def confirmation():
    """Displays a confirmation message after successful signup."""
    user_email = request.args.get('user_email')
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

        # For demo purposes, store the summary time in the session
        session['summary_time'] = summary_time

        return redirect(url_for('first_summary', user_email=user_email, summary_time=summary_time))

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
    if request.method == 'POST':
        pause_duration = request.form.get('pause_duration')  # "1 week", "1 month", or "unsubscribe"
        user_email = session.get('user_email')
        
        # For demo purposes, simulate the action
        if pause_duration in ['1 week', '1 month']:
            message = f"Paused for {pause_duration}."
        else:
            message = "You've been unsubscribed."

        return render_template('unsubscribe_confirmation.html', message=message)
    
    return render_template('unsubscribe.html')

# Unpause page
@app.route('/unpause', methods=['POST'])
def unpause():
    """Allow a user to reactivate their account if it's paused."""
    user_email = session.get('user_email')
    
    # For demo purposes, simulate the action
    message = "Your account is now active again."

    return render_template('unpause_confirmation.html', message=message)

# First Summary page
@app.route('/first-summary')
def first_summary():
    """Display the first summary page with user email and selected summary time."""
    user_email = request.args.get('user_email')
    summary_time = request.args.get('summary_time')
    return render_template('first_summary.html', user_email=user_email, summary_time=summary_time)

# Initialize and start the scheduler
# scheduler.init_app(app)
# scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
