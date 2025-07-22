# backend/services/decks/deck_scraper.py

import requests
import json
import logging
import re

logger = logging.getLogger(__name__)

# This function is now just for getting the card list from Moxfield
def get_card_identifiers_from_moxfield(deck_url):
    """Fetches a decklist from Moxfield's API and returns a list of Scryfall identifiers."""
    if "moxfield.com" not in deck_url:
        raise ValueError("URL must be a valid Moxfield decklist.")

    match = re.search(r'/decks/([a-zA-Z0-9_-]+)', deck_url)
    if not match:
        raise ValueError("Could not extract a valid deck ID from the URL.")
    deck_id = match.group(1)

    api_url = f"https://api2.moxfield.com/v2/decks/all/{deck_id}"
    headers = {
        'User-Agent': 'TcgTrackerApp/1.0 (+https://tcg-tracker.fly.dev; mailto:spamgaston@gmail.com)'
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        deck_data = response.json()
    except requests.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 404:
            # Enhanced logging with the full URL
            logger.warning(f"Moxfield deck not found (404) for URL '{deck_url}'. It might be private or deleted.")
            raise ValueError("Moxfield deck not found. Please ensure the URL is correct and the deck is set to 'Public'.")
        elif status_code == 403:
            # Enhanced logging with the full URL
            logger.warning(f"Moxfield deck access forbidden (403) for URL '{deck_url}'. The deck may be private or the server IP may be blocked.")
            raise ValueError("Access to this Moxfield deck is forbidden. Please ensure the deck is set to 'Public'.")
        else:
            logger.error(f"HTTP error {status_code} when fetching from Moxfield for URL '{deck_url}': {e}")
            raise ConnectionError(f"Moxfield's API responded with an error (Code: {status_code}). Please try again later.")
    except requests.RequestException as e:
        logger.error(f"Network error when fetching from Moxfield API for URL '{deck_url}': {e}")
        raise ConnectionError("Could not connect to Moxfield's API. There may be a network issue.")

    mainboard = deck_data.get('mainboard', {})
    if not mainboard:
        raise ValueError("API response did not contain a 'mainboard' object.")

    identifiers = []
    for card_name, card_info in mainboard.items():
        scryfall_id = card_info.get('card', {}).get('scryfall_id')
        quantity = card_info.get('quantity', 0)
        if scryfall_id and quantity > 0:
            identifiers.append({"scryfall_id": scryfall_id, "quantity": quantity})

    if not identifiers:
        raise ValueError("Deck appears to be empty or card IDs could not be found.")
        
    return identifiers

# This new function gets all card details from Scryfall in one go
def get_card_details_from_scryfall(identifiers):
    """Takes a list of Scryfall identifiers and quantities, fetches their full data."""
    if not identifiers:
        return []

    all_card_data = []
    chunk_size = 75
    
    quantity_map = {item['scryfall_id']: item['quantity'] for item in identifiers}
    scryfall_identifiers = [{"id": item['scryfall_id']} for item in identifiers]

    for i in range(0, len(scryfall_identifiers), chunk_size):
        chunk = scryfall_identifiers[i:i + chunk_size]
        
        scryfall_api_url = "https://api.scryfall.com/cards/collection"
        headers = {'Content-Type': 'application/json'}
        payload = {"identifiers": chunk}

        try:
            response = requests.post(scryfall_api_url, headers=headers, json=payload)
            response.raise_for_status()
            scryfall_data = response.json()
            
            for card in scryfall_data.get('data', []):
                card['quantity'] = quantity_map.get(card['id'], 0)
            
            all_card_data.extend(scryfall_data.get('data', []))
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch from Scryfall collection API: {e}")
            raise ConnectionError("Could not retrieve card details from Scryfall.")

    return all_card_data

# This function now analyzes the rich data from Scryfall
def analyze_scryfall_data(scryfall_card_list):
    """
    Takes a list of full Scryfall card objects and returns structured analysis,
    including average CMC and card counts.
    """
    primary_types = ['Creature', 'Instant', 'Sorcery', 'Artifact', 'Enchantment', 'Planeswalker', 'Land']
    analysis = {card_type: {i: 0 for i in range(11)} for card_type in primary_types + ['Other']}
    
    total_cmc_sum = 0.0
    non_land_card_count = 0
    land_card_count = 0

    for card in scryfall_card_list:
        type_line = card.get('type_line', '')
        quantity = card.get('quantity', 0)
        cmc = card.get('cmc', 0.0)
        curve_key = min(int(cmc), 10)

        assigned_type = 'Other'
        is_land = 'Land' in type_line

        if is_land:
            assigned_type = 'Land'
            land_card_count += quantity
        else:
            total_cmc_sum += cmc * quantity
            non_land_card_count += quantity
            
            for p_type in primary_types:
                if p_type in type_line:
                    assigned_type = p_type
                    break
        
        analysis[assigned_type][curve_key] += quantity

    average_cmc = (total_cmc_sum / non_land_card_count) if non_land_card_count > 0 else 0.0
    final_analysis = {k: v for k, v in analysis.items() if sum(v.values()) > 0}
    
    return {
        'analysis': final_analysis,
        'average_cmc': average_cmc,
        'non_land_count': non_land_card_count,
        'land_count': land_card_count
    }