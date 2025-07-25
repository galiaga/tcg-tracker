# Changelog

## [4.5.1] - 2025-07-23

### Removed
- **Decklist Intelligence & Analysis Feature:** The "Fetch Info" functionality on the Deck Details page has been removed. This was due to persistent, unresolvable `403 Forbidden` errors from the external Moxfield API, caused by Cloudflare security rules blocking the application's hosting provider (Fly.io). All related UI elements (Fetch button, analysis chart, summary stats) and the backend API endpoint (`POST /api/decks/<deck_id>/fetch_metadata`) have been decommissioned to provide a cleaner user experience.

### Fixed
- **Tag Management on Deck Details Page:** Resolved a critical `404 NOT FOUND` error that occurred when attempting to remove a tag from a deck on its details page. The issue was caused by a local routing misconfiguration where tag association routes were incorrectly placed. The fix involved reverting the local backend route structure to match the working production environment, ensuring the `DELETE /api/decks/<deck_id>/tags/<tag_id>` endpoint is correctly registered and accessible.

## [4.5.0] - 2025-07-22

### Added
- **Match History - View Notes Functionality:**
    - Implemented a new modal to view "Pod Notes" directly from the "My Matches" page.
    - The "Notes" icon on a match card is now an interactive button.
    - The icon now provides a visual cue: it appears solid when notes exist for a match and hollow/dimmed when they do not.

### Changed
- **UI/UX - Match History Card Redesign:**
    - Fundamentally redesigned the layout of match cards on the "My Matches" page for a more modern, scannable, and visually balanced experience.
    - The top of the card is now a two-column layout:
        - The left column features a large, prominent image of the user's commander.
        - The right column contains all textual information, creating a clear separation between visuals and data.
    - The user's **Deck Name** is now the primary title in the right column, improving readability.
    - The **Match Date** is now a subtitle below the deck name, giving it its own line and preventing awkward text wrapping on smaller screens.
    - The **Win/Loss/Draw pill** and the **"three dots" options menu** are now cleanly aligned to the top-right of the content column.

### Fixed
- **Quick Log Functionality on Deck Details Page:**
    - Resolved a critical bug where the "Quick Log" (Win/Loss/Draw) buttons on the Deck Details page failed to pre-select the deck and result in the Log Match modal.
    - The `deck-details.js` script now correctly passes pre-selection data to the refactored `log-match-modal.js` module, restoring this key workflow.
- **Log New Match Modal - Opponent Interaction:**
    - Fixed an issue where the **"+ Add Opponent"** button was unresponsive. The logic has been refactored to be correctly driven by the button click, allowing users to add opponent rows one by one after selecting their turn order.
- **UI & Styling Regressions:**
    - Restored the correct visual styling (borders, colors, etc.) for the "Match Result," "Turn Order," and "Mulligan" buttons within the Log Match modal, which were lost during an HTML refactor.
    - The "three dots" options menu, which had disappeared from match cards on the "My Matches" page, has been restored.
- **JavaScript Stability:**
    - Fixed a `ReferenceError: Can't find variable: zone` in `match-list-manager.js` that prevented match cards from rendering.
    - Fixed a `ReferenceError: Can't find variable: preselectionData` in `log-match-modal.js` that caused an error when opening the modal from the Deck Details page.
    - Resolved an error where the "Add Tag" and "Delete Match" functions on match cards were broken due to missing `data-match-id` attributes in the newly generated HTML.

## [4.4.1] - 2025-07-17

### Changed
- **UI/UX - Match History Card Redesign:**
    - Fundamentally redesigned the layout of match cards on the "My Matches" page for a more modern, compact, and visually intuitive experience.
    - The top of the card is now a two-column layout:
        - The left column is dedicated to a large, prominent visual of the **user's commander** or commander pairing.
        - The right column now neatly contains all other top-level match details: the date, the Win/Loss pill, and the options menu.
    - The user's commander pairing now uses a clean, side-by-side split-image style for visual consistency with opponent pairings.
    - The user's commander/deck name is now displayed as a bold, slightly larger overlay on their commander's art, creating a clear "hero" element.
    - Turn order and mulligan information is now displayed compactly in the right-hand column, below the match date.
- **UI/UX - Opponent Display:**
    - The display for opponent commanders has been refined to be more compact and visually scannable.
    - Opponent commander names are now displayed as an overlay on their art, with a subtle gradient to ensure readability.
    - Single opponent commanders now show their full name (e.g., "Aminatou, the Fateshifter"), while paired commanders are abbreviated for compactness (e.g., "Tymna / Rograkh").

### Fixed
- **Backend Stability:**
    - Resolved a critical 500 Internal Server Error caused by an `AttributeError` when the match history service tried to access a non-existent `associated_commander` relationship on the `CommanderDeck` model. The fix involved defining the missing SQLAlchemy relationship in `commander_deck.py` and correcting the eager-loading query in `match_history_service.py`.
    - Fixed a subsequent `TypeError` by correctly handling the one-to-one relationship between `Deck` and `CommanderDeck` (accessing `deck.commander_decks` directly instead of as a list).
    - Corrected a `ValueError` by ensuring the data tuple returned from the service and unpacked by the API route had the same number of items.
- **SQLAlchemy Mapper Initialization:** Fixed a `sqlalchemy.exc.InvalidRequestError` that occurred at application startup. The error was caused by an ambiguous relationship between the `Commander` and `CommanderDeck` models. The fix involved explicitly defining the `foreign_keys` on the `Commander.commander_decks` relationship to resolve the ambiguity.

## [4.4.0] - 2025-07-15

### Added
- **Deck Details - Decklist Intelligence & Analysis:**
    - Implemented a powerful new **"Decklist Intelligence"** feature on the "Deck Details" page.
    - When a user provides a Moxfield decklist URL, a new **"Fetch Info"** button appears.
    - On click, the application now performs a multi-step analysis:
        1.  Calls the internal Moxfield API to retrieve the full, accurate card list for the deck.
        2.  Sends the list of card identifiers to the Scryfall API to get detailed, up-to-date card data (CMC, type line, etc.) in a single, efficient batch request.
        3.  Analyzes the complete data on the backend to calculate key deck-building metrics.
    - The results are displayed in a new, compact, mobile-first **stacked bar chart**, which visualizes:
        - **Mana Curve:** The distribution of cards at each mana cost from 0 to 10+.
        - **Card Types:** The composition of the mana curve, with colored segments in each bar representing Creatures, Instants, Sorceries, Artifacts, etc.
    - A new summary line prominently displays the deck's **Average CMC**, along with non-land and land counts.

### Changed
- **UI/UX - Deck Details Page:**
    - The "Decklist Link" card has been redesigned to be an interactive analysis module.
    - Replaced the previous two separate charts (mana curve and card type doughnut) with the single, more information-dense stacked bar chart, significantly improving layout compactness on mobile devices.
- **Backend & API:**
    - Created a new API endpoint `POST /api/decks/<deck_id>/fetch_metadata` to orchestrate the decklist analysis.
    - Implemented a robust, multi-stage data fetching service in `deck_scraper.py` that now uses the official Scryfall API for card data, removing the dependency on an incomplete local card database for analysis. This ensures accuracy for all cards, not just commanders.

### Fixed
- **Decklist Analysis Accuracy:** Resolved a critical logical flaw where deck analysis was performed against the local `commanders` table, leading to incorrect charts that only accounted for creature cards. The new Scryfall-based approach guarantees accurate analysis for all 100 cards in a decklist.
- **Web Scraper Brittleness:** Replaced all previous HTML-based web scraping and `__NEXT_DATA__` parsing methods with a direct call to Moxfield's internal API. This provides a much more stable and reliable way to retrieve the initial card list, preventing errors caused by frequent changes to Moxfield's website layout.
- **Database Model:** Added a `cmc` column to the `Commander` model and updated the `update_commanders.py` script to populate it, resolving an `AttributeError` and ensuring the local commander database is more complete.

## [4.3.1] - 2025-07-10

### Added
- **Match History - Opponent Display:** Individual match cards on the "My Matches" page now display a list of the commanders and pairings faced in that game. This leverages the new database schema to correctly show partnered commanders as a single entity (e.g., "Tymna the Weaver / Kraum, Ludevic's Opus").

### Changed
- **UI/UX - Match Card Layout:** The match cards on the "My Matches" page have been redesigned to be more compact and information-dense.
    - The "Win/Loss/Draw" result pill has been moved into the card's header, on the same line as the deck name.
    - The new "Opponents" list and the existing "Tags" list are now grouped together in a unified footer section at the bottom of the card.

### Fixed
- **Application Stability:** Resolved a critical application startup failure (presenting as a 404 error on all pages) caused by an SQLAlchemy ORM compiler issue when fetching match history with opponent data. The fix involved replacing the complex ORM subqueries with a single, robust raw SQL subquery (`text()`), ensuring stability and performance.
- **Tag Functionality on Match Cards:** Restored the "Tags" section (including the "+ Tag" button) to match cards on the "My Matches" page, which was inadvertently removed during a layout refactor.
- **Tag Filter UI:** Corrected a CSS issue in the "Filter by Tags" dropdown where tag names were unreadable in dark mode. Added appropriate `dark:` mode text color classes to the labels.
- **Tag Filter Functionality:** Fixed a `ReferenceError` in the tag filtering logic that prevented it from working correctly. The `getSelectedMatchTagIds` function was updated to filter checkboxes *before* mapping them to their values.
- **JavaScript Module Loading:** Resolved a `SyntaxError: Unexpected keyword 'export'` by ensuring the shared `utils.js` script is loaded with `type="module"` in the application's HTML templates.

## [4.3.0] - 2025-07-26

### Added
- **Deck Details - Advanced Matchup Analysis:**
    - The "Deck Details" page now features a powerful new **"Matchup Analysis"** indicator card.
    - This card displays the user's toughest opponents (nemesis matchups) and most favorable matchups for the specific deck being viewed.
    - The analysis intelligently groups opponent commanders by their full command zone, correctly treating partner/associated commanders (e.g., "Rograkh, Son of Rohgahh / Thrasios, Triton Hero") as a single entity.
    - Matchups are partitioned based on their win rate relative to the deck's overall average win rate.
    - A minimum of 3 encounters with an opponent command zone is required for it to appear in the analysis, ensuring statistical relevance.

### Changed
- **BREAKING CHANGE (Database & API):**
    - The `LoggedMatch` data model has been fundamentally refactored to support complex opponent command zones.
    - The old, rigid `commander_at_seat_X_id` columns have been **removed** from the `logged_matches` table.
    - A new `OpponentCommanderInMatch` model and `opponent_commanders_in_match` table have been introduced. This new "linking" table stores multiple commanders per opponent seat, each with a designated role (e.g., "primary", "partner").
    - The `POST /api/log_match` endpoint has been updated to accept a new, flexible `opponent_commanders_by_seat` object, allowing clients to submit multi-commander opponents.
    - The `GET /api/decks/<deck_id>` endpoint now accepts an `include_matchup_stats=true` query parameter to return the new matchup analysis data.
    - The `GET /api/matches_history` endpoint now returns the full opponent commander data for each match in a structured `opponents_by_seat` object.

### Fixed
- **Matchup Analytics Accuracy:** Resolved a long-standing issue where matchup analytics could not correctly aggregate or display data for partnered commanders. The new data model and backend query now provide a precise and valuable strategic overview.
- **Database Query Performance:** The new analytics query is optimized to perform the complex commander grouping and aggregation efficiently on the backend.

## [4.2.0] - 2025-07-25

### Added
- **Player Performance Dashboard:**
    - Introduced a new top-level **"Player Performance"** page, designed to give users a strategic overview of their overall gameplay, independent of any single deck.
    - Added "Performance" to the main site navigation on both desktop (header) and mobile (footer).
    - The new dashboard features primary indicators:
        - **Headline Stats Card:** Displays key KPIs at a glance, including Overall Win Rate, Total Matches Logged, a user's "Winningest Deck" (min. 10 matches), and their "Most Played Deck".
        - **Overall Performance by Turn Order:** A powerful visual breakdown of a player's win rate in the 1st, 2nd, 3rd, and 4th seats, aggregated across all of their logged matches.
    - Includes a dedicated "No Data" state that encourages new users to log their first match.
- **Backend & API:**
    - Created a new API endpoint `GET /api/performance-summary` to perform all necessary aggregations and calculations for the dashboard in a single, efficient call.
    - Added a new route `GET /player-performance` to render the page template.
    - Refactored blueprint registration to centralize all page-rendering routes in `frontend.py` and API routes in their respective files for improved code organization.

### Changed
- **Personal Metagame Indicator:** The "Your Personal Metagame" card on the Player Performance page has been significantly enhanced to provide a more accurate and valuable representation of the cEDH meta.
    - The indicator now intelligently groups opponent commanders by their full command zone pairing (e.g., "Tymna the Weaver / Kraum, Ludevic's Opus") instead of counting them individually.
    - The backend query now generates a unique "signature" for each opponent's command zone, allowing for correct aggregation of both partnered and single-commander decks.
- **Deck Details Page:** The page now includes a "Mulligan Performance" indicator card, showing win rates grouped by mulligan decisions (Keep First 7, Free mulligan, mulligan to 6, etc.).
- **API Endpoints:**
    - The `GET /api/decks/<deck_id>` endpoint now accepts an `include_mulligan_stats=true` query parameter.
    - The `GET /api/performance-summary` endpoint has been updated to return the new commander pairing data for the metagame breakdown.

## [4.1.1] - 2025-07-08

### Fixed
- **Log New Match Modal:** Resolved an issue where the **'Free (to 7)'** mulligan button did not provide visual feedback (i.e., turn purple) when selected. The button's styling now correctly updates to indicate its active state, matching the behavior of all other options in the group.

## [4.1.0] - 2025-06-15 

### Added
- **Enhanced Match Logging (Commander Specifics):**
    - **Opponent Commanders:**
        - Implemented structured logging for opponent commanders based on their seat at the table.
        - "Log New Match" modal now dynamically displays input fields for each opponent seat after the user selects their own turn order.
        - Each opponent commander input uses autocomplete, searching against the application's commander database.
        - Added support for logging an **associated commander** (e.g., Partner, Background, Friends Forever, Doctor's Companion) for each opponent.
            - An "+ Add Partner/Associated" button appears if the selected primary opponent commander has a pairing ability.
            - The search for the associated commander is filtered by the required pairing type (e.g., only shows "Partner" commanders if the primary has "Partner").
        - Backend `LoggedMatch` model updated with a new `OpponentCommanderInMatch` association table to store multiple commanders per opponent seat with their roles (primary, partner, etc.).
        - API endpoint `POST /api/log_match` now accepts a structured `opponent_commanders_by_seat` payload.
    - **Player Mulligans:**
        - Added functionality to log the number of mulligans taken by the player for deeper strategic analysis.
        - "Log New Match" modal now features radio-button style selectors for mulligan count, including a distinct **'Free (to 7)'** option (value: -1) to differentiate it from keeping the initial 7-card hand.
        - Updated `LoggedMatch` model to include `player_mulligans` and allow for the new free mulligan value.
        - API endpoint `POST /api/log_match` now accepts `player_mulligans`, including the `-1` value for a free mulligan.
    - **Pod Notes:** The "Opponent/Pod Description" field in the "Log New Match" modal has been repurposed and renamed to "Pod Notes" for more general match commentary.
- **Deck Details Page Enhancements:**
    - **Performance by Turn Order:** Added a new card to display the deck's win rate and match count broken down by the player's turn order (1st, 2nd, 3rd, 4th).
    - **Recent Matches Display:** The "Recent Matches" card on the Deck Details page now loads and displays a list of the last 5 matches played with the deck, showing result, date, and player position.
    - API endpoint `GET /api/decks/<deck_id>` now optionally returns `turn_order_stats` and `recent_matches` via query parameters.
- **API - Commander Search Enhancement:**
    - The `GET /api/search_commanders` endpoint now accepts an optional `type` query parameter to filter commander search results by specific pairing abilities (e.g., `?type=partner` will only return commanders with the "Partner" ability).

### Changed
- **UI/UX - Deck Details Page:**
    - Redesigned the layout for a more compact and mobile-first experience.
    - Combined deck identity (Commander, Associated) and core performance statistics (Win Rate, Matches, Wins) into a single, prominent card.
    - Removed the redundant display of "Deck Name" and "Format: Commander / EDH" from the main content card, as this information is already present in the page header.
    - Reduced vertical spacing between the page header and the first content card.
    - Adjusted styling of card headers and content for better visual hierarchy and compactness.
- **UI/UX - Log New Match Modal:**
    - "Your Turn Order" selection now dynamically determines which "Seat X Commander" input fields are displayed.
    - Opponent commander inputs now use a pill-based display for selected commanders, similar to tag inputs.
- **Backend - Match Logging:**
    - `LoggedMatch.player_position` is now a non-nullable field and required during match logging.
    - Refactored opponent commander storage from individual columns in `LoggedMatch` to the new `OpponentCommanderInMatch` association table.
- **JavaScript - Modals & Script Loading:**
    - Ensured global modals (`_quick_add_tag_modal.html`, `_log_match_modal.html`) and their dependent JavaScript files (`tag-utils.js`, `tagInput.js`, `log-match-modal.js`, `log-match.js`, `deck-api.js`) are correctly included and initialized via `layout.html` for consistent availability across pages.

### Fixed
- **Deck Details Page - Tag Modal:** Resolved an error where the "Quick Add Tag Modal" would not open due to its HTML elements not being found in the DOM. This was fixed by ensuring the modal's HTML is globally available via `layout.html`.
- **My Decks Page - Deck Loading:** Fixed a `SyntaxError` ("Importing binding name 'handleRemoveTagClick' is not found") in `deckCardComponent.js` (and potentially other files like `deck-list-manager.js`, `user-tags.js`) by correcting the import statement to use the actual exported function name `handleRemoveDeckTagClick` from `tag-utils.js`.
- **Unit Tests:**
    - Updated `test_deck_register.py` to no longer send `deck_type_id` (as backend defaults to Commander) and to correctly use test fixtures.
    - Updated `test_get_user_decks.py` to expect `format_name: "Commander"` and potentially adjust for AND/OR logic in tag filtering.
    - Updated `test_get_matches_history.py` (match tag API tests) to provide the now-required `player_position` when creating `LoggedMatch` instances in fixtures and to use correct dictionary keys for tag data.

## [4.0.1] - 2025-06-04 

### Fixed
- **Deck Details Page:**
    - Resolved an issue where the Deck Details page would get stuck in a "Loading deck details..." state due to a `ReferenceError` for `totalMatches` during rendering.
    - Ensured that after logging a new match via the "Quick Log" buttons on the Deck Details page, the main deck statistics (Win Rate, Matches, Wins) and the "Recent Matches" list are correctly refreshed.
- **Tag Management Modals & Inputs:**
    - **Log Match Modal:**
        - Corrected JavaScript errors that prevented adding tags when logging a new match, by aligning the tag input initialization with the older, simpler `TagInputManager`.
        - Ensured the deck select dropdown within the modal is populated before attempting to preselect a deck when logging from the Deck Details page, resolving "Option for preselected deck not found" warnings.
        - Added a visual display area for selected tag pills within the Log Match Modal.
        - Removed the default selection for "Player Position," requiring the user to make an explicit choice.
        - Improved the validation message to be more specific if "Player Position" is not selected.
    - **New Deck Modal:**
        - Aligned the tag input field with the older `TagInputManager`, allowing tags to be added to new decks. Selected tags are now displayed as pills below the input field.
    - **"My Tags" Page:**
        - Fixed the "X" button functionality for removing tags from the "Selected Tags" display.
        - Ensured the "Clear All" button correctly resets the selected tags UI and the search results placeholder.
- **JavaScript Stability & Console Errors:**
    - Resolved `InvalidCharacterError` on "My Decks" and "My Matches" pages when applying dynamic border styles to cards by correctly using `classList.add` with the spread operator.
    - Fixed `SyntaxError: Importing binding name 'fetchUserTags' is not found` by ensuring all JavaScript modules correctly import `fetchAllUserTags` from `tag-utils.js` (which uses the older `TagInputManager`'s internal cache).
    - Addressed console warnings (e.g., "Required match list elements not found") on pages like "Deck Details" and "My Tags" by adding guard clauses to page-specific JavaScript modules (`match-list-manager.js`, `sort-decks.js`), preventing them from executing their main initialization logic if their target HTML elements are not present.
    - Resolved a circular dependency issue between `log-match.js` and `log-match-modal.js` related to the `populateDeckSelect` function by moving the function to be an internal part of `log-match-modal.js`.

### Changed
- **UI Consistency:**
    - Minor styling adjustments to tag pills and "+ Tag" buttons on "My Decks" and "My Matches" cards for better visual consistency with the "My Tags" page and modals.
    - Ensured the "Selected Tags:" label and display area on the "My Tags" page maintain consistent left alignment regardless of whether tags are selected.

## [4.0.0] - 2025-06-03

### Added
- **Player Position Tracking (Commander):**
    - Added functionality to log the player's turn order (1st, 2nd, 3rd, 4th) for each match, assuming 4-player Commander pods.
    - Updated `LoggedMatch` model and database schema (`88ac1a3b8000_...`) to include `player_position`.
    - Enhanced "Log Match" modal with button-style selectors for choosing player position.
    - Match history displays now include player position information.
- **API Support for Player Position:**
    - `POST /api/log_match` now accepts and stores `player_position`.
    - `/api/matches_history` and `/api/decks/<deck_id>` (for recent matches) now return `player_position`.
- **Enhanced Tag Management on Item Cards:**
    - **"My Decks" & "My Matches" Pages:** Users can now directly add or remove tags from individual deck and match cards using a consistent "+ Tag" button and "x" on tag pills.
    - **Quick Add Tag Modal:** A new modal allows users to quickly select existing tags or create new ones for association with decks or matches directly from the card view.

### Changed
- **BREAKING CHANGE - Application Focus: Commander (EDH) Exclusivity:**
    - The application is now primarily focused on supporting the Commander (EDH) TCG format.
    - **Deck Creation:** New decks are implicitly Commander format. The "Deck Type" selection has been removed from the "New Deck" modal. The backend (`POST /api/register_deck`) now defaults to Commander type.
    - **Deck Listing ("My Decks"):** Removed the "Format" filter from the "My Decks" page and associated JavaScript.
    - **Deck Details:** The "Format" display on the deck details page now consistently shows "Commander".
- **UI/UX - Modals & Forms:**
    - **Log Match Modal:**
        - Player position input changed from a dropdown to more intuitive radio-button-styled buttons.
        - Tags input section now uses a simpler, more direct input field with suggestions, consistent with the "Quick Add Tag" modal.
    - **New Deck Modal:**
        - "Deck Type" selection removed.
        - Commander, Partner, and other associated commander (Friends Forever, Doctor/Companion, Background) input fields are now correctly displayed and functional based on main commander abilities.
        - Tags input section updated to display selected tags as pills below the input field, using a simpler suggestion-based input.
    - **Deck Details Page:**
        - "Quick Log" buttons (Win/Loss/Draw) now open the main "Log Match Modal", pre-filling the deck and result, ensuring `player_position` can be captured.
        - Recent match history is now integrated directly within the main deck details card.
- **UI/UX - Card Displays:**
    - **"My Decks" Page:**
        - Deck cards now feature a colored left accent border (green for high win rate, yellow for medium, red for low, neutral for new) for quick visual assessment, replacing full background color changes.
        - Consistent dark mode background (`dark:bg-slate-800`) applied to all deck cards.
        - "Commander" format pill retained for clarity.
    - **"My Matches" Page:**
        - Match cards now feature a colored left accent border (green for Win, red for Loss, neutral for Draw).
        - Consistent dark mode background (`dark:bg-slate-800`) applied to all match cards.
        - Removed the redundant "Commander / EDH" format pill from match cards.
        - Result badges (Win/Loss/Draw) styling refined for better visual clarity.
    - **"My Tags" Page:**
        - Improved alignment of the "Selected Tags:" label and display area, ensuring consistent left alignment.
        - Enhanced visual feedback for selected tags in "Quick Select" and "Find Tags" results.
        - Placeholder text for tag search results is now correctly restored when the search is cleared or "Clear All" is used.
- **JavaScript Refactoring:**
    - `deck-form.js`: Updated `FIELD_CONFIG` and logic to correctly handle dataset attributes for commander types and manage visibility of associated commander fields.
    - `registerDeck.js`: Aligned with Commander-only focus and corrected reading of dataset attributes for commander/partner IDs. Now correctly retrieves selected tag IDs from the new deck modal's tag input.
    - `tagInput.js`: Reverted to a simpler, older version that focuses on suggestion-based input without inline pills, aligning with the "Quick Add Tag" modal and "New Deck" modal's tag input behavior. Manages its own global tag cache.
    - `tag-utils.js`: Adapted to work with the older `tagInput.js`, managing the "Quick Add Tag Modal" initialization and tag association logic. No longer exports `fetchUserTags` or `invalidateTagCache` directly.
    - `log-match-modal.js`: Updated to manage the new player position radio buttons and use the simpler tag input style.
    - `deck-list-manager.js` & `match-list-manager.js`:
        - Removed dependency on the "Format" filter for decks.
        - Updated to correctly apply new card styling (left borders, consistent backgrounds).
        - Now correctly pass refresh callbacks to card rendering components to ensure list updates after tag modifications via the "Quick Add Tag Modal".
        - Added guard clauses to prevent initialization errors when loaded on pages where their primary target elements are missing (e.g., `my-tags.html`).
    - `deckCardComponent.js`: Updated to implement new deck card styling (left accent border, consistent dark mode background) and correctly handle `classList.add` for multiple classes.
    - `sort-decks.js`: Adapted to pass refresh callbacks through to `renderDeckCard`. Added guard clause for missing elements.
    - `new-deck-modal.js`: Updated to correctly initialize the older `tagInput.js` for its tag field, manage selected tags as pills displayed below the input, and ensure proper cleanup.
    - `user-tags.js`:
        - Correctly initializes event listeners for removing selected tags and clearing all selections.
        - Ensures search result placeholder text is properly managed.
        - Manages display and interaction for "Quick Select" and "Find Tags" sections.
        - Handles fetching and displaying associated decks/matches, including tag interactions on those displayed cards.

### Fixed
- **Tag Management:**
    - Resolved issues with adding/removing tags from deck and match cards via the "Quick Add Tag Modal".
    - Fixed errors preventing the "Quick Add Tag Modal" from initializing correctly on "My Matches" and "My Decks" pages due to missing HTML or incorrect JavaScript element targeting.
    - Corrected "X" button functionality for removing tags in the "Selected Tags" display on the "My Tags" page.
    - Ensured "Clear All" on "My Tags" page correctly resets UI state.
- **Deck Creation:** Resolved issues preventing Commander and associated Partner/Companion/Background from being correctly selected and saved.
- **"My Decks" & "My Matches" Pages:**
    - Fixed `InvalidCharacterError` when applying dynamic border styles to cards by correctly using `classList.add` with the spread operator for multiple classes.
    - Fixed JavaScript errors related to the removal of the "Format" filter and missing modal elements.
- **Modal Functionality:** Addressed issues with modal open/close mechanisms and form element initialization across various modals.
- **Database Migrations:** Ensured migration `88ac1a3b8000_...` correctly adds `player_position`, removes `match_format`, and applies necessary check constraints.
- **Console Warnings:** Reduced console warnings by adding guard clauses to page-specific JavaScript modules to prevent them from running on pages where their target HTML elements are not present.

## [3.0.0] - 2025-05-27

### Changed
- **UI/UX - "My Decks" Page:**
    - Ensured tag filter dropdown options (checkboxes and labels) are correctly styled and visible in dark mode.
    - Updated the "Sort by" and "Format" select dropdowns to visually match the style of the "Tags" filter button for a consistent appearance.
- **API Rate Limiting:** Investigated 429 "Too Many Requests" errors on the Deck Details page, identifying rapid "Quick Log Match" clicks as a primary cause due to multiple subsequent API calls. Current rate limits on relevant endpoints (e.g., `/api/matches_history`) were reviewed. (Further optimization of frontend request patterns for "Quick Log Match" is a potential future improvement).

### Removed
- **Tournament Management Feature:**
    - Removed all tournament-related functionality from the application, as it is no longer required. This includes:
        - Frontend: "My Tournaments" and "Explore Tournaments" navigation links and pages (`my-tournaments.html`, `explore-tournaments.html`, `view-tournament.html`, `create-tournament.html`, `tournament_settings.html`).
        - Backend: The `tournaments_bp` Flask blueprint, all associated routes (e.g., `/tournaments/...`, `/api/tournaments/...`), and service logic.
        - Database: The `Tournament` and `TournamentParticipant` SQLAlchemy models and their corresponding database tables (`tournaments`, `tournament_participants`) via a database migration (`9b20491f0678_remove_tournament_tables.py`).
        - Tests: All unit and integration tests related to tournament functionality.

### Fixed
- **Database Migrations:** Corrected the order of operations in the `9b20491f0678_remove_tournament_tables.py` migration script for dropping and re-creating tables with foreign key dependencies to ensure `upgrade` and `downgrade` paths execute correctly.


## [2.3.0] - YYYY-MM-DD 

### Added
- **Public Tournament Discovery:**
    - Implemented a new public "Explore Tournaments" page (`GET /tournaments/explore`) listing 'Planned' and 'Active' tournaments, accessible to all users (logged-in or not).
    - Made the individual tournament detail page (`GET /tournaments/<tournament_id>`) publicly accessible for 'Planned', 'Active', 'Completed', and 'Cancelled' tournaments.
    - Added navigation links to "Explore Tournaments" in the main desktop navigation (for logged-in users), mobile navigation (for logged-in users), and the site footer (for all users).
- **Tournament Detail Page Enhancements (Public View):**
    - Public tournament detail pages now display a list of registered (active, non-dropped) participants for 'Planned', 'Active', and 'Completed' tournaments.
    - Organizer-specific actions (e.g., "Edit Tournament", "Manage Participants") on the tournament detail page are now correctly hidden from non-organizers and unauthenticated users.

### Changed
- **UI/UX - Dark Mode & Consistency:**
    - Implemented comprehensive dark mode styling across most application pages, including:
        - Login, Register, Forgot Password, Reset Password pages.
        - My Decks, My Matches, My Tags, My Profile pages.
        - Tournament List (My Tournaments & Explore), Tournament Detail, Create Tournament, and Tournament Settings pages.
    - Standardized page headers (logo, title, mobile profile icon) for a consistent look and feel across all major sections.
    - Improved styling of form elements (inputs, selects, buttons, labels, placeholders, error messages) for better readability and consistency in both light and dark modes.
    - Enhanced modal styling (New Deck, Log Match, Delete Account) for better overlay coverage, dark mode appearance, and content scrollability.
    - Refined button styles (primary, secondary, tertiary/link) for better visual hierarchy and dark mode compatibility.
    - Improved layout and spacing on various pages for a cleaner mobile and desktop experience.
- **Client-Side Navigation:**
    - Refined JavaScript logic in `menu.js` for determining active navigation links (desktop and mobile) to correctly handle nested paths (e.g., `/tournaments` vs. `/tournaments/explore`), ensuring only the most specific link is highlighted.
- **CSRF Token Handling:**
    - Modified `auth.js` to make the initial CSRF token fetch conditional based on the user's logged-in status (passed from the backend via `window.TCGTRACKER_APP_CONFIG.isLoggedIn`). This prevents unnecessary and failing CSRF token requests on public, unauthenticated pages.
- **API Call Consistency (`authFetch`):**
    - Reverted `authFetch` to a simpler model where it does not automatically `JSON.stringify` the request body.
    - Ensured all calling modules (`deck-api.js`, `log-match.js`, `tagInput.js`, etc.) are now explicitly responsible for `JSON.stringify`-ing their JSON payloads before passing them to `authFetch`. This resolved `415 Unsupported Media Type` errors.

### Fixed
- **CSRF Token Fetch on Public Pages:** Resolved console errors (`401 Unauthorized`) caused by `auth.js` attempting to fetch CSRF tokens on public pages where the user is not authenticated.
- **API `415 Unsupported Media Type` Errors:** Corrected issues in `authFetch` and its callers (`deck-api.js`, `log-match.js`, `tagInput.js`) related to `Content-Type` headers and `JSON.stringify` for `POST` requests, ensuring backends receive correctly formatted JSON. This fixed errors when creating tags, registering decks, and logging matches.
- **JavaScript TypeErrors:**
    - Resolved `TypeError: window.associateTagWithDeck is not a function` in `registerDeck.js` by ensuring `associateTagWithDeck` is correctly imported from `deck-api.js` and called as a module function.
- **Deck Registration Logic:**
    - Fixed an issue in `registerDeck.js` where the `commander_id` was not being correctly read from the `dataset` attribute, preventing commander deck registration. Ensured consistency in `dataset` key usage (e.g., `dataset.commanderid`).
    - Corrected the payload key for deck type in `registerDeck.js` from `deck_type_id` to `deck_type` to match backend expectations, resolving "Deck type is required" errors.
- **Deck Sorting/Filtering Initialization:** Resolved "Cannot initialize deck sorting/filtering" error on `my-decks.html` by reverting sort and format filter controls to use standard `<select>` elements (as expected by the existing JS) while maintaining the new dark mode styling. The tag filter remains a custom button-based dropdown.
- **Dark Mode Activation:** Configured Tailwind CSS `darkMode: 'class'` in `tailwind.config.js` to prevent automatic dark mode switching based on OS/browser preferences, allowing for more explicit control (though the app currently defaults to the theme based on whether the `dark` class is on `<html>`).
- **Public Page Headers:** Ensured that public pages like "Explore Tournaments" and tournament detail views correctly display their page headers (logo, title) even when the user is not logged in, by adjusting `layout.html`.
- **Login Page Centering:** Restored centering for the login form after changes to `layout.html`'s main content area padding for public pages.

## [2.2.0] - 2025-05-13 

### Added
- **Tournament Settings Management (Organizer View):**
    - Implemented a feature allowing tournament organizers to edit the settings of their existing tournaments.
    - Added a dedicated form (`TournamentSettingsForm`) for updating tournament details: name, description, event date, format, status, pairing system, and maximum players. Includes input validation.
    - Created new Flask route `GET, POST /tournaments/<tournament_id>/settings` to display and process the settings form.
    - Developed `tournament_settings.html` template, styled for a light theme, with client-side enhancements (Flatpickr).
    - Ensured authorization restricts settings access to the tournament organizer.
- **"My Tournaments" Page Enhancements:**
    - Created a dedicated page (`GET /tournaments/`) for users to view a list of tournaments they have organized.
    - Implemented a **card-based layout** for displaying tournaments on the "My Tournaments" page, improving responsiveness and visual consistency with other app sections (e.g., "My Decks").
    - Added server-side sorting functionality to the "My Tournaments" list, allowing users to sort by Name, Status, Event Date, and Creation Date (ASC/DESC) via query parameters.
    - Included UI elements (select dropdown) for sort controls on `my-tournaments.html`, with basic JavaScript to trigger page reloads with sort parameters.
    - Added a placeholder for status filtering on the "My Tournaments" page.
    - Prominent "Create New Tournament" button added to the top of the "My Tournaments" page content.
- **Tournament Model:**
    - Enabled and ensured the `updated_at` timestamp field on the `Tournament` model to track when settings are last modified. (Requires database migration if not already applied).

### Changed
- **UI/UX - Tournament Pages:**
    - Refined the `view-tournament.html` page to display tournament details in a card-style layout for better visual organization and consistency.
    - Standardized page headers (logo and title) across tournament-related pages (`my-tournaments.html`, `view-tournament.html`, `tournament_settings.html`, `create-tournament.html`).
    - Ensured a consistent light theme across all tournament management pages by removing `dark:` mode specific styling and adjusting text/background colors for optimal readability.
    - Updated button styling on `view-tournament.html` for "Edit Tournament" and "Manage Participants" to preferred style.
- **Routing:**
    - The primary page for listing a user's organized tournaments is now consistently `/tournaments/`, handled by `tournaments.list_my_tournaments`.
    - Redirects after tournament creation and for not-found/archived tournaments now point to `/tournaments/`.

### Fixed
- **Client-Side Script Loading:** Resolved `ReferenceError: flatpickr is not defined` on tournament forms by ensuring the Flatpickr JavaScript library is correctly loaded before the custom `tournament_form.js` that initializes it. This involved adding Flatpickr script tags to `create-tournament.html` and `tournament_settings.html`.
- **Route Conflicts:** Resolved issue where `/my-tournaments` (handled by `frontend_bp`) was intercepting requests intended for the new tournament listing page. The `frontend_bp` route was removed in favor of `/tournaments/` handled by `tournaments_bp`.
- **Initial Data Display:** Addressed an issue where the "My Tournaments" page might not display tournaments on initial load by ensuring the correct route with data fetching logic is used.
- **Table Readability:** Improved text contrast on the "My Tournaments" table (before refactoring to cards) for better readability.
- **Database Initialization Errors:** Corrected SQLAlchemy `db` instance usage across the application (ensuring a single instance from `backend/database.py` is used by models and the app factory) to resolve "Table 'tournaments' is already defined" errors during startup.
- **Import Errors:** Fixed `cannot import name 'limiter' from 'backend.database'` by ensuring `limiter` and other extensions are correctly instantiated and imported from their proper locations (primarily `backend/__init__.py`).

## [2.1.0] - YYYY-MM-DD 

### Added
- **Tournament Creation (Organizer View):**
    - Implemented a new feature allowing logged-in users to create tournament events.
    - Added a dedicated form (`TournamentCreationForm`) for capturing tournament details: name, description, event date, format, pairing system, and maximum players. Includes input validation.
    - Created new Flask routes under the `/tournaments` prefix:
        - `GET /tournaments/new`: Displays the tournament creation form.
        - `POST /tournaments/new`: Processes the form submission, validates data, and creates a new `Tournament` record in the database, associating it with the logged-in user as the organizer. Sets default status to "Planned".
    - Developed new Jinja2 templates for the tournament creation process:
        - `create-tournament.html`: Renders the tournament creation form, styled with Tailwind CSS, and displays validation errors.
        - `view-tournament.html`: A placeholder page to display details of a newly created tournament (will be expanded later).
    - Integrated a client-side JavaScript date/time picker (Flatpickr) for the "Event Date" field on the creation form for improved user experience.
    - Added `tournament_form.js` for client-side enhancements on the tournament creation form.
    - Ensured the new tournament creation routes are protected by login requirements and include rate limiting.
    - Updated `layout.html` to include Flatpickr CSS and JS.
    - Registered the new `tournaments_bp` blueprint, ensuring correct URL prefixing for tournament-related HTML pages.

### Changed
- Refactored route handling for tournament creation to reside within a dedicated `tournaments_bp` blueprint (in `backend/routes/tournaments.py`) instead of `frontend_bp`, improving modularity.

### Fixed
- Resolved `jinja2.exceptions.UndefinedError: 'form' is undefined` by ensuring the correct Flask route (`tournaments.create_tournament`) was handling the `/tournaments/new` URL and passing the `TournamentCreationForm` instance to the template. This involved removing a conflicting route definition from `frontend.py`.
- Corrected `werkzeug.routing.exceptions.BuildError` in templates by ensuring `url_for()` calls for tournament endpoints use underscores (e.g., `url_for('tournaments.create_tournament')`) consistent with Python function names.
- Fixed `jinja2.exceptions.TemplateNotFound` for `view-tournaments.html` by updating the `render_template` call in the `view_tournament` route to use the correct hyphenated filename.
- Ensured that `is_logged_in` and `user` context variables are passed to templates rendered by the `tournaments_bp` routes, allowing the shared `layout.html` (including the page header) to render correctly.

## [2.0.1] - 2025-05-05

### Fixed
- Win, lose, draw values corrected.

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