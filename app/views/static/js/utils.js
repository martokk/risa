/**
 * Utility functions
 */

/**
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * @param {Function} func - Function to debounce
 * @param {number} wait - Milliseconds to wait
 * @returns {Function} Debounced function
 */
export function debounce(func, wait) {
    console.log(`[init] Creating debounced function with ${wait}ms delay`);
    let timeout;
    return function executedFunction(...args) {
        console.log('[debounce] Debouncing function call');
        return new Promise((resolve) => {
            const later = async () => {
                clearTimeout(timeout);
                console.log('[debounce] Executing debounced function');
                const result = await func(...args);
                resolve(result);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        });
    };
}

