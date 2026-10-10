from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """
    Application user record mapped directly to Supabase Auth.
    The primary key `id` stores the Supabase user UUID (`sub` from verified Supabase JWT).
    Passwords are never stored or managed in the application database.
    """
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships to user-scoped Gmail connection and classified messages
    gmail_connection = db.relationship('GmailConnection', backref='user', uselist=False, cascade="all, delete-orphan")
    classified_emails = db.relationship('ClassifiedEmail', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.id} ({self.email})>"


class GmailConnection(db.Model):
    """
    Stores encrypted Gmail OAuth credentials and watch state for an authenticated user.
    """
    __tablename__ = 'gmail_connections'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    gmail_address = db.Column(db.String(255), unique=True, nullable=True)
    encrypted_credentials_json = db.Column(db.Text, nullable=False)
    history_id = db.Column(db.String(255), nullable=True)
    watch_expiration = db.Column(db.BigInteger, nullable=True)
    monitoring_status = db.Column(db.String(50), default='inactive')  # 'active', 'inactive', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GmailConnection user_id={self.user_id} gmail={self.gmail_address} status={self.monitoring_status}>"


class ClassifiedEmail(db.Model):
    """
    Stores metadata and prediction results for an email processed by the spam classifier.
    Isolated per user.
    """
    __tablename__ = 'classified_emails'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message_id = db.Column(db.String(255), nullable=False)
    sender = db.Column(db.String(255), nullable=True)
    subject = db.Column(db.Text, nullable=True)
    snippet = db.Column(db.Text, nullable=True)
    prediction = db.Column(db.String(50), nullable=True)
    strength = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.String(100), nullable=True)
    body = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    spam_indicators = db.Column(db.Text, nullable=True)
    internal_date = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'message_id', name='_user_message_uc'),
        db.Index('idx_classified_emails_user_id', 'user_id'),
        db.Index('idx_classified_emails_internal_date', 'internal_date'),
    )

    def __repr__(self):
        return f"<ClassifiedEmail id={self.id} user_id={self.user_id} msg={self.message_id} pred={self.prediction}>"
