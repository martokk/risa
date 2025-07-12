/**
 * Markdown Editor module for initializing and managing EasyMDE instances
 */

/**
 * Initialize a markdown editor on the given element
 * 
 * @param {HTMLElement|string} element - Element or element ID to initialize editor on
 * @param {Object} options - Additional options to merge with defaults
 * @returns {EasyMDE} The editor instance
 */
export function initMarkdownEditor(element, options = {}) {
    // Handle element as string (ID)
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }

    if (!element) {
        console.error('Element not found for markdown editor');
        return null;
    }

    // Default configuration
    const defaultConfig = {
        element: element,
        spellChecker: true,
        toolbar: [
            'bold', 'italic', 'heading', '|',
            'quote', 'unordered-list', 'ordered-list', '|',
            'spellchecker', '|',
            'fullscreen'
        ],
        status: ['words', 'lines'],
        unorderedListStyle: "-"
    };

    // Merge default config with user options
    const config = { ...defaultConfig, ...options };

    // Initialize EasyMDE with configuration
    return new EasyMDE(config);
}

/**
 * Get the value from a markdown editor
 * 
 * @param {EasyMDE} editor - The EasyMDE instance
 * @returns {string} The editor content
 */
export function getMarkdownValue(editor) {
    if (!editor) {
        console.error('Editor instance is null or undefined');
        return '';
    }
    return editor.value();
}

/**
 * Set the value of a markdown editor
 * 
 * @param {EasyMDE} editor - The EasyMDE instance
 * @param {string} value - The content to set
 */
export function setMarkdownValue(editor, value) {
    if (!editor) {
        console.error('Editor instance is null or undefined');
        return;
    }
    editor.value(value);
} 
