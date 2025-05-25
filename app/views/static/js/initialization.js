// Import all required managers and utilities
import { initializeApi } from './api_utils.js';

export class InitializationManager {
    constructor(config) {
        this.config = config;
        this.managers = {};
    }

    initialize() {
        this._initializeAPI();
        return this.managers;
    }

    _initializeAPI() {
        initializeApi({
            access_token: this.config.tokens.access_token,
            refresh_token: this.config.tokens.refresh_token
        });
    }

} 
