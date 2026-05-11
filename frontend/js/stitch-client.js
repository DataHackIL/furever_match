// frontend/js/stitch-client.js
// MongoDB Stitch/Atlas App Services client configuration

// Note: This is a placeholder for Stitch client initialization
// You'll need to replace YOUR_APP_ID with your actual Stitch App ID from MongoDB Atlas

class StitchClient {
    constructor() {
        this.appId = 'YOUR_APP_ID_HERE'; // Replace with your actual Stitch App ID
        this.client = null;
        this.isInitialized = false;
    }

    /**
     * Initialize Stitch client
     * You would normally use: Stitch.initializeAppClient(appId)
     * But we're using a simple fetch API approach instead
     */
    init() {
        console.log('Stitch client initialized (using REST API)');
        this.isInitialized = true;
    }

    /**
     * Call a Stitch function (via HTTP API)
     * @param {string} functionName - Function name
     * @param {Array} args - Function arguments
     * @returns {Promise}
     */
    async callFunction(functionName, args = []) {
        try {
            const response = await fetch(
                `/api/function/${functionName}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(args)
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error calling Stitch function ${functionName}:`, error);
            throw error;
        }
    }

    /**
     * Query MongoDB collection (via REST API)
     * @param {string} database - Database name
     * @param {string} collection - Collection name
     * @param {Object} query - Query filter
     * @returns {Promise}
     */
    async queryCollection(database, collection, query = {}) {
        try {
            const response = await fetch(
                `/api/database/${database}/${collection}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(query)
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error querying ${collection}:`, error);
            throw error;
        }
    }

    /**
     * Insert document into MongoDB
     * @param {string} database - Database name
     * @param {string} collection - Collection name
     * @param {Object} document - Document to insert
     * @returns {Promise}
     */
    async insertDocument(database, collection, document) {
        try {
            const response = await fetch(
                `/api/database/${database}/${collection}/insert`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(document)
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error inserting into ${collection}:`, error);
            throw error;
        }
    }
}

// Create and export global Stitch client instance
const stitchClient = new StitchClient();
stitchClient.init();

window.Stitch = window.Stitch || stitchClient;
