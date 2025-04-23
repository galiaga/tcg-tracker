import { authFetch } from '../auth/auth.js';

// --- Configuration ---
const BASE_API_URL = '/api'; // Or your actual API base path

// --- API Functions ---

async function searchCommanders(query, type) {
    const apiUrl = `${BASE_API_URL}/search_commanders?q=${encodeURIComponent(query)}&type=${type}`;
    // Using standard fetch here as it seems this endpoint might not require auth based on original code
    const response = await fetch(apiUrl);
    if (!response.ok) {
        console.error(`API Error: ${response.status} - ${response.statusText}`);
        throw new Error(`Failed to search commanders (Status: ${response.status})`);
    }
    return await response.json();
}

async function getCommanderAttributes(commanderId) {
    const apiUrl = `${BASE_API_URL}/get_commander_attributes?q=${commanderId}`;
    const response = await authFetch(apiUrl); // Assuming this needs auth
     if (!response) {
         // authFetch likely handled error/redirect
         throw new Error("Authentication or network error fetching attributes.");
     }
    if (!response.ok) {
        let errorMsg = `Failed to fetch commander attributes (Status: ${response.status})`;
        try {
            const errData = await response.json();
            errorMsg = errData.error || errorMsg;
        } catch(e) { /* Ignore parse error */ }
        console.error("Error fetching commander attributes:", response.status, response.statusText);
        throw new Error(errorMsg);
    }
    return await response.json();
}

async function registerDeck(payload) {
    const apiUrl = `${BASE_API_URL}/register_deck`;
    const response = await authFetch(apiUrl, {
        method: 'POST',
        body: JSON.stringify(payload)
    });
     if (!response) {
         throw new Error("Authentication or network error registering deck.");
     }
    // Let the caller handle non-OK responses based on JSON content
    return response; // Return the full response object
}

async function associateTagWithDeck(deckId, tagId) {
    const apiUrl = `${BASE_API_URL}/decks/${deckId}/tags`;
    const response = await authFetch(apiUrl, {
        method: 'POST',
        body: JSON.stringify({ tag_id: tagId })
    });
     if (!response) {
         throw new Error(`Authentication or network error associating tag ${tagId}.`);
     }
    // Return the response for the caller to check status
    return response;
}

// --- Exports ---
export {
    searchCommanders,
    getCommanderAttributes,
    registerDeck,
    associateTagWithDeck
};