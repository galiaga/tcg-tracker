CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
CREATE TABLE commanders (
	id INTEGER NOT NULL, 
	scryfall_id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	flavor_name VARCHAR, 
	mana_cost VARCHAR, 
	type_line VARCHAR, 
	oracle_text TEXT, 
	power VARCHAR, 
	toughness VARCHAR, 
	loyalty VARCHAR, 
	colors VARCHAR, 
	color_identity VARCHAR, 
	set_code VARCHAR, 
	image_url VARCHAR, 
	art_crop VARCHAR, 
	updated_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	partner BOOLEAN DEFAULT '0' NOT NULL, 
	background BOOLEAN DEFAULT '0' NOT NULL, 
	choose_a_background BOOLEAN DEFAULT '0' NOT NULL, 
	friends_forever BOOLEAN DEFAULT '0' NOT NULL, 
	doctor_companion BOOLEAN DEFAULT '0' NOT NULL, 
	time_lord_doctor BOOLEAN DEFAULT '0' NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (scryfall_id)
);
CREATE TABLE deck_types (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	hash VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);
CREATE TABLE decks (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	deck_type_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deck_type_id) REFERENCES deck_types (id)
);
CREATE TABLE commander_decks (
	id INTEGER NOT NULL, 
	deck_id INTEGER NOT NULL, 
	commander_id INTEGER NOT NULL, 
	associated_commander_id INTEGER, 
	relationship_type VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(commander_id) REFERENCES commanders (id), 
	FOREIGN KEY(deck_id) REFERENCES decks (id)
);
CREATE TABLE user_decks (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	deck_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deck_id) REFERENCES decks (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE matches (
	id INTEGER NOT NULL, 
	timestamp DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	result INTEGER NOT NULL, 
	user_deck_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT check_match_result CHECK (result IN (0, 1, 2)), 
	FOREIGN KEY(user_deck_id) REFERENCES user_decks (id)
);
