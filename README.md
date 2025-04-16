# TCG Tracker
#### Video Demo: https://youtu.be/aRYaDvsCBSA
#### Description: 
This project is a web application designed for Trading Card Game (TCG) players to systematically track and analyze deck performance. It provides an interface, optimized for mobile use, allowing rapid logging of match outcomes, opponent deck types, and win/loss conditions. The backend, built with Python and Flask, processes this data to generate performance statistics, such as overall win rates and matchup-specific results. A JavaScript front end renders this information. Data persistence is managed via SQLite during development and PostgreSQL in production, ensuring scalability and data integrity essential for performance analysis.

TCG Tracker is a web app that uses JavaScript for its front end and has a significant focus on user experience and interface. One of the problems the app aims to solve is that TCG Players typically don't want to spend much time logging information; they want to focus on playing and winning games. Consequently, the app needed to be as simple and lightweight as possible. That's why the app is straightforward enough for users to log information quickly but provides all the minimal information required to meet the goal of delivering valuable insights, enabling a TCG Player to make the best decisions with their decks based on actual performance data.

The app is based on the 'My Decks' section, where users are able to create, add, and start tracking their decks. While creating a new deck, users can select a Deck Type, define its name, and add optional Tags for organizational purposes. The first iteration of the app is specifically related to Magic: The Gathering (MTG), so MTG players are able to identify specific Commanders for their Commander decks, a key feature for players of that popular format.

Once created, Decks within the 'My Decks' section are sorted by default by 'Last Played' date, but users can also sort their Decks alphabetically by 'Deck Name', by calculated 'Win Rate' (which shows the percentage of matches won versus total matches played), by the total number of 'Matches Played', and by 'Date Added'. They can also filter the displayed Decks by selecting a specific game Format or one or more assigned Tags for focused viewing.

The decks are shown using a visual 'card' element, allowing for easy visibility and sorting within both mobile and desktop user experiences. These deck cards display key details and feature a color-coded background based on their calculated Win Rate: red is associated with a Win Rate below 40%, yellow indicates a Win Rate between 40% and 60%, and green signifies a Win Rate above 60%. This intuitive system allows users to easily understand at a glance which decks have better overall performance.

Decks can be edited by users, allowing them to change their name or even delete them completely if needed. Furthermore, Tags can be easily added to or removed from Decks at any time, empowering users to readily organize their Decks using Tags. This feature maximizes flexibility to accommodate different TCGs and individual player organizational needs.

Once created, Decks can start having individual Matches associated with them. Each Match can be recorded as Won, Loss, or Draw for the corresponding Deck. This system allows users to easily and quickly log their results throughout the day, particularly useful while playing at Leagues or Tournaments. They can select a specific Deck to log results against, or they can perform this action within the dedicated 'My Matches' section. Matches can also be associated with Tags, enabling players to easily connect their match data with a Tag that links them to the relevant League or Tournament, the kind of Deck they were playing against, or any other characteristic of the Match that might be relevant for later analysis. Once again, this design choice maximizes flexibility for users.
The 'My Matches' section offers users the option to filter their logged Matches by associated Tags. The matches displayed in this section are sorted by default from newest to oldest ('new to old'), allowing users to have easy access to review their latest played games and performance trends.

Additionally, the 'My Tags' section allows users to easily view all the Decks and Matches that are currently connected with one or more specific Tags. This way, users gain a complete understanding of all the items within the app that utilize a particular Tag, thereby maximizing organizational capabilities and offering enhanced flexibility for analysis. Users can easily add or remove Tags from both Decks and Matches directly, and these changes automatically update the list of associated elements displayed on the 'My Tags' page, ensuring data consistency.

TCG Tracker requires users to register with a unique username and password to start using the application and track their personal data. The application utilizes Flask secrets to manage the user session securely, helping to avoid potential cyber-attacks related to session handling. Furthermore, it employs a CSRF (Cross-Site Request Forgery) compatible token mechanism, which significantly reduces its vulnerability to certain types of web attacks. For user convenience, active sessions are persistent. This means users remain logged in on the app across browser sessions until they explicitly choose to log out by pressing the 'Logout' option provided within the application's menu structure.




TCG Tracker - Setup and Installation Guide

Welcome! This guide will walk you through setting up the TCG Tracker project on your local machine. Follow these steps carefully.

1. Prerequisites (What You Need First)

Before starting, make sure you have these tools installed on your computer:

*   Git: Used for downloading (cloning) the project code.
*   Python: Version 3.8 or higher is recommended. You can check your version by opening a terminal or command prompt and typing:
    python --version
    Python usually comes with pip, its package installer.
*   Node.js: The LTS (Long Term Support) version is recommended (check the Node.js website). This includes npm (Node Package Manager), which we need for the website's styling tools. Check your version:
    node --version
    npm --version
*   (Optional) PostgreSQL: This project uses SQLite (a simple file-based database) for development by default, so you probably DON'T need to install PostgreSQL just to run it locally. It's listed as a requirement (psycopg2-binary) because the production version is configured for it.

2. Getting the Code

First, download the project code using Git:

    # Replace <your-repository-url> with the actual URL you're cloning from
    git clone <your-repository-url>

    # Navigate into the project directory
    cd tcg-tracker

(The `cd` command means "change directory")

3. Setting Up the Backend (Python/Flask)

We need to create an isolated space for our Python packages and configure the application.

a. Create a Virtual Environment

This keeps the Python packages for this project separate from others on your system (good practice!).

*   Create the environment (run this command inside the tcg-tracker folder):
    python -m venv .venv
    (This creates a hidden folder named .venv)

*   Activate the environment: You need to "turn on" this environment each time you work on the project in a new terminal window.
    *   On Windows (Command Prompt / PowerShell):
        .\.venv\Scripts\activate
    *   On macOS / Linux (Bash / Zsh):
        source .venv/bin/activate
    *   Success: You should see (.venv) appear at the beginning of your terminal prompt.

b. Configure Environment Variables (.env file)

The application needs some secret settings, like a key for security. We use a special file called .env for this. This file is NOT included in the repository for security reasons.

*   Create the file: In the main tcg-tracker folder, create a new file named exactly .env (notice the dot at the beginning).
*   Add content: Open the .env file in your text editor and add the following lines. This tells Flask how to run and provides essential keys.

    # --- Start of .env file content ---

    # Flask Settings
    SECRET_KEY='PLEASE_CHANGE_ME_TO_A_LONG_RANDOM_STRING' # Important! Generate a real secret key.
    FLASK_APP=app.py    # Tells Flask which file starts the app
    FLASK_DEBUG=1       # Enables helpful error messages for development (set to 0 for production)

    # Database Connection (Using SQLite for Development)
    # This tells the app to create and use a simple database file inside an 'instance' folder.
    DATABASE_URL='sqlite:///instance/dev.db'

    # --- End of .env file content ---

*   VERY IMPORTANT: Replace 'PLEASE_CHANGE_ME_TO_A_LONG_RANDOM_STRING' with a long, random string of characters. You can generate one using online tools or Python itself. This key keeps user sessions secure.

c. Install Python Dependencies

Now, let's install all the Python packages listed in requirements.txt. Make sure your virtual environment (.venv) is still active!

    pip install -r requirements.txt

(This might take a few moments as it downloads and installs Flask, SQLAlchemy, etc.)

4. Setting Up the Frontend (Styling with Tailwind CSS)

This project uses Tailwind CSS for styling. We need Node.js/npm to install the tools and build the final CSS file.

a. Install Node.js Dependencies

This command reads package.json and installs the necessary development tools (like Tailwind).

    npm install

(This creates a node_modules folder containing the tools. You should NOT commit this folder to Git.)

b. Build the CSS File

Tailwind needs to process your style rules and create a final CSS file that the browser understands. Since there isn't a pre-defined script in package.json, you'll likely need to run the Tailwind command directly.

*   Run the build command:
    npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css

    Explanation:
    *   npx tailwindcss: Runs the Tailwind command-line tool installed by npm install.
    *   -i ./static/src/input.css: Specifies the input CSS file where you (or the project) define styles using Tailwind classes. (You might need to check your project structure and adjust this path if static/src/input.css doesn't exist or is named differently!)
    *   -o ./static/dist/output.css: Specifies the output CSS file that Tailwind generates. This is the file that your HTML templates will link to. (Check your HTML templates (<link rel="stylesheet">) to confirm this path is correct!)

*   (Optional) Watch for Changes during Development: If you plan to edit styles, you can run this command instead. It will automatically rebuild the CSS whenever you save changes to your input CSS or template files using Tailwind classes:
    npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --watch
    (Leave this running in a separate terminal while you work on styles.)

5. Setting Up the Database

This project uses Flask-Migrate to manage the database structure (creating tables, etc.).

*   Make sure your DATABASE_URL in the .env file is set correctly (it should be for SQLite by default).
*   Apply the database migrations: Make sure your virtual environment (.venv) is active.
    flask db upgrade
    (This command looks at the files in the migrations folder and applies them to create the necessary tables in your instance/dev.db file.)

6. Running the Application!

You're ready to run the web server!

*   Make sure your virtual environment (.venv) is active.
*   Run the Flask development server:
    flask run
*   Open your browser: The terminal will show output like * Running on http://127.0.0.1:5000. Open that URL (usually http://localhost:5000) in your web browser.

You should now see the TCG Tracker application running!

7. Running Tests (Optional)

This project includes automated tests using Pytest. To run them:

*   Make sure your virtual environment (.venv) is active.
*   Run the tests:
    pytest
    (This will find files starting with test_ and run the functions inside them to check if the code works as expected.)


That's it! If you encounter any issues, double-check that you followed each step, that your virtual environment is active, and that your .env file is correctly configured. Good luck and start logging matches!!!

Gastón
