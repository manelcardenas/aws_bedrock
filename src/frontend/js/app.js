// ============================================
// AWS Bedrock Playground - Main Application
// ============================================

document.addEventListener("DOMContentLoaded", function () {
  // Check authentication
  if (!isAuthenticated()) {
    window.location.href = "login.html";
    return;
  }

  initializeApp();
});

function initializeApp() {
  // Display username
  displayUsername();

  // Initialize character counters
  initCharacterCounters();

  // Initialize event listeners
  initEventListeners();
}

// ============================================
// Character Counters
// ============================================
function initCharacterCounters() {
  const textInput = document.getElementById("text-input");
  const charCount = document.getElementById("char-count");

  const descInput = document.getElementById("description-input");
  const descCharCount = document.getElementById("desc-char-count");

  textInput.addEventListener("input", () => {
    charCount.textContent = `${textInput.value.length} / 5000`;
  });

  descInput.addEventListener("input", () => {
    descCharCount.textContent = `${descInput.value.length} / 500`;
  });
}

// ============================================
// User Display
// ============================================
function displayUsername() {
  const username = getUsername();
  const usernameDisplay = document.getElementById("username-display");
  if (usernameDisplay && username) {
    usernameDisplay.textContent = username;
  }
}

// ============================================
// Event Listeners
// ============================================
function initEventListeners() {
  // Logout button
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
  }

  // Text Summarization
  const summarizeBtn = document.getElementById("summarize-btn");
  summarizeBtn.addEventListener("click", handleSummarize);

  const copySummaryBtn = document.getElementById("copy-summary-btn");
  copySummaryBtn.addEventListener("click", () => {
    const summaryContent =
      document.getElementById("summary-content").textContent;
    copyToClipboard(summaryContent);
  });

  // Image Generation
  const generateBtn = document.getElementById("generate-btn");
  generateBtn.addEventListener("click", handleGenerateImage);

  const downloadImageBtn = document.getElementById("download-image-btn");
  downloadImageBtn.addEventListener("click", handleDownloadImage);

  const openImageBtn = document.getElementById("open-image-btn");
  openImageBtn.addEventListener("click", () => {
    const imageUrl = document.getElementById("generated-image").src;
    if (imageUrl) {
      window.open(imageUrl, "_blank");
    }
  });
}

// ============================================
// Text Summarization
// ============================================
async function handleSummarize() {
  const textInput = document.getElementById("text-input");
  const pointsInput = document.getElementById("points-input");
  const summarizeBtn = document.getElementById("summarize-btn");
  const resultBox = document.getElementById("summary-result");
  const errorBox = document.getElementById("summary-error");
  const summaryContent = document.getElementById("summary-content");

  const text = textInput.value.trim();
  const points = parseInt(pointsInput.value);

  // Validation
  if (!text) {
    showError("summary-error", "Please enter text to summarize");
    return;
  }

  if (!points || points < 1 || points > 10) {
    showError("summary-error", "Please enter a valid number of points (1-10)");
    return;
  }

  const token = getJwtToken();
  if (!token) {
    showError("summary-error", "Authentication required. Please login again.");
    setTimeout(() => logout(), 2000);
    return;
  }

  // Hide previous results/errors
  resultBox.style.display = "none";
  errorBox.style.display = "none";

  // Show loading state
  setButtonLoading(summarizeBtn, true);

  try {
    const response = await fetch(`${CONFIG.TEXT_PROXY_URL}?points=${points}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        showError("summary-error", "Session expired. Please login again.");
        setTimeout(() => logout(), 2000);
        return;
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.error || `HTTP error! status: ${response.status}`
      );
    }

    const data = await response.json();

    // Display result
    summaryContent.textContent = data.summary;
    resultBox.style.display = "block";
  } catch (error) {
    console.error("Error:", error);
    showError("summary-error", `Failed to summarize text: ${error.message}`);
  } finally {
    setButtonLoading(summarizeBtn, false);
  }
}

// ============================================
// Image Generation
// ============================================
async function handleGenerateImage() {
  const descInput = document.getElementById("description-input");
  const generateBtn = document.getElementById("generate-btn");
  const resultBox = document.getElementById("image-result");
  const errorBox = document.getElementById("image-error");
  const generatedImage = document.getElementById("generated-image");

  const description = descInput.value.trim();

  // Validation
  if (!description) {
    showError("image-error", "Please enter a description for the image");
    return;
  }

  const token = getJwtToken();
  if (!token) {
    showError("image-error", "Authentication required. Please login again.");
    setTimeout(() => logout(), 2000);
    return;
  }

  // Hide previous results/errors
  resultBox.style.display = "none";
  errorBox.style.display = "none";

  // Show loading state
  setButtonLoading(generateBtn, true);

  try {
    const response = await fetch(CONFIG.IMAGE_PROXY_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ description }),
    });

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        showError("image-error", "Session expired. Please login again.");
        setTimeout(() => logout(), 2000);
        return;
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.error || `HTTP error! status: ${response.status}`
      );
    }

    const data = await response.json();

    // Display result
    generatedImage.src = data.image_url;
    generatedImage.alt = description;
    resultBox.style.display = "block";
  } catch (error) {
    console.error("Error:", error);
    showError("image-error", `Failed to generate image: ${error.message}`);
  } finally {
    setButtonLoading(generateBtn, false);
  }
}

// ============================================
// Image Download
// ============================================
async function handleDownloadImage() {
  const generatedImage = document.getElementById("generated-image");
  const imageUrl = generatedImage.src;

  if (!imageUrl) {
    showError("image-error", "No image to download");
    return;
  }

  try {
    // Fetch the image as a blob
    const response = await fetch(imageUrl);
    const blob = await response.blob();

    // Create a temporary URL and download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bedrock-generated-${Date.now()}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    showNotification("Image downloaded successfully! 💾");
  } catch (error) {
    console.error("Error downloading image:", error);
    showError(
      "image-error",
      "Failed to download image. You can right-click and save instead."
    );
  }
}

// ============================================
// Utility Functions
// ============================================
function showError(elementId, message) {
  const errorBox = document.getElementById(elementId);
  errorBox.textContent = message;
  errorBox.style.display = "block";

  // Auto-hide after 5 seconds
  setTimeout(() => {
    errorBox.style.display = "none";
  }, 5000);
}

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

function copyToClipboard(text) {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      showNotification("Copied to clipboard! 📋");
    })
    .catch((err) => {
      console.error("Failed to copy:", err);
      showNotification("Failed to copy to clipboard ❌");
    });
}

function showNotification(message) {
  // Create notification element
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

  // Remove after 3 seconds
  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease-out";
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}

// Add notification animations
const style = document.createElement("style");
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
