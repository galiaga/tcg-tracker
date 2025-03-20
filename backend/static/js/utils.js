// Utility function to map match results
export function formatMatchResult(result) {
    const resultsMap = { 0: 'Win', 1: 'Loss', 2: 'Draw' }
    return resultsMap[result] || 'Unknown';
}