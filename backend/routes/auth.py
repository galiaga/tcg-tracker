# backend/routes/auth.py

# --- Imports ---
from flask import Blueprint, request, jsonify, current_app, session, url_for, render_template
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from backend import db, limiter, csrf
from backend.models.user import User # User model now has first_name, last_name, etc.
from backend.utils.decorators import login_required
from backend.utils.validation import validate_password_strength_backend
from email_validator import validate_email, EmailNotValidError
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_wtf.csrf import generate_csrf
import smtplib
from email.message import EmailMessage
from email import policy

# --- Blueprint and Bcrypt Setup ---
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()
csrf.exempt(auth_bp)

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

        # Use user.first_name for personalization if available
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

# --- UPDATED create_user Helper ---
def create_user(first_name, last_name, email, password, username=None): # Added first/last name, username optional
    """Creates and saves a new user."""
    try:
        # Ensure email is lowercase
        email = email.lower()
        # Trim whitespace from names
        first_name = first_name.strip()
        last_name = last_name.strip()
        # Handle optional username (ensure uniqueness if provided later)
        username = username.strip() if username else None

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username, # Will be None if not provided
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        current_app.logger.info(f"User created successfully: {first_name} {last_name} ({email}), Username: {username or 'N/A'}")
        return new_user
    except IntegrityError as e:
        db.session.rollback()
        error_detail = str(e.orig).lower() if e.orig else ""
        err_type = "DB_CONSTRAINT"
        err_msg = "Database constraint violation during registration."
        status_code = 400 # Default

        if 'unique constraint' in error_detail or 'duplicate key value violates unique constraint' in error_detail:
            status_code = 409 # Conflict
            # Check which constraint failed (adjust keywords based on PostgreSQL vs SQLite errors)
            if 'users_email_key' in error_detail or 'users.email' in error_detail:
                err_type = "DUPLICATE_EMAIL"
                err_msg = "Email address already registered."
            elif 'users_username_key' in error_detail or 'users.username' in error_detail:
                 # This should only happen if username is provided and is a duplicate
                err_type = "DUPLICATE_USERNAME"
                err_msg = "Username already exists."
            else:
                err_msg = "A unique value conflict occurred." # More generic unique error

        current_app.logger.warning(f"IntegrityError during registration for {first_name} {last_name}/{email}: {err_msg} - {e}")
        return {"error": err_msg, "type": err_type}, status_code
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error during user creation for {first_name} {last_name}/{email}: {e}", exc_info=True)
        return {"error": "An unexpected error occurred during registration.", "type": "UNKNOWN_ERROR"}, 500

# --- UPDATED Registration Route ---
@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # --- Get Required Fields ---
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")
    confirmation = data.get("confirmation")
    # --- Get Optional Field ---
    username = data.get("username") # Optional

    # --- Basic Field Checks ---
    required_fields = {"first_name": first_name, "last_name": last_name, "email": email, "password": password, "confirmation": confirmation}
    missing_fields = [name for name, value in required_fields.items() if not value]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # --- Basic Name Validation (Example: ensure not just whitespace) ---
    if not first_name.strip() or not last_name.strip():
         return jsonify({"error": "First name and last name cannot be empty."}), 400

    if password != confirmation:
        return jsonify({"error": "Passwords do not match."}), 400

    # --- Email Format Validation ---
    try:
        # Consider check_deliverability=True in production if needed, but it's slower
        validate_email(email, check_deliverability=False)
        email = email.lower() # Normalize email
    except EmailNotValidError as e:
        return jsonify({"error": f"Invalid email address format."}), 400

    # --- Password Strength Validation ---
    is_valid, errors = validate_password_strength_backend(password)
    if not is_valid:
        error_message = "Password does not meet security requirements."
        return jsonify({
            "error": error_message,
            "type": "VALIDATION_ERROR",
            "details": errors
        }), 400

    # --- Check for Duplicate Email ---
    if User.find_by_email(email):
        return jsonify({"error": "Email address already registered.", "type": "DUPLICATE_EMAIL"}), 409

    # --- Check for Duplicate Username (ONLY if provided and needs to be unique) ---
    if username:
        username = username.strip()
        if not username: # Treat empty string as None
            username = None
        elif User.find_by_username(username):
             # This check assumes your model still enforces unique=True on username
            return jsonify({"error": "Username already exists.", "type": "DUPLICATE_USERNAME"}), 409

    # --- Create User ---
    # Pass optional username to the helper
    user_or_error = create_user(first_name, last_name, email, password, username=username)

    if isinstance(user_or_error, tuple):
        # Error occurred during creation
        error_response, status_code = user_or_error
        return jsonify(error_response), status_code

    # --- Login User and Return Success ---
    new_user = user_or_error
    session.clear()
    session['user_id'] = new_user.id
    # Store full name or first name for potential greeting? Optional.
    session.permanent = True # Make session persistent

    current_app.logger.info(f"User {new_user.full_name} (ID: {new_user.id}) registered and logged in successfully.")
    # Return relevant user info (avoid sending password hash!)
    return jsonify({
        "message": f"User {new_user.first_name} successfully registered and logged in.",
        "user": {
            "id": new_user.id,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "email": new_user.email,
            "username": new_user.username # Include if relevant
        }
     }), 201

# --- UPDATED Login Route ---
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # --- Use Email for Login ---
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # --- Find user by email (case-insensitive) ---
    user = User.find_by_email(email)

    # --- Check Password ---
    if user and bcrypt.check_password_hash(user.password_hash, password):
        # --- Login Success ---
        session.clear()
        session['user_id'] = user.id
        session.permanent = True
        current_app.logger.info(f"User {user.full_name} (ID: {user.id}) logged in successfully via email.")
        # Return relevant user info
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username # Include if relevant
            }
        }), 200
    else:
        # --- Login Failure ---
        current_app.logger.warning(f"Failed login attempt for email: {email}")
        # Generic error message for security
        return jsonify({"error": "Invalid email or password"}), 401


# --- Forgot Password Route ---
# (No changes needed - already uses email)
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

    # Generic message for security (don't reveal if email exists)
    return jsonify({"message": "If an account with that email exists, a password reset link has been sent."}), 200


# --- Reset Password Route ---
# (No changes needed - already uses email via token)
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
        email = s.loads(token, salt='password-reset-salt', max_age=3600) # Default 1 hour expiry
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
        # Avoid confirming user existence based on token validity
        return jsonify({"error": "Password reset link is invalid or user not found.", "type": "TOKEN_USER_MISMATCH"}), 400 # Changed from 404

    try:
        new_hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        user.password_hash = new_hashed_password
        db.session.commit()
        current_app.logger.info(f"Password successfully reset for user: {user.full_name} ({user.email})") # Use full_name
        return jsonify({"message": "Your password has been successfully updated."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during password reset for user {user.email}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while updating your password. Please try again.", "type": "DB_ERROR"}), 500


# --- UPDATED Logout Route ---
@auth_bp.route("/logout", methods=["POST"])
@limiter.limit("60 per minute")
def logout():
    user_id = session.get('user_id')
    # Optional: Log full name if stored, otherwise just ID
    # user_full_name = session.get('user_full_name')
    session.clear()
    if user_id:
        current_app.logger.info(f"User ID: {user_id} logged out successfully.")
    else:
        current_app.logger.info(f"Logout request processed, no active session found.")
    return jsonify({"message": "Logout successful"}), 200


# --- CSRF Token Route ---
# (No changes needed - uses user_id)
@auth_bp.route("/csrf_token", methods=["GET"])
@login_required
def get_csrf_token():
    token = generate_csrf()
    current_app.logger.debug(f"Generated/Retrieved CSRF token for user {session.get('user_id')}")
    return jsonify({"csrf_token": token}), 200


# --- UPDATED Profile Route ---
@auth_bp.route("/profile", methods=["GET"])
@limiter.limit("60 per minute")
@login_required # Ensures session['user_id'] exists
def profile():
    user_id = session.get('user_id')
    # Use db.session.get for optimized primary key lookup
    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        session.clear() # Clear potentially invalid session
        current_app.logger.warning(f"Profile access attempt for non-existent or inactive user ID: {user_id}. Session cleared.")
        # Return 404 as the specific user resource isn't found/valid
        return jsonify({"error": "User data not found or account inactive, session cleared"}), 404

    # Return the relevant user profile data
    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "username": user.username # Include username if it's still used/relevant
        # DO NOT return password_hash or other sensitive info
    }), 200

# --- NEW: Update Profile Info Route ---
@auth_bp.route("/profile/update", methods=["PUT"]) # Using PUT for update
@limiter.limit("10 per minute")
@login_required
def update_profile():
    """Updates the user's basic profile information (names, username)."""
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return jsonify({"error": "User not found or inactive"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # --- Get and Validate Input ---
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    username = data.get('username', '').strip()

    name_errors = {} # Use a separate dict for name errors initially
    if not first_name:
        name_errors['first_name'] = "First name cannot be empty."
    if not last_name:
        name_errors['last_name'] = "Last name cannot be empty."

    new_username = username if username else None

    # --- Check username uniqueness FIRST and return 409 if duplicate ---
    if new_username and new_username != user.username:
        existing_user = User.query.filter(
            User.username == new_username,
            User.id != user_id
        ).first()
        if existing_user:
            # --- CORRECTED: Return 409 directly ---
            return jsonify({"error": "Username is already taken.", "type": "DUPLICATE_USERNAME"}), 409
            # --- END CORRECTION ---

    # --- If username is okay, check for other validation errors (names) ---
    if name_errors:
        return jsonify({"error": "Validation failed", "details": name_errors}), 400

    # --- Update User Object ---
    try:
        user.first_name = first_name
        user.last_name = last_name
        user.username = new_username # Assign None if it was empty

        db.session.commit()
        current_app.logger.info(f"User profile updated successfully for user ID: {user_id}")

        # Return updated user data (excluding sensitive info)
        return jsonify({
            "message": "Profile updated successfully.",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email, # Email wasn't changed here
                "username": user.username
            }
        }), 200

    except IntegrityError as e:
         # Fallback catch for race conditions or other DB constraints
         db.session.rollback()
         current_app.logger.error(f"IntegrityError during profile update for user ID {user_id}: {e}")
         error_detail = str(e.orig).lower() if e.orig else ""
         if 'users_username_key' in error_detail or 'users.username' in error_detail:
              # Return 409 here too
              return jsonify({"error": "Username is already taken (DB constraint).", "type": "DUPLICATE_USERNAME"}), 409
         else:
              return jsonify({"error": "Database error during update.", "type": "DB_ERROR"}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error during profile update for user ID {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred.", "type": "UNKNOWN_ERROR"}), 500
    
# --- NEW: Change Password Route ---
@auth_bp.route("/profile/change-password", methods=["PUT"])
@limiter.limit("5 per 15 minute") # Stricter limit for password changes
@login_required
def change_password():
    """Allows the logged-in user to change their password."""
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return jsonify({"error": "User not found or inactive"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirmation = data.get('confirmation')

    # --- Validation ---
    if not all([current_password, new_password, confirmation]):
        return jsonify({"error": "Current password, new password, and confirmation are required."}), 400

    # 1. Verify Current Password
    if not bcrypt.check_password_hash(user.password_hash, current_password):
        current_app.logger.warning(f"Incorrect current password attempt for user ID: {user_id}")
        # Return 400 or 401 - 400 is common for validation-like failures within an authenticated context
        return jsonify({"error": "Incorrect current password.", "type": "INVALID_CURRENT_PASSWORD"}), 400

    # 2. Verify New Password Confirmation
    if new_password != confirmation:
        return jsonify({"error": "New passwords do not match.", "type": "PASSWORD_MISMATCH"}), 400

    # 3. Verify New Password Strength
    is_valid, errors = validate_password_strength_backend(new_password)
    if not is_valid:
        return jsonify({
            "error": "New password does not meet security requirements.",
            "type": "WEAK_PASSWORD",
            "details": errors
        }), 400

    # 4. (Optional but recommended) Check if new password is same as old
    if bcrypt.check_password_hash(user.password_hash, new_password):
         return jsonify({"error": "New password cannot be the same as the current password.", "type": "PASSWORD_SAME_AS_OLD"}), 400

    # --- Update Password ---
    try:
        new_hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        user.password_hash = new_hashed_password
        db.session.commit()
        current_app.logger.info(f"Password changed successfully for user ID: {user_id}")

        # Optionally: Log out other sessions? More complex, skip for now.

        return jsonify({"message": "Password changed successfully."}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error changing password for user ID {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while changing password.", "type": "DB_ERROR"}), 500
    
# --- NEW: Delete Account Route ---
@auth_bp.route("/profile/delete", methods=["DELETE"])
@limiter.limit("3 per hour") # Very strict limit for account deletion
@login_required
def delete_account():
    """Deactivates (soft deletes) the logged-in user's account after password verification."""
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        # Should be caught by @login_required, but good practice
        return jsonify({"error": "User not found or inactive"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    password = data.get('password') # Expect current password for confirmation

    if not password:
        return jsonify({"error": "Password confirmation is required."}), 400

    # --- Verify Current Password ---
    if not bcrypt.check_password_hash(user.password_hash, password):
        current_app.logger.warning(f"Incorrect password during account deletion attempt for user ID: {user_id}")
        # Use 403 Forbidden or 400 Bad Request for incorrect password during delete confirmation
        return jsonify({"error": "Incorrect password provided.", "type": "INVALID_PASSWORD"}), 403

    # --- Perform Soft Delete ---
    try:
        current_app.logger.info(f"Initiating account soft delete for user ID: {user_id}, Email: {user.email}")
        user.soft_delete() # Calls the method on the User model
        db.session.commit()

        # --- CRITICAL: Clear the user's session ---
        session.clear()
        current_app.logger.info(f"Session cleared for deleted user ID: {user_id}")

        # Return 200 OK or 204 No Content on successful deletion
        return jsonify({"message": "Account deactivated successfully."}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during account deletion for user ID {user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while deactivating the account.", "type": "DB_ERROR"}), 500