# backend/utils/decorators.py

from functools import wraps
from flask import session, jsonify, request, current_app
import logging

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # --- DEBUG PRINTS ---
        print(f"--- DEBUG: Entering @login_required for endpoint: {request.endpoint} ---", flush=True)
        user_id = session.get("user_id")
        print(f"--- DEBUG: @login_required - session user_id: {user_id} ---", flush=True)
        # --- END DEBUG PRINTS ---
        if not user_id:
            logger.warning(f"Login required for {request.endpoint}: No user_id in session.")
            print(f"--- DEBUG: @login_required - Returning 401 ---", flush=True)
            return jsonify(msg="Authentication required"), 401

        print(f"--- DEBUG: @login_required - Proceeding for user {user_id} ---", flush=True)
        return f(*args, **kwargs)
    return decorated_function