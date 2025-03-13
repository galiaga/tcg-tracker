const SCRYFALL_API = "https://api.scryfall.com/cards/search?q=";

export async function searchCommander(query) {
    if (!query) return [];

    try {
        const url = `${SCRYFALL_API}${encodeURIComponent(query)}+is:commander`;
        console.log("Fetching:", url);

        const response = await fetch(url);

        // 🔹 Si Scryfall devuelve un 404 (sin resultados), manejamos el error aquí
        if (response.status === 404) {
            console.warn(`⚠ No se encontraron resultados para: "${query}"`);
            return [];
        }

        if (!response.ok) throw new Error(`Scryfall API Error: ${response.status}`);

        const data = await response.json();

        // 🔹 Filtrar solo los nombres que comienzan con la búsqueda
        const filteredResults = data.data.filter(card =>
            card.name.toLowerCase().startsWith(query.toLowerCase())
        );

        return filteredResults.map(card => ({
            id: card.id,
            name: card.name
        }));
    } catch (error) {
        console.error("Scryfall API Error:", error);
        return [];
    }
}
