// Configuration for AWS Bedrock Playground
// This file will be populated with your API endpoints after deployment

const CONFIG = {
  // Auth API Endpoint - Update this after deploying your auth stack
  AUTH_API_URL: "https://oa2psn63h1.execute-api.eu-west-3.amazonaws.com/prod",

  // Proxy endpoints (through auth API)
  TEXT_PROXY_URL: "", // Will be set as AUTH_API_URL + "/proxy/text"
  IMAGE_PROXY_URL: "", // Will be set as AUTH_API_URL + "/proxy/image"

  // Local storage keys
  STORAGE_KEYS: {
    AUTH_API_URL: "bedrock_auth_api_url",
    JWT_TOKEN: "bedrock_jwt_token",
    USERNAME: "bedrock_username",
  },
};

// Initialize proxy URLs
function initProxyUrls() {
  CONFIG.TEXT_PROXY_URL = `${CONFIG.AUTH_API_URL}/proxy/text`;
  CONFIG.IMAGE_PROXY_URL = `${CONFIG.AUTH_API_URL}/proxy/image`;
}

// Load configuration from localStorage if available
function loadConfig() {
  const authApiUrl = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_API_URL);

  if (authApiUrl) {
    CONFIG.AUTH_API_URL = authApiUrl;
  }

  initProxyUrls();
}

// Save auth API URL to localStorage
function saveAuthApiUrl(authApiUrl) {
  if (authApiUrl) {
    localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_API_URL, authApiUrl);
    CONFIG.AUTH_API_URL = authApiUrl;
    initProxyUrls();
  }
}

// JWT Token Management
function getJwtToken() {
  return localStorage.getItem(CONFIG.STORAGE_KEYS.JWT_TOKEN);
}

function setJwtToken(token) {
  localStorage.setItem(CONFIG.STORAGE_KEYS.JWT_TOKEN, token);
}

function clearJwtToken() {
  localStorage.removeItem(CONFIG.STORAGE_KEYS.JWT_TOKEN);
  localStorage.removeItem(CONFIG.STORAGE_KEYS.USERNAME);
}

function getUsername() {
  return localStorage.getItem(CONFIG.STORAGE_KEYS.USERNAME);
}

function setUsername(username) {
  localStorage.setItem(CONFIG.STORAGE_KEYS.USERNAME, username);
}

// Check if user is authenticated
function isAuthenticated() {
  const token = getJwtToken();
  if (!token) return false;

  try {
    // Decode JWT to check expiration (basic check without validation)
    const payload = JSON.parse(atob(token.split(".")[1]));
    const expiration = payload.exp * 1000; // Convert to milliseconds
    return Date.now() < expiration;
  } catch (error) {
    console.error("Invalid token:", error);
    return false;
  }
}

// Logout function
function logout() {
  clearJwtToken();
  window.location.href = "login.html";
}

// Initialize configuration on load
loadConfig();
