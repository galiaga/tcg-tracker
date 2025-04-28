# backend/routes/auth.py

# --- Imports ---
from flask import Blueprint, request, jsonify, current_app, session, url_for, render_template
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from backend import db, limiter, mail
from backend.models.user import User
from backend.utils.decorators import login_required
from backend.utils.validation import validate_password_strength_backend
from email_validator import validate_email, EmailNotValidError
import secrets
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import smtplib
from email.message import EmailMessage
from email import policy

# --- Blueprint and Bcrypt Setup ---
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()

# --- Helper Functions ---
def send_password_reset_email_manual(user):
    try:
        s = current_app.password_reset_serializer
        if not s:
             current_app.logger.error("Password reset serializer not found on app instance.")
             return False

        token = s.dumps(user.email, salt='password-reset-salt')
        frontend_base_url = current_app.config.get('FRONTEND_BASE_URL', 'http://localhost:8080')
        reset_url = f"{frontend_base_url}/reset-password/{token}"

        subject = "Reset Your Password"
        sender_email = current_app.config.get('MAIL_USERNAME')
        sender_password = current_app.config.get('MAIL_PASSWORD')
        recipient_email = user.email
        smtp_server = current_app.config.get('MAIL_SERVER')
        smtp_port = current_app.config.get('MAIL_PORT')

        if not all([sender_email, sender_password, smtp_server, smtp_port]):
            current_app.logger.error("Manual email sending failed: Missing mail configuration.")
            return False

        text_body = render_template('email/reset_password.txt', user=user, reset_url=reset_url)
        html_body = render_template('email/reset_password.html', user=user, reset_url=reset_url)

        msg = EmailMessage(policy=policy.SMTPUTF8)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg.set_content(text_body, subtype='plain')
        msg.add_alternative(html_body, subtype='html')

        current_app.logger.debug(f"Attempting manual SMTP connection to {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as connection:
            connection.starttls()
            connection.login(sender_email, sender_password)
            connection.send_message(msg)
            current_app.logger.info(f"Manual password reset email successfully sent via smtplib to {recipient_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        current_app.logger.error(f"SMTP Authentication Error during manual send to {user.email}: {e}", exc_info=False)
        return False
    except Exception as e:
        current_app.logger.error(f"Failed to send MANUAL password reset email to {user.email}: {e}", exc_info=True)
        return False

def create_user(username, email, password):
    try:
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, email=email.lower(), password_hash=hashed_password)
        db.session.add(new_user); db.session.commit()
        current_app.logger.info(f"User created successfully: {username} ({email})")
        return new_user
    except IntegrityError as e:
        db.session.rollback(); error_detail = str(e.orig).lower() if e.orig else ""; err_type = "DB_CONSTRAINT"; err_msg = "Database constraint violation during registration."; status_code = 400
        if 'unique constraint' in error_detail: status_code = 409
        if 'users.username' in error_detail or 'users_username_key' in error_detail: err_type = "DUPLICATE_USERNAME"; err_msg = "Username already exists."
        elif 'users.email' in error_detail or 'users_email_key' in error_detail: err_type = "DUPLICATE_EMAIL"; err_msg = "Email address already registered."
        current_app.logger.warning(f"IntegrityError during registration for {username}/{email}: {err_msg} - {e}"); return {"error": err_msg, "type": err_type}, status_code
    except Exception as e:
        db.session.rollback(); current_app.logger.error(f"Unexpected error during user creation for {username}/{email}: {e}", exc_info=True); return {"error": "An unexpected error occurred during registration.", "type": "UNKNOWN_ERROR"}, 500

# --- Registration Route ---
@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    data = request.get_json();
    if not data: return jsonify({"error": "Invalid JSON payload"}), 400
    username = data.get("username"); email = data.get("email"); password = data.get("password"); confirmation = data.get("confirmation")

    # --- Basic Field Checks ---
    if not all([username, email, password, confirmation]):
        return jsonify({"error": "Username, email, password, and confirmation are required"}), 400
    if password != confirmation:
        return jsonify({"error": "Passwords do not match."}), 400

    # --- Email Format Validation ---
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
        return jsonify({"error": f"Invalid email address format."}), 400

    # --- *** ADD PASSWORD STRENGTH VALIDATION HERE *** ---
    is_valid, errors = validate_password_strength_backend(password)
    if not is_valid:
        error_message = "Password does not meet security requirements."
        # Return validation errors similar to the reset route
        return jsonify({
            "error": error_message,
            "type": "VALIDATION_ERROR",
            "details": errors
        }), 400
    # --- *** END PASSWORD STRENGTH VALIDATION *** ---

    # --- Check for Duplicates ---
    if User.find_by_username(username):
        return jsonify({"error": "Username already exists.", "type": "DUPLICATE_USERNAME"}), 409
    if User.find_by_email(email):
        return jsonify({"error": "Email address already registered.", "type": "DUPLICATE_EMAIL"}), 409

    # --- Create User ---
    user_or_error = create_user(username, email, password)
    if isinstance(user_or_error, tuple):
        error_response, status_code = user_or_error
        return jsonify(error_response), status_code

    # --- Login User and Return Success ---
    new_user = user_or_error; session.clear(); session['user_id'] = new_user.id; session['username'] = new_user.username; session['csrf_token'] = secrets.token_hex(16); session.permanent = True
    current_app.logger.info(f"User {new_user.username} registered and logged in successfully. User ID: {new_user.id}")
    return jsonify({"username": new_user.username, "message": f"User {new_user.username} successfully registered and logged in."}), 201

# --- Login Route ---
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json();
    if not data: return jsonify({"error": "Invalid JSON payload"}), 400
    username = data.get("username"); password = data.get("password")
    if not username or not password: return jsonify({"error": "Username and password are required"}), 400
    user = User.find_by_username(username)
    if user and bcrypt.check_password_hash(user.password_hash, password):
        session.clear(); session['user_id'] = user.id; session['username'] = user.username
        if 'csrf_token' not in session: session['csrf_token'] = secrets.token_hex(16)
        session.permanent = True; current_app.logger.info(f"User {user.username} logged in successfully. User ID: {user.id}")
        return jsonify({"username": user.username, "message": "Login successful"}), 200
    else: current_app.logger.warning(f"Failed login attempt for username: {username}"); return jsonify({"error": "Invalid username or password"}), 401

# --- Forgot Password Route ---
@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per 15 minutes")
def forgot_password():
    data = request.get_json()
    email = data.get('email', '').lower()

    if not email:
        current_app.logger.warning("Forgot password request missing email.")
        return jsonify({"message": "If an account with that email exists, a password reset link has been sent."}), 200

    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        current_app.logger.warning(f"Forgot password attempt with invalid email format: {email}")
        return jsonify({"message": "If an account with that email exists, a password reset link has been sent."}), 200

    user = User.find_by_email(email)

    if user:
        current_app.logger.info(f"Password reset requested for existing user: {email}")
        send_password_reset_email_manual(user)
    else:
        current_app.logger.info(f"Password reset requested for non-existent email: {email}")

    return jsonify({"message": "If an account with that email exists, a password reset link has been sent."}), 200

# --- Reset Password Route ---
@auth_bp.route("/reset-password/<token>", methods=["POST"])
@limiter.limit("10 per minute")
def reset_password_with_token(token):
    data = request.get_json();
    if not data or not data.get('password'):
        return jsonify({"error": "New password is required."}), 400

    new_password = data.get('password')

    is_valid, errors = validate_password_strength_backend(new_password)
    if not is_valid:
        error_message = "Password does not meet security requirements."
        return jsonify({
            "error": error_message,
            "type": "VALIDATION_ERROR",
            "details": errors
        }), 400

    s = current_app.password_reset_serializer
    if not s:
        current_app.logger.error("Password reset serializer not found on app instance during reset attempt.")
        return jsonify({"error": "Password reset configuration error.", "type": "CONFIG_ERROR"}), 500

    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
        current_app.logger.info(f"Password reset token verified for email: {email}")
    except SignatureExpired:
        return jsonify({"error": "Password reset link has expired.", "type": "TOKEN_EXPIRED"}), 400
    except BadTimeSignature:
        return jsonify({"error": "Password reset link is invalid or has expired.", "type": "TOKEN_INVALID"}), 400
    except Exception as e:
        current_app.logger.error(f"Error verifying password reset token ({token}): {e}", exc_info=True)
        return jsonify({"error": "Password reset link is invalid or corrupted.", "type": "TOKEN_ERROR"}), 400

    user = User.find_by_email(email)
    if not user:
        current_app.logger.error(f"Password reset attempt for valid token ({token}), but user not found for email: {email}")
        return jsonify({"error": "User not found for this reset request.", "type": "USER_NOT_FOUND"}), 404

    try:
        new_hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        user.password_hash = new_hashed_password
        db.session.commit()
        current_app.logger.info(f"Password successfully reset for user: {user.username} ({user.email})")
        return jsonify({"message": "Your password has been successfully updated."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during password reset for user {user.email}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while updating your password. Please try again.", "type": "DB_ERROR"}), 500

# --- Logout Route ---
@auth_bp.route("/logout", methods=["POST"])
@limiter.limit("60 per minute")
def logout():
    user_id = session.get('user_id'); username = session.get('username'); session.clear()
    if username: current_app.logger.info(f"User {username} (ID: {user_id}) logged out successfully.")
    else: current_app.logger.info(f"Logout request processed, no active session found.")
    return jsonify({"message": "Logout successful"}), 200

# --- CSRF Token Route ---
@auth_bp.route("/csrf_token", methods=["GET"])
def get_csrf_token():
    if not session.get("user_id"): return jsonify({"error": "Not authenticated"}), 401
    token = session.get("csrf_token")
    if not token: token = secrets.token_hex(16); session['csrf_token'] = token; current_app.logger.warning(f"CSRF token requested by user {session.get('user_id')} but none found in session; generated new one.")
    return jsonify({"csrf_token": token}), 200

# --- Profile Route ---
@auth_bp.route("/profile", methods=["GET"])
@limiter.limit("60 per minute")
@login_required
def profile():
    user_id = session.get('user_id'); user = db.session.get(User, user_id)
    if not user or not user.is_active: session.clear(); current_app.logger.warning(f"Profile access attempt for non-existent or inactive user ID: {user_id}. Session cleared."); return jsonify({"error": "User data not found or account inactive, session cleared"}), 404
    return jsonify({"id": user.id, "username": user.username}), 200