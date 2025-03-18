export async function searchCommander(query) {
    if (!query.trim()) return [];

    try {
        const response = await authFetch(`/api/search_commanders?q=${encodeURIComponent(query)}`);
        
        if (!response) return;

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Error fetching commanders:", error);
        return [];
    }
}
