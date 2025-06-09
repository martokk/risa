import { apiCrud } from '/static/js/api_utils.js';
import { uiHelpers } from '/static/js/ui_helpers.js';

class InlineEditor {
    constructor({ containerSelector, entityType, entityId }) {
        this.container = document.querySelector(containerSelector);
        this.entityType = entityType;
        this.entityId = entityId;
        this.originalValues = {};

        if (!this.container) {
            console.error(`InlineEditor: Container "${containerSelector}" not found.`);
            return;
        }
        this.addEventListeners();
    }

    addEventListeners() {
        this.container.addEventListener('click', (event) => {
            const target = event.target.closest('[data-editable="true"]');
            if (target) {
                this.makeEditable(target);
            }
        });

        this.container.addEventListener('change', (event) => {
            const target = event.target;
            if (target.type === 'checkbox' && target.dataset.field) {
                this.handleCheckboxChange(target);
            }
        });
    }

    async handleCheckboxChange(checkbox) {
        const fieldName = checkbox.dataset.field;
        const newValue = checkbox.checked;

        try {
            const payload = { [fieldName]: newValue };
            await apiCrud.update(this.entityType, this.entityId, payload);
            uiHelpers.showToast(`'${fieldName}' updated successfully.`, 'success');
        } catch (error) {
            checkbox.checked = !newValue;
            const errorMessage = error.message || `Failed to update ${fieldName}.`;
            uiHelpers.showToast(errorMessage, 'error');
            console.error(`Failed to update ${fieldName}:`, error);
        }
    }

    makeEditable(element) {
        if (element.isEditing) {
            return;
        }
        element.isEditing = true;

        const fieldName = element.dataset.field;
        const originalValue = element.textContent.trim();
        this.originalValues[fieldName] = originalValue;

        element.innerHTML = '';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control form-control-sm';
        input.value = originalValue;

        element.appendChild(input);
        input.focus();

        const saveChanges = async () => {
            if (!element.isEditing) return; // Prevent saving if already saved/cancelled

            element.isEditing = false;
            const newValue = input.value.trim();
            element.textContent = newValue || '...'; // Show placeholder for empty value

            if (newValue !== originalValue) {
                try {
                    const payload = { [fieldName]: newValue === '' ? null : newValue };
                    await apiCrud.update(this.entityType, this.entityId, payload);
                    uiHelpers.showToast(`'${fieldName}' updated successfully.`, 'success');
                } catch (error) {
                    element.textContent = this.originalValues[fieldName] || '...';
                    const errorMessage = error.message || `Failed to update ${fieldName}.`;
                    uiHelpers.showToast(errorMessage, 'error');
                    console.error(`Failed to update ${fieldName}:`, error);
                }
            }
        };

        const handleKeyDown = (event) => {
            if (event.key === 'Enter') {
                input.blur();
            } else if (event.key === 'Escape') {
                element.isEditing = false;
                element.textContent = this.originalValues[fieldName] || '...';
                input.removeEventListener('blur', saveChanges);
                input.removeEventListener('keydown', handleKeyDown);
            }
        };

        input.addEventListener('blur', saveChanges, { once: true });
        input.addEventListener('keydown', handleKeyDown);
    }
}

export function initializeInlineEditor(options) {
    return new InlineEditor(options);
} 
