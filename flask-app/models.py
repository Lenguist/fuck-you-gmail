# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    oauth_token = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True)
    pause_end = db.Column(db.DateTime, nullable=True)

    preferences = db.relationship('Preference', backref='user', uselist=False)

class Preference(db.Model):
    __tablename__ = 'preferences'

    preference_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    summary_time = db.Column(db.String(50), nullable=False)
    prompt_last_updated = db.Column(db.DateTime, default=datetime.utcnow)
