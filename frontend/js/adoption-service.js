// frontend/js/adoption-service.js
// Handles adoption request submission

class AdoptionService {
    constructor(apiBaseUrl = 'http://localhost:8000/api') {
        this.apiBaseUrl = apiBaseUrl;
    }

    /**
     * Submit adoption form
     * @param {Object} formData - Adoption form data
     * @returns {Promise<Object>} - Response with request ID
     */
    async submitForm(formData) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/adoption-requests`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return {
                success: true,
                requestId: data.request_id || data.id,
                message: 'בקשתך התקבלה בהצלחה!'
            };
        } catch (error) {
            console.error('Error submitting adoption form:', error);
            return {
                success: false,
                message: 'שגיאה בשליחת הבקשה. נסה שוב מאוחר יותר.'
            };
        }
    }

    /**
     * Convert form data to correct format
     * @param {FormData} rawFormData - Raw form data from HTML form
     * @returns {Object} - Formatted adoption request data
     */
    formatFormData(rawFormData) {
        return {
            why_adopt: rawFormData.get('why_adopt'),
            has_kids: rawFormData.get('has_kids') === 'yes',
            kids_age: rawFormData.get('kids_age') || null,
            has_other_pets: rawFormData.get('has_other_pets') === 'yes',
            which_pets: rawFormData.get('which_pets') || null,
            has_yard: rawFormData.get('has_yard') === 'yes',
            has_house: rawFormData.get('has_house') === 'yes',
            requested_level_of_train: rawFormData.get('requested_level_of_train') || null,
            requested_gender: rawFormData.get('requested_gender') || null,
            requested_size: rawFormData.get('requested_size') || null,
            requested_age: rawFormData.get('requested_age') || null,
            requested_level_energy: rawFormData.get('requested_level_energy') || null,
            dog_living_location: rawFormData.get('dog_living_location'),
            primary_care_giver: rawFormData.get('primary_care_giver')
        };
    }

    /**
     * Get a single adoption request
     * @param {string} requestId - Adoption request ID
     * @returns {Promise<Object>} - Adoption request data
     */
    async getRequest(requestId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/adoption-requests/${requestId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching adoption request:', error);
            return null;
        }
    }

    /**
     * Get all adoption requests
     * @returns {Promise<Array>} - Array of adoption requests
     */
    async getAllRequests() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/adoption-requests`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching adoption requests:', error);
            return [];
        }
    }
}

// Create global instance
const adoptionService = new AdoptionService();
