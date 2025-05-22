# main_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User, Preference
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/confirmation')
def confirmation():
    user_email = request.args.get('user_email')
    return render_template('confirmation.html', user_email=user_email)

@main_bp.route('/preferences', methods=['GET', 'POST'])
def preferences():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('auth.signup'))

    if request.method == 'POST':
        summary_time = request.form.get('summary_time')
        preference = user.preferences
        if preference:
            preference.summary_time = summary_time
            preference.prompt_last_updated = datetime.utcnow()
        else:
            preference = Preference(
                user=user,
                summary_time=summary_time
            )
            db.session.add(preference)
        db.session.commit()

        return redirect(url_for('main.first_summary', user_email=user_email, summary_time=summary_time))
    
    return render_template('preferences.html')

@main_bp.route('/first-summary')
def first_summary():
    user_email = request.args.get('user_email')
    summary_time = request.args.get('summary_time')
    return render_template('first_summary.html', user_email=user_email, summary_time=summary_time)

@main_bp.route('/account_management')
def account_management():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('auth.signup'))

    return render_template('account_management.html', user_email=user_email)

@main_bp.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('auth.signup'))

    if request.method == 'POST':
        pause_duration = request.form.get('pause_duration')
        user = User.query.filter_by(email=user_email).first()
        if pause_duration in ['1 week', '1 month']:
            pause_end = datetime.utcnow() + (timedelta(weeks=1) if pause_duration == '1 week' else timedelta(weeks=4))
            user.active = False
            user.pause_end = pause_end
        else:
            user.active = False
            user.pause_end = None

        db.session.commit()

        message = "You've been unsubscribed." if pause_duration == "unsubscribe" else f"Paused for {pause_duration}."
        return render_template('unsubscribe_confirmation.html', message=message)

    return render_template('unsubscribe.html')

@main_bp.route('/unpause', methods=['POST'])
def unpause():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=user_email).first()
    if user:
        user.active = True
        user.pause_end = None
        db.session.commit()
        message = "Your account is now active again."
    else:
        message = "User not found."

    return render_template('unpause_confirmation.html', message=message)
