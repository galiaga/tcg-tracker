import { authFetch } from '../auth/auth.js';

const BASE_API_URL = '/api';

async function searchCommanders(query, type = null) {
    try {
        const params = new URLSearchParams({ q: query });
        // Only append 'type' if it's a meaningful filter for associated commanders
        if (type && type !== 'unknown' && type !== 'primary') { 
            params.append('type', type.toLowerCase()); // Ensure type is lowercase for backend matching
        }
        const response = await authFetch(`${BASE_API_URL}/search_commanders?${params.toString()}`);
        if (!response.ok) {
            console.error(`API Error searching commanders: ${response.status} - ${response.statusText}`);
            const errorData = await response.json().catch(() => ({ error: "Failed to parse error response" }));
            throw new Error(errorData.error || `Failed to search commanders (Status: ${response.status})`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error in searchCommanders:", error);
        // Re-throw to be caught by the caller (e.g., TagInputManager or log-match-modal)
        throw error; 
    }
}

async function getCommanderAttributes(commanderId) {
    const apiUrl = `${BASE_API_URL}/get_commander_attributes?q=${commanderId}`;
    const response = await authFetch(apiUrl);
     if (!response) {
         throw new Error("Authentication or network error fetching attributes.");
     }
    if (!response.ok) {
        let errorMsg = `Failed to fetch commander attributes (Status: ${response.status})`;
        try {
            const errData = await response.json();
            errorMsg = errData.error || errorMsg;
        } catch(e) { /* Ignore parse error */ }
        console.error("Error fetching commander attributes:", response.status, response.statusText, errorMsg);
        throw new Error(errorMsg);
    }
    return await response.json();
}

async function registerDeck(payload) {
    // ... (remains the same)
    const apiUrl = `${BASE_API_URL}/register_deck`;
    const response = await authFetch(apiUrl, {
        method: 'POST',
        body: JSON.stringify(payload)
    });
     if (!response) {
         throw new Error("Authentication or network error registering deck.");
     }
    return response;
}

async function associateTagWithDeck(deckId, tagId) {
    // ... (remains the same)
    const apiUrl = `${BASE_API_URL}/decks/${deckId}/tags`;
    const response = await authFetch(apiUrl, {
        method: 'POST',
        body: JSON.stringify({ tag_id: tagId })
    });
     if (!response) {
         throw new Error(`Authentication or network error associating tag ${tagId}.`);
     }
    return response;
}

export {
    searchCommanders,
    getCommanderAttributes,
    registerDeck,
    associateTagWithDeck
};