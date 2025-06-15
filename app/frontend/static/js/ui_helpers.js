/**
 * UI Helper functions for application
 */
export const uiHelpers = {
    /**
     * Initialize a form with data and optional validation
     * @param {string} formId - ID of the form element
     * @param {Object} initialData - Initial form data
     * @param {Object} options - Additional options
     */
    initializeForm(formId, initialData = {}, options = {}) {
        const form = document.getElementById(formId);
        if (!form) {
            console.warn(`Form with id ${formId} not found`);
            return;
        }

        // Reset form first
        form.reset();

        // Set initial values
        Object.entries(initialData).forEach(([key, value]) => {
            const input = form.querySelector(`[name="${key}"]`);
            if (!input) return;

            if (input.type === 'checkbox') {
                input.checked = Boolean(value);
            } else if (input.multiple && Array.isArray(value)) {
                Array.from(input.options).forEach(option => {
                    option.selected = value.includes(option.value);
                });
            } else {
                input.value = value ?? '';
            }
        });

        // Set up validation if enabled
        if (options.validate) {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        }
    },

    /**
     * Get form data as object with type conversion
     * @param {string} formId - ID of the form element
     * @param {Object} options - Options for type conversion
     * @returns {Object} Form data as object
     */
    getFormData(formId, options = {}) {
        const form = document.getElementById(formId);
        if (!form) {
            console.warn(`Form with id ${formId} not found`);
            return {};
        }

        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // Handle number inputs
            if (form.querySelector(`[name="${key}"][type="number"]`)) {
                value = value ? Number(value) : null;
            }
            // Handle checkboxes
            else if (form.querySelector(`[name="${key}"][type="checkbox"]`)) {
                value = form.querySelector(`[name="${key}"]`).checked;
            }
            // Handle multiple select
            else if (form.querySelector(`[name="${key}"][multiple]`)) {
                value = Array.from(form.querySelectorAll(`[name="${key}"]`))
                    .filter(opt => opt.selected)
                    .map(opt => opt.value);
            }

            if (value !== null && value !== '') {
                data[key] = value;
            }
        }
        return data;
    },

    /**
     * Show confirmation dialog with improved styling
     * @param {string} message - Confirmation message
     * @param {Object} options - Dialog options
     * @returns {Promise<boolean>} User's choice
     */
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'modal fade';
            dialog.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${options.title || 'Confirm'}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" data-action="confirm">Confirm</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(dialog);
            const modal = new bootstrap.Modal(dialog);

            dialog.querySelector('[data-action="confirm"]').addEventListener('click', () => {
                modal.hide();
                resolve(true);
            });

            dialog.addEventListener('hidden.bs.modal', () => {
                dialog.remove();
                resolve(false);
            });

            modal.show();
        });
    },

    /**
     * Show error message with improved styling
     * @param {Error} error - Error object
     */
    showError(error) {
        console.error(error);
        this.showToast(error.message, 'danger');
    },

    /**
     * Refresh the current page
     * @param {boolean} forceClear - Whether to force clear cache
     */
    refreshPage(forceClear = false) {
        if (forceClear) {
            window.location.reload(true);
        } else {
            window.location.reload();
        }
    },

    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Bootstrap alert type
     * @param {Object} options - Additional options
     */
    showToast(message, type = 'success', options = {}) {
        const toastContainer = document.getElementById('toast-container')
            || this._createToastContainer();

        const toast = document.createElement('div');

        // replace 'error' type with 'danger'
        if (type === 'error') {
            type = 'danger';
        }

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

        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, {
            delay: options.delay || 3000,
            autohide: options.autohide !== false
        });
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    /**
     * Private: Create toast container if it doesn't exist
     * @returns {HTMLElement} Toast container
     */
    _createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    },
    escapeHtml(str) {
        if (typeof str !== 'string') return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },
    navigateTo(path) {
        window.location.href = path;
    }
}; 
