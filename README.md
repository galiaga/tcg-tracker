# TCG Tracker
#### Video Demo: https://youtu.be/aRYaDvsCBSA
#### Description: 
Okay, here is the proofread version of the text you provided. I have focused on correcting grammar, spelling, punctuation, and ensuring consistency in terminology and capitalization. Minor adjustments were made for clarity and flow, keeping the core content intact and adjusting the length to be just over 700 words as requested.

This project is a web application designed for Trading Card Game (TCG) players to systematically track and analyze deck performance. It provides an interface, optimized for mobile use, allowing rapid logging of match outcomes, opponent deck types, and win/loss conditions. The backend, built with Python and Flask, processes this data to generate performance statistics, such as overall win rates and matchup-specific results. A JavaScript front end renders this information. Data persistence is managed via SQLite during development and PostgreSQL in production, ensuring scalability and data integrity for performance analysis.

TCG Tracker is a web app that uses JavaScript for its front end and focuses significantly on user experience and interface. One of the problems the app aims to solve is that TCG players don't want to spend much time logging information; they want to focus on playing and winning games. The app needed to be as simple and lightweight as possible. Consequently, the app is simple enough for quick information logging yet provides the minimal data required for valuable insights, helping players make the best decisions with their decks.

The app is based on the 'My Decks' section, where users are able to create and add decks to begin tracking them. While creating a new deck, users can select a Deck Type, define its name, and add optional tags for organization purposes. The first iteration of the app is related to Magic: The Gathering (MTG); consequently, MTG players are able to identify specific Commanders for their Commander decks, a key detail for that format.

Once created, decks are sorted by default by 'Last Played', but users can also sort decks alphabetically by 'Deck Name', by 'Win Rate' (which shows the percentage of matches won versus total matches played), by total 'Matches Played', and by 'Date Added'. They can filter the decks by selecting a specific format or one or more relevant tags, allowing for focused analysis.

The decks are displayed as distinct card elements, ensuring easy visibility and sorting on both mobile and desktop. These cards show essential details and feature a dynamic color background based on win rate: red for below 40%, yellow for 40-60%, and green for above 60%. This visual system helps users instantly gauge deck performance.

Decks can be edited by users, allowing them to change a deck's name or delete it completely. Tags can also be added or removed from decks at any time, allowing users to easily organize their collection. This flexible use of tags maximizes organization for different TCGs and player needs.

Once created, decks can have matches associated with them. Each match can be recorded as a Win, Loss, or Draw. This allows users to easily and quickly log their results while playing in leagues or tournaments. Users can log results from a specific deck's view or directly in the 'My Matches' section. Matches can also be associated with tags, allowing players to connect matches with tags for leagues, tournaments, opponent archetypes, or other relevant characteristics for later analysis. This tagging maximizes user flexibility.

The 'My Matches' section offers the option to filter matches by tag. Matches are sorted chronologically from newest to oldest, allowing users easy access to their latest played games.

The 'My Tags' section allows users to easily view all decks and matches connected with one or more specific tags. This way, users gain a complete understanding of all items associated with a tag, maximizing organizational capabilities and flexibility. Users can easily add or remove tags from decks and matches; these changes automatically update the list of elements displayed on the 'My Tags' page, ensuring data consistency.

TCG Tracker requires users to register with a unique username and password to start using the app. It uses Flask secrets to manage user sessions securely, helping to prevent potential cyber-attacks. Furthermore, it employs a CSRF-compatible token mechanism that reduces vulnerability to cross-site request forgery.

Users remain logged into the app until they explicitly choose to log out by selecting the 'Logout' option via the application menu. TCG Tracker aims to be the go-to tool for players serious about improving their game through data.
