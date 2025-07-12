/**
 * API Utilities for CRUD operations
 */

import { API_CONFIG, getHeaders, handleResponse, retryRequest } from './api_config.js';
export { initializeApi } from './api_config.js';
export { uiHelpers } from './ui_helpers.js';

// Request interceptors
const requestInterceptors = [];
const responseInterceptors = [];

/**
 * Add a request interceptor
 * @param {Function} interceptor - Function to process request config
 */
export function addRequestInterceptor(interceptor) {
    requestInterceptors.push(interceptor);
}

/**
 * Add a response interceptor
 * @param {Function} interceptor - Function to process response
 */
export function addResponseInterceptor(interceptor) {
    responseInterceptors.push(interceptor);
}

/**
 * Process request through interceptors
 * @param {Object} config - Request configuration
 * @returns {Object} Processed configuration
 */
async function processRequest(config) {
    let processedConfig = { ...config };
    console.log('Processing request with config:', processedConfig);
    for (const interceptor of requestInterceptors) {
        processedConfig = await interceptor(processedConfig);
    }
    return processedConfig;
}

/**
 * Process response through interceptors
 * @param {Response} response - Fetch response
 * @returns {Response} Processed response
 */
async function processResponse(response) {
    console.log('Processing response:', response);
    let processedResponse = response;
    for (const interceptor of responseInterceptors) {
        processedResponse = await interceptor(processedResponse);
    }
    return processedResponse;
}

// Replace the existing LOADING_SPINNER_HTML constant with:
const LOADING_SPINNER_HTML = `
    <div class="loading-overlay" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.3);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;">
        <div class="loading-spinner" style="
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;">
        </div>
    </div>
`;

// Replace the existing loadingManager with:
const loadingManager = {
    activeRequests: 0,
    overlay: null,

    /**
     * Shows loading indicator
     */
    showLoading() {
        this.activeRequests++;

        if (!this.overlay) {
            const div = document.createElement('div');
            div.innerHTML = LOADING_SPINNER_HTML;
            this.overlay = div.firstElementChild;
            document.body.appendChild(this.overlay);
        }

        this.overlay.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent scrolling while loading
    },

    /**
     * Hides loading indicator
     */
    hideLoading() {
        this.activeRequests = Math.max(0, this.activeRequests - 1);

        if (this.activeRequests === 0 && this.overlay) {
            this.overlay.style.display = 'none';
            document.body.style.overflow = ''; // Restore scrolling
        }
    },

    /**
     * Clears all loading indicators
     */
    clearAll() {
        this.activeRequests = 0;
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
        document.body.style.overflow = '';
    }
};

/**
 * Make an API request with interceptors and retry logic
 * @param {string} url - API endpoint
 * @param {Object} config - Request configuration
 * @returns {Promise} API response
 */
async function makeRequest(url, config) {
    console.log(`Making request to ${url} with config:`, config);
    const processedConfig = await processRequest(config);

    loadingManager.showLoading();

    try {
        const response = await retryRequest(async () => {
            const response = await fetch(url, processedConfig);
            const processedResponse = await processResponse(response);
            return processedResponse;
        });
        return response;
    } finally {
        loadingManager.hideLoading();
    }
}

/**
 * Generic CRUD operations for any entity type
 */
export const apiCrud = {
    /**
     * Create a new entity
     * @param {string} entityType - Type of entity (e.g., 'tags', 'users')
     * @param {Object} data - Entity data to create
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} Created entity
     */
    async create(entityType, data, loadingTarget = null) {
        console.log(`Creating ${entityType} with data:`, data);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${entityType}/`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(data),
            loadingTarget
        });
        return handleResponse(response, `Failed to create ${entityType}`);
    },

    /**
     * Get all entities of a type
     * @param {string} entityType - Type of entity
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} List of entities
     */
    async getAll(entityType, loadingTarget = null) {
        console.log(`Fetching all ${entityType}`);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${entityType}/`, {
            headers: getHeaders(false),
            loadingTarget
        });
        return handleResponse(response, `Failed to fetch ${entityType}`);
    },

    /**
     * Get a single entity by ID
     * @param {string} entityType - Type of entity
     * @param {string|number} id - Entity ID
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} Entity data
     */
    async getById(entityType, id, loadingTarget = null) {
        console.log(`Fetching ${entityType} with ID: ${id}`);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${entityType}/${id}`, {
            headers: getHeaders(false),
            loadingTarget
        });
        return handleResponse(response, `Failed to fetch ${entityType}`);
    },

    /**
     * Get text content from an endpoint
     * @param {string} endpoint - API endpoint
     * @param {HTMLElement} [loadingTarget] - Optional target element
     * @returns {Promise<string>} Text content
     */
    async getText(endpoint, loadingTarget = null) {
        console.log(`Fetching text from ${endpoint}`);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${endpoint}`, {
            headers: getHeaders(false),
            loadingTarget
        });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `Failed to fetch text from ${endpoint}`);
        }
        return response.text();
    },

    /**
     * Post text to api endpoint
     * @param {string} endpoint - API endpoint
     * @param {Object} postData - Data to send to endpoint
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} API response
     */
    async postText(endpoint, postData, loadingTarget = null) {
        console.log(`Posting text to ${endpoint}`);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${endpoint}`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(postData),
            loadingTarget
        });
        return handleResponse(response, `Failed to post text to ${endpoint}`);
    },

    /**
     * Put text to api endpoint
     * @param {string} endpoint - API endpoint
     * @param {Object} postData - Data to send to endpoint
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} API response
     */
    async putText(endpoint, postData, loadingTarget = null) {
        console.log(`Putting text to ${endpoint}`);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${endpoint}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(postData),
            loadingTarget
        });
        return handleResponse(response, `Failed to put text to ${endpoint}`);
    },

    /**
     * Update an entity
     * @param {string} entityType - Type of entity
     * @param {string|number} id - Entity ID
     * @param {Object} data - Updated entity data
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} Updated entity
     */
    async update(entityType, id, data, loadingTarget = null) {
        console.log(`Updating ${entityType} with ID: ${id} and data:`, data);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${entityType}/${id}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(data),
            loadingTarget
        });
        return handleResponse(response, `Failed to update ${entityType}`);
    },

    /**
     * Partially update an entity
     * @param {string} entityType - Type of entity
     * @param {string|number} id - Entity ID
     * @param {Object} data - Partial entity data to update
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} Updated entity
     */
    async patch(entityType, id, data, loadingTarget = null) {
        console.log(`Patching ${entityType} with ID: ${id} and data:`, data);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${entityType}/${id}`, {
            method: 'PATCH',
            headers: getHeaders(),
            body: JSON.stringify(data),
            loadingTarget
        });
        return handleResponse(response, `Failed to patch ${entityType}`);
    },

    /**
     * Delete an entity
     * @param {string} entityType - Type of entity
     * @param {string|number} id - Entity ID
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} Void
     */
    async delete(entityType, id, loadingTarget = null) {
        console.log(`Deleting ${entityType} with ID: ${id}`);
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${entityType}/${id}`, {
            method: 'DELETE',
            headers: getHeaders(false),
            loadingTarget
        });
        return handleResponse(response, `Failed to delete ${entityType}`);
    },

    /**
     * Custom GET request to any endpoint
     * @param {string} endpoint - API endpoint (relative to baseUrl)
     * @param {HTMLElement} [loadingTarget] - Optional target element to attach loading spinner
     * @returns {Promise} API response data
     */
    async getEndpoint(endpoint, loadingTarget = null) {
        const response = await makeRequest(`${API_CONFIG.baseUrl}/${endpoint}`, {
            headers: getHeaders(false),
            loadingTarget
        });
        return handleResponse(response, `Failed to fetch ${endpoint}`);
    }
}; 
