document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("register-form").addEventListener("submit", async function (event) {
      event.preventDefault();

      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;
      const confirmation = document.getElementById("confirmation").value;

      if (password !== confirmation) {
        showFlashMessage("Passwords do not match.", "error");
        return;
      }

      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, confirmation }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("username", data.username);

        sessionStorage.setItem("flashMessage", `Welcome ${data.username}!`);
        sessionStorage.setItem("flashType", "success");

        window.location.href = "/";
      }

      if (!response.ok) {
        showFlashMessage(data.error, "error");
      }
    });
  });