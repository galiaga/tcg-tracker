async function fetchProtectedData() {
    const token = localStorage.getItem("access_token");

    if (!token) {
        console.warn("No token found. User might be logged out.");
        return;
    }

    const response = await fetch("/api/protected-route", {
        method: "GET",
        headers: { "Authorization": `Bearer ${localStorage.getItem("access_token")}` }
    });

    if (response.ok) {
        const data = await response.json();
        console.log("Protected data:", data);
    } else {
        console.error("Failed to access protected data");
        if (response.status === 401) {
            console.warn("Session expired. Logging out...");
            logout();
        }
    }
}