document.addEventListener("DOMContentLoaded", () => {
    const statusTitle = document.getElementById("status-title");
    const statusMessage = document.getElementById("status-message");
    const iconContainer = document.querySelector(".icon-container");

    // Extract asset ID from URL parameters (e.g. ?id=123)
    const urlParams = new URLSearchParams(window.location.search);
    const assetId = urlParams.get('id');

    if (!assetId) {
        showError("Invalid QR Code", "No asset ID found in the URL.");
        return;
    }

    // Start process
    getLocation();

    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    updateAsset(assetId, lat, lng);
                },
                (error) => {
                    console.error(error);
                    let errMsg = "Unable to retrieve your location.";
                    if (error.code === 1) errMsg = "Location access was denied. Please enable permissions.";
                    showError("Location Required", errMsg);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            showError("Unsupported", "Geolocation is not supported by this browser.");
        }
    }

    async function updateAsset(id, lat, lng) {
        statusTitle.textContent = "Updating Asset...";
        statusMessage.textContent = "Connecting to ArcGIS servers to update location.";
        
        try {
            const response = await fetch("/api/update", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    asset_id: id,
                    lat: lat,
                    lng: lng
                })
            });

            const data = await response.json();

            if (response.ok) {
                showSuccess("Update Complete", "Location logged successfully. Redirecting you to the web map...");
                
                // Redirect after short delay so user can see success state
                setTimeout(() => {
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        statusMessage.textContent = "You may now close this window.";
                    }
                }, 2000);
            } else {
                showError("Update Failed", data.detail || "An error occurred while communicating with the server.");
            }
        } catch (error) {
            console.error(error);
            showError("Network Error", "Failed to connect to the server. Please try again.");
        }
    }

    function showSuccess(title, message) {
        statusTitle.textContent = title;
        statusMessage.textContent = message;
        
        // Swap spinner for checkmark
        iconContainer.innerHTML = `
            <svg class="success-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
              <circle class="success-icon__circle" cx="26" cy="26" r="25" fill="none"/>
              <path class="success-icon__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
        `;
    }

    function showError(title, message) {
        statusTitle.textContent = title;
        statusMessage.textContent = message;
        
        // Swap spinner for cross icon
        iconContainer.innerHTML = `
            <svg class="error-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle cx="26" cy="26" r="25" fill="none" stroke-width="2"/>
                <path fill="none" stroke-width="2" stroke-linecap="round" d="M16,16 L36,36 M36,16 L16,36"/>
            </svg>
        `;
    }
});
