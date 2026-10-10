from flask import Blueprint, request, jsonify, g
from models import db, User
from utils.supabase_auth import require_supabase_auth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/sync', methods=['POST'])
@require_supabase_auth
def sync_user():
    """
    Syncs the authenticated Supabase user profile into the application database.
    Does not handle or store passwords.
    """
    user_id = g.user_id
    email = g.user_email or (request.json.get('email') if request.is_json else '')

    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id, email=email)
        db.session.add(user)
    else:
        if email and user.email != email:
            user.email = email
    db.session.commit()

    return jsonify({'user': {'id': user.id, 'email': user.email}}), 200


@auth_bp.route('/me', methods=['GET'])
@require_supabase_auth
def get_me():
    """
    Returns the authenticated Supabase user profile.
    """
    user = User.query.get(g.user_id)
    if not user:
        return jsonify({'id': g.user_id, 'email': g.user_email, 'synced': False}), 200

    return jsonify({'id': user.id, 'email': user.email, 'synced': True}), 200
