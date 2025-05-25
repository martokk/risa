/**
 * API Configuration and Initialization
 */

// Base API configuration
export const API_CONFIG = {
    baseUrl: '/api/v1',
    tokens: {
        access_token: null,
        refresh_token: null
    },
    retryConfig: {
        maxRetries: 3,
        retryDelay: 1000, // ms
        retryableStatuses: [408, 429, 500, 502, 503, 504]
    }
};

/**
 * Initialize the API configuration with tokens
 * @param {Object} tokens - Object containing access_token and refresh_token
 */
export function initializeApi(tokens) {
    console.log('Initializing API with tokens:', tokens);
    API_CONFIG.tokens = tokens;
}

/**
 * Get headers for API requests
 * @param {boolean} includeContent - Whether to include Content-Type header
 * @returns {Object} Headers object
 */
export function getHeaders(includeContent = true) {
    const headers = {
        'Authorization': `Bearer ${API_CONFIG.tokens.access_token}`
    };
    if (includeContent) {
        headers['Content-Type'] = 'application/json';
    }
    console.log('Generated headers:', headers);
    return headers;
}

/**
 * Retry logic for failed requests
 * @param {Function} requestFn - Function that makes the request
 * @param {number} retryCount - Current retry count
 * @returns {Promise} - Promise that resolves with the response
 */
export async function retryRequest(requestFn, retryCount = 0) {
    try {
        console.log(`Attempting request, attempt number: ${retryCount + 1}`);
        return await requestFn();
    } catch (error) {
        console.error('Request failed with error:', error);
        // Check if we should retry
        if (
            retryCount < API_CONFIG.retryConfig.maxRetries &&
            (error.status in API_CONFIG.retryConfig.retryableStatuses)
        ) {
            console.log(`Retrying request, attempt number: ${retryCount + 2}`);
            // Wait before retrying
            await new Promise(resolve =>
                setTimeout(resolve, API_CONFIG.retryConfig.retryDelay * Math.pow(2, retryCount))
            );
            // Retry with incremented count
            return retryRequest(requestFn, retryCount + 1);
        }
        throw error;
    }
}

/**
 * Handle API response with improved error handling
 * @param {Response} response - Fetch Response object
 * @param {string} errorMessage - Custom error message
 * @returns {Promise} Resolved with response data or rejected with error
 */
export async function handleResponse(response, errorMessage) {
    if (!response.ok) {
        let error;
        try {
            const errorData = await response.json();
            error = new Error(errorData.detail || errorMessage);
            error.status = response.status;
            error.data = errorData;
            console.error('API response error:', error);
        } catch (e) {
            error = new Error(errorMessage);
            error.status = response.status;
            console.error('Failed to parse error response:', error);
        }
        throw error;
    }
    const responseData = response.status === 204 ? null : await response.json();
    console.log('API response data:', responseData);
    return responseData;
} 
