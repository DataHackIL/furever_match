// frontend/js/matching-service.js
// Handles dog matching and scoring

class MatchingService {
    constructor(apiBaseUrl = 'http://localhost:8000/api') {
        this.apiBaseUrl = apiBaseUrl;
    }

    /**
     * Get matching dogs for an adoption request
     * @param {string} adoptionRequestId - Adoption request ID
     * @returns {Promise<Array>} - Array of matching dogs with scores
     */
    async getMatches(adoptionRequestId) {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/matches/${adoptionRequestId}`
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.matches || [];
        } catch (error) {
            console.error('Error fetching matches:', error);
            return [];
        }
    }

    /**
     * Get top N matches
     * @param {string} adoptionRequestId - Adoption request ID
     * @param {number} limit - Number of top matches to return
     * @returns {Promise<Array>} - Top matching dogs
     */
    async getTopMatches(adoptionRequestId, limit = 5) {
        const matches = await this.getMatches(adoptionRequestId);
        return matches.slice(0, limit);
    }

    /**
     * Get detailed match info for a specific dog
     * @param {string} adoptionRequestId - Adoption request ID
     * @param {string} dogId - Dog ID
     * @returns {Promise<Object>} - Detailed match information
     */
    async getMatchDetails(adoptionRequestId, dogId) {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/matches/${adoptionRequestId}/${dogId}`
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching match details:', error);
            return null;
        }
    }

    /**
     * Get all dogs
     * @returns {Promise<Array>} - Array of all dogs
     */
    async getAllDogs() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dogs`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching dogs:', error);
            return [];
        }
    }

    /**
     * Get a single dog
     * @param {string} dogId - Dog ID
     * @returns {Promise<Object>} - Dog data
     */
    async getDog(dogId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dogs/${dogId}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching dog:', error);
            return null;
        }
    }

    /**
     * Get match quality label
     * @param {number} score - Match score (0-100)
     * @returns {string} - Quality label
     */
    getQualityLabel(score) {
        if (score >= 80) return 'Excellent';
        if (score >= 60) return 'Good';
        if (score >= 40) return 'Fair';
        return 'Poor';
    }

    /**
     * Get match quality emoji
     * @param {number} score - Match score (0-100)
     * @returns {string} - Quality emoji
     */
    getQualityEmoji(score) {
        if (score >= 80) return '⭐';
        if (score >= 60) return '✅';
        if (score >= 40) return '⊙';
        return '❌';
    }

    /**
     * Get quality CSS class for styling
     * @param {number} score - Match score (0-100)
     * @returns {string} - CSS class name
     */
    getQualityClass(score) {
        if (score >= 80) return 'excellent';
        if (score >= 60) return 'good';
        if (score >= 40) return 'fair';
        return 'poor';
    }

    /**
     * Format match result for display
     * @param {Object} match - Match data from API
     * @returns {Object} - Formatted match object
     */
    formatMatch(match) {
        return {
            dog_id: match.dog_id,
            dog_name: match.dog_name,
            breed: match.breed,
            size: match.size,
            gender: match.gender,
            age: match.age,
            match_score: parseFloat(match.match_score),
            match_score_display: `${parseFloat(match.match_score).toFixed(1)}%`,
            quality_label: this.getQualityLabel(match.match_score),
            quality_emoji: this.getQualityEmoji(match.match_score),
            quality_class: this.getQualityClass(match.match_score),
            match_details: match.match_details
        };
    }
}

// Create global instance
const matchingService = new MatchingService();
