import { authFetch } from '../auth/auth.js';

let cachedUserTags = null;
let isFetching = false;

async function fetchUserTags(forceRefresh = false) {
    if (!forceRefresh && cachedUserTags !== null) {
        return cachedUserTags;
    }
    if (isFetching) {
        return cachedUserTags;
    }

    isFetching = true;
    try {
        const response = await authFetch("/api/tags");
        if (!response) {
             throw new Error("Auth or network error fetching tags");
        }
        if (!response.ok) {
             console.error("tagUtils.js: API response not OK", response);
             throw new Error(`Failed to fetch tags: ${response.status}`);
        }
        const tags = await response.json();
        tags.sort((a, b) => a.name.localeCompare(b.name));
        cachedUserTags = tags;
        return tags;
    } catch (error) {
         return null;
    } finally {
         isFetching = false;
    }
}

function invalidateTagCache() {
     cachedUserTags = null;
     isFetching = false;
}

export { fetchUserTags, invalidateTagCache };