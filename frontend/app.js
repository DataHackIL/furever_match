// frontend/app.js
// Main application entry point

document.addEventListener('DOMContentLoaded', () => {
    console.log('ForeverMatch App Loaded');

    // Initialize UI manager (happens automatically)
    // The uiManager is created in ui-manager.js

    // Show home page by default
    uiManager.showPage('home-page');

    // Check for stored adoption request ID
    const storedRequestId = localStorage.getItem('adoptionRequestId');
    if (storedRequestId) {
        uiManager.currentRequestId = storedRequestId;
    }
});

// Utility function to store adoption request ID
function storeAdoptionRequestId(requestId) {
    localStorage.setItem('adoptionRequestId', requestId);
    uiManager.currentRequestId = requestId;
}

// Utility function to clear stored adoption request ID
function clearAdoptionRequestId() {
    localStorage.removeItem('adoptionRequestId');
    uiManager.currentRequestId = null;
}

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e);
    if (uiManager) {
        uiManager.showError('An unexpected error occurred');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    if (uiManager) {
        uiManager.showError('An error occurred. Please try again.');
    }
});
