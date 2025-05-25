/**
 * Toast Notification Management
 */
export class ToastManager {
    constructor(options = {}) {
        this.options = {
            containerId: 'toast-container',
            position: 'bottom-0 end-0',
            padding: 'p-3',
            ...options
        };
        this.container = null;
    }

    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Bootstrap alert type (success, danger, warning, info)
     */
    show(message, type = 'success') {
        const container = this._getContainer();
        const toast = this._createToastElement(message, type);

        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
            // Clean up container if empty
            if (container.children.length === 0) {
                container.remove();
                this.container = null;
            }
        });
    }

    /**
     * Create a toast element
     * @private
     */
    _createToastElement(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        return toast;
    }

    /**
     * Get or create toast container
     * @private
     */
    _getContainer() {
        if (this.container) {
            return this.container;
        }

        this.container = document.getElementById(this.options.containerId);
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = this.options.containerId;
            this.container.className = `toast-container position-fixed ${this.options.position} ${this.options.padding}`;
            document.body.appendChild(this.container);
        }

        return this.container;
    }
}

// Create a singleton instance
export const toast = new ToastManager(); 
