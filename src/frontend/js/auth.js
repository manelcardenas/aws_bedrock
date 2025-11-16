// ============================================
// Authentication Handler
// ============================================

document.addEventListener("DOMContentLoaded", function () {
  // Check if already authenticated and redirect to main app
  if (isAuthenticated()) {
    window.location.href = "index.html";
    return;
  }

  initLoginForm();
});

function initLoginForm() {
  const loginForm = document.getElementById("login-form");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();

    // Validation
    if (!username || !password) {
      showLoginError("Please enter both username and password");
      return;
    }

    // Hide previous errors
    hideLoginError();

    // Show loading state
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    setButtonLoading(submitBtn, true);

    try {
      const response = await fetch(`${CONFIG.AUTH_API_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error ||
            errorData.message ||
            `Login failed: ${response.status}`
        );
      }

      const data = await response.json();

      if (!data.token) {
        throw new Error("No token received from server");
      }

      // Store JWT token and username
      setJwtToken(data.token);
      setUsername(username);

      // Show success message briefly before redirect
      showNotification("Login successful! Redirecting... ✅");

      // Redirect to main app after short delay
      setTimeout(() => {
        window.location.href = "index.html";
      }, 500);
    } catch (error) {
      console.error("Login error:", error);
      showLoginError(error.message || "Login failed. Please try again.");
    } finally {
      setButtonLoading(submitBtn, false);
    }
  });
}

// ============================================
// Error Display
// ============================================
function showLoginError(message) {
  const errorBox = document.getElementById("login-error");
  if (errorBox) {
    errorBox.textContent = message;
    errorBox.style.display = "block";
  }
}

function hideLoginError() {
  const errorBox = document.getElementById("login-error");
  if (errorBox) {
    errorBox.style.display = "none";
  }
}

// ============================================
// Button Loading State
// ============================================
function setButtonLoading(button, isLoading) {
  const btnText = button.querySelector(".btn-text");
  const loader = button.querySelector(".loader");

  button.disabled = isLoading;

  if (isLoading) {
    btnText.style.display = "none";
    loader.style.display = "block";
  } else {
    btnText.style.display = "inline";
    loader.style.display = "none";
  }
}

// ============================================
// Notification
// ============================================
function showNotification(message) {
  const notification = document.createElement("div");
  notification.className = "notification";
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #28a745;
    color: white;
    padding: 15px 25px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 1000;
    animation: slideInRight 0.3s ease-out;
  `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease-out";
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 2000);
}

// Add notification animations if not already present
if (!document.getElementById("notification-styles")) {
  const style = document.createElement("style");
  style.id = "notification-styles";
  style.textContent = `
    @keyframes slideInRight {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slideOutRight {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);
}
