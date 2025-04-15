from functools import wraps
from flask import session, jsonify, request, current_app
import logging, secrets

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            logger.warning("Login required: No user_id in session.")
            return jsonify(msg="Authentication required"), 401

        csrf_methods = ["POST", "PUT", "DELETE", "PATCH"]
        if request.method in csrf_methods:
            token_from_header = request.headers.get("X-CSRF-TOKEN")
            token_from_session = session.get("csrf_token")

            if not token_from_session:
                 logger.error(f"CRITICAL: No CSRF token found in session for logged-in user {user_id}. Regenerating.")
                 token_from_session = secrets.token_hex(16)
                 session['csrf_token'] = token_from_session
                 return jsonify(msg="CSRF configuration error"), 500

            if not token_from_header or token_from_header != token_from_session:
                logger.warning(f"CSRF validation failed for user {user_id}. Header='{token_from_header}', Session='{token_from_session}'.")
                return jsonify(msg="CSRF token validation failed"), 401

        return f(*args, **kwargs)
    return decorated_function