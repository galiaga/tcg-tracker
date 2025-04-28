// backend/static/js/utils/validation-utils.js

// --- Password Complexity Validation ---

/**
 * Validates password complexity based on predefined rules.
 * @param {string} password - The password string to validate.
 * @returns {{isValid: boolean, errors: string[]}} - An object indicating validity and an array of error messages.
 */
export function validatePasswordComplexity(password) {
    const minLength = 8; // Minimum password length
    const errors = [];

    // Rule 1: Minimum Length
    if (password.length < minLength) {
        errors.push(`Password must be at least ${minLength} characters long.`);
    }

    // Rule 2: Uppercase Letter
    if (!/[A-Z]/.test(password)) {
        errors.push("Password must include at least one uppercase letter.");
    }

    // Rule 3: Lowercase Letter
    if (!/[a-z]/.test(password)) {
        errors.push("Password must include at least one lowercase letter.");
    }

    // Rule 4: Number
    if (!/\d/.test(password)) {
        errors.push("Password must include at least one number.");
    }

    // Rule 5: Special Character
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/.test(password)) {
        errors.push("Password must include at least one special character (e.g., !@#$%).");
    }

    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

// --- Add other validation functions below as needed ---
// export function validateEmailFormat(email) { ... }
// export function validateUsername(username) { ... }