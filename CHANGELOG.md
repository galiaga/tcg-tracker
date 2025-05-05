# Changelog

## [2.0.0] - 2025-05-05 

### Added
- **Tournament Structure (Phase 1):**
    - Added `Tournament` model and `tournaments` database table...
    - Added `TournamentParticipant` model and `tournament_participants` database table...
    - Added database migration script (`786fcb4a0387`)...
- Database migration script (`e0e70a397868`)...

### Changed
- **BREAKING CHANGE (Database):** Renamed the `matches` table...
- **BREAKING CHANGE (Model):** Refactored the `Match` model to `LoggedMatch`...
    - Removed the `user_deck_id` foreign key...
    - Added `logger_user_id` column...
    *   Added `deck_id` column...
    *   Added optional `opponent_description`...
- **Internal Services:**
    - Updated `match_service`...
    - Updated `match_history_service`...
- **API:**
    - Updated `matches` routes...
    - The response structure for `POST /api/log_match`...
    - **API Interaction:** Clients interacting with protected, state-changing endpoints (e.g., POST `/api/register_deck`, DELETE `/api/decks/<id>`) **must** now perform the following sequence after authentication:
        1. Fetch the CSRF token via a GET request to `/api/auth/csrf_token`.
        2. Include the fetched token in the `X-CSRFToken` header for subsequent protected POST/PUT/PATCH/DELETE requests.
    - Authentication-related routes (login, register, password reset) within the `/api/auth` blueprint are exempt from this CSRF requirement.
    - Updated the `/api/auth/csrf_token` endpoint to use Flask-WTF's `generate_csrf()` function.
- **Testing:**
    - Updated test fixtures...
    - Updated relevant tests...

### Fixed
- Resolved multiple test failures caused by...
    - Incorrect fixture setup...
    - Persistent execution environment issues...
    - Missing `@login_required` decorators...
    - Incorrect expected status codes...
    - Incorrect login fixture logic...
    - SQLAlchemy failing to determine join conditions...
    - SQLite batch migration errors...
- **Resolved intermittent `400 Bad Request` and `401 Unauthorized` errors** on protected API endpoints (e.g., `/api/register_deck`) caused by incorrect or missing CSRF token validation. Removed previous manual/incomplete CSRF validation logic.

### Security
- **Implemented application-wide CSRF (Cross-Site Request Forgery) protection** using Flask-WTF. This enhances security by preventing malicious actors from forcing logged-in users to perform unwanted actions via their browser session. Protection is now automatically applied by default to state-changing requests (POST, PUT, PATCH, DELETE) on protected blueprints.


## [1.3.0] - 2024-04-30

### Added
- **User Profile Functionality:**
    - New Profile page (`/profile`) displaying user's First Name, Last Name, Email, and Username (if set).
    - Ability for users to update their First Name, Last Name, and Username (can be set to empty/null) via the Profile page.
    - Ability for users to change their password via the Profile page (requires current password confirmation and meets complexity rules).
    - Ability for users to deactivate (soft delete) their account via the Profile page (requires password confirmation and shows warnings).
    - Logout button added to the Profile page (primary logout location).
- **API Endpoints:**
    - `PUT /api/auth/profile/update` for updating basic user info.
    *   `PUT /api/auth/profile/change-password` for changing the user's password.
    *   `DELETE /api/auth/profile/delete` for deactivating the user's account.
- Profile icon added to top-right on mobile view for accessing profile page. *(Moved from Changed section as it's part of the new feature)*
- Unit tests for new profile update, change password, and delete account API endpoints.

### Changed
- **BREAKING CHANGE (Authentication):** User login now uses Email Address instead of Username. The `username` field is now optional for users.
- **BREAKING CHANGE (API):**
    - `POST /api/auth/register` now requires `first_name` and `last_name` instead of `username`. `username` is now an optional field in the request body. Response returns user object with new fields.
    - `POST /api/auth/login` now requires `email` instead of `username`. Response returns user object with new fields.
    - `GET /api/auth/profile` response now includes `first_name`, `last_name`, `email`, and optional `username`.
- **Database:**
    - `users` table: Added required `first_name` (string) and `last_name` (string) columns.
    - `users` table: Made `email` column non-nullable (`NOT NULL`).
    - `users` table: Made `username` column nullable (`NULLABLE`), but kept unique constraint.
- **UI:**
    - Registration form now collects First Name and Last Name instead of Username.
    - Login form now uses an Email Address input instead of Username.
    - Desktop navigation bar now displays the user's First Name instead of static "Profile" text.
    - Relocated mobile profile icon from a floating position to within the main page header area, next to the page title. *(Consolidated UI change)*
    - Revamped Profile page UI for vertical compactness using definition lists and reduced padding. *(Kept from original)*
    - Implemented standard "Edit/Save/Cancel" workflow for Profile Information section with initially read-only fields. *(Kept from original)*
    - Improved visual styling for read-only input fields on the Profile page. *(Kept from original)*
- **Testing:** Updated authentication, deck, match, and tag test fixtures and relevant tests to accommodate the new User model structure and login method.

### Fixed
- Resolved CSS specificity issue where the "Edit Profile" button remained visible during edit mode. *(Kept from original)*
- Restored vertical and horizontal centering for logged-out pages (e.g., Login) within the main layout. *(Kept from original)*
- Resolved issues in test suite related to `itsdangerous` token expiry checks by using mocking.
- Corrected database migration steps for adding non-nullable columns to existing tables, using a two-step process with manual data population.
- Corrected backend API validation logic to return `409 Conflict` instead of `400 Bad Request` for duplicate username errors during profile updates.
- Corrected test assertions for invalid JSON responses and 401 authentication errors.
- Fixed `DetachedInstanceError` in profile update tests by adjusting object handling across sessions.
- Improved user-facing message for rate limit (429) errors.

### Removed
- Logout button/link from the main mobile bottom navigation bar.


## [1.2.0] - 2025-04-28

### Added
- User profiles now require First Name and Last Name fields.
- Profile icon added to top-right on mobile view for accessing profile page (page itself TBD).

### Changed
- **BREAKING CHANGE:** User login now uses Email Address instead of Username.
- Registration form now collects First Name and Last Name instead of Username.
- Desktop navigation bar now displays the user's First Name instead of "Profile".
- User model: `email` field is now required (`NOT NULL`).
- User model: `username` field is now optional (`NULLABLE`), but remains unique if provided.
- Updated various test fixtures to accommodate the new User model structure.

### Fixed
- Resolved issues in test suite related to `itsdangerous` token expiry checks by using mocking.
- Corrected database migration steps for adding non-nullable columns to existing tables.