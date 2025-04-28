# backend/utils/validation.py

import re

def validate_password_strength_backend(password):
    """
    Validates password strength based on common criteria (backend counterpart).

    Args:
        password (str): The password string to validate.

    Returns:
        tuple: A tuple containing:
            - bool: True if the password meets all criteria, False otherwise.
            - list: A list of strings describing the validation errors.
                    Empty if the password is valid.
    """
    errors = []
    min_length = 8
    # Define the set of required special characters using a raw string
    # Ensure this matches or is a superset of your frontend validation definition
    special_chars_pattern = r'[!@#$%^&*]' # Example set

    # --- Basic Checks ---
    if not isinstance(password, str):
        # Handle non-string input gracefully, though route should prevent this
        return False, ["Password must be provided."]

    # --- Validation Criteria ---

    # 1. Minimum Length
    if len(password) < min_length:
        errors.append(f"Must be at least {min_length} characters long.")

    # 2. Uppercase Letter
    if not re.search(r'[A-Z]', password):
        errors.append("Must contain at least one uppercase letter (A-Z).")

    # 3. Lowercase Letter
    if not re.search(r'[a-z]', password):
        errors.append("Must contain at least one lowercase letter (a-z).")

    # 4. Digit
    if not re.search(r'\d', password): # \d matches any Unicode digit
        errors.append("Must contain at least one number (0-9).")

    # 5. Special Character
    if not re.search(special_chars_pattern, password):
        errors.append(f"Must contain at least one special character (e.g., {special_chars_pattern}).")

    # --- Determine Overall Validity ---
    is_valid = not errors # Password is valid if the errors list is empty

    return is_valid, errors

# --- Optional: Add other validation functions here as needed ---
# For example, username validation, etc.