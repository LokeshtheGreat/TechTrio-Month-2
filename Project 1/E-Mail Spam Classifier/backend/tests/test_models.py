import pytest
from models import User, GmailConnection, ClassifiedEmail

def test_user_model_has_no_password_field():
    """Verify that User model does NOT have password_hash or password columns."""
    columns = [c.name for c in User.__table__.columns]
    assert 'password_hash' not in columns
    assert 'password' not in columns
    assert 'id' in columns
    assert 'email' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns

def test_user_id_column_properties():
    """Verify that User.id is a String(36) primary key designed for Supabase UUIDs."""
    id_col = User.__table__.columns['id']
    assert id_col.primary_key is True
    assert id_col.type.length == 36

def test_gmail_connection_relationships_and_foreign_keys():
    """Verify GmailConnection foreign key to users.id and unique constraints."""
    user_id_col = GmailConnection.__table__.columns['user_id']
    assert user_id_col.unique is True
    assert len(user_id_col.foreign_keys) == 1
    fk = list(user_id_col.foreign_keys)[0]
    assert fk.target_fullname == 'users.id'
    assert fk.ondelete == 'CASCADE'

def test_classified_email_constraints():
    """Verify ClassifiedEmail unique constraint on (user_id, message_id)."""
    table = ClassifiedEmail.__table__
    user_id_col = table.columns['user_id']
    assert len(user_id_col.foreign_keys) == 1
    fk = list(user_id_col.foreign_keys)[0]
    assert fk.target_fullname == 'users.id'
    assert fk.ondelete == 'CASCADE'

    # Check unique constraint on (user_id, message_id)
    u_constraints = [c for c in table.constraints if getattr(c, 'name', '') == '_user_message_uc']
    assert len(u_constraints) == 1
    col_names = [col.name for col in u_constraints[0].columns]
    assert 'user_id' in col_names
    assert 'message_id' in col_names


def test_classified_email_rich_columns():
    """Verify ClassifiedEmail model includes body, body_html, spam_indicators, and internal_date columns."""
    columns = [c.name for c in ClassifiedEmail.__table__.columns]
    assert 'body' in columns
    assert 'body_html' in columns
    assert 'spam_indicators' in columns
    assert 'internal_date' in columns
