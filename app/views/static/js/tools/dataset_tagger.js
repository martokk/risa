document.addEventListener('DOMContentLoaded', () => {
    const imageGridContainer = document.getElementById('image-grid-container');
    let selectedImagesInput = document.getElementById('selectedImagesInput'); // Make it `let` so it can be reassigned
    let selectAllButton = document.getElementById('selectAllImagesBtn'); // Make 'let'
    let deselectAllButton = document.getElementById('deselectAllImagesBtn'); // Make 'let'

    if (!imageGridContainer) {
        console.error('Dataset Tagger JS: Image grid container (#image-grid-container) not found.');
        return;
    }

    function updateSelectedImagesInput() {
        if (!selectedImagesInput) {
            selectedImagesInput = document.getElementById('selectedImagesInput');
            if (!selectedImagesInput) {
                console.warn('Dataset Tagger JS: updateSelectedImagesInput called but #selectedImagesInput is still not found.');
                return;
            }
        }
        const selectedImages = [];
        const selectedImageElements = imageGridContainer.querySelectorAll('img.selected-image-outline[data-filename]');
        selectedImageElements.forEach(imgElement => {
            selectedImages.push(imgElement.dataset.filename);
        });
        selectedImagesInput.value = selectedImages.join(',');
        console.log('Selected images input updated:', selectedImagesInput.value);
    }

    function initializeTagProcessingArea() {
        selectedImagesInput = document.getElementById('selectedImagesInput');
        if (!selectedImagesInput) {
            console.error('Dataset Tagger JS: Selected images input (#selectedImagesInput) not found after HTMX swap or on initial load.');
        }
        updateSelectedImagesInput(); // Ensure input is synced
    }

    function initializeSelectButtons() {
        selectAllButton = document.getElementById('selectAllImagesBtn');
        deselectAllButton = document.getElementById('deselectAllImagesBtn');

        if (selectAllButton) {
            selectAllButton.replaceWith(selectAllButton.cloneNode(true)); // Remove old listeners
            selectAllButton = document.getElementById('selectAllImagesBtn'); // Re-fetch after clone
            selectAllButton.addEventListener('click', () => {
                const allImagesInGrid = imageGridContainer.querySelectorAll('img[data-filename]');
                if (allImagesInGrid.length === 0) return;
                allImagesInGrid.forEach(img => img.classList.add('selected-image-outline'));
                updateSelectedImagesInput();
            });
        } else {
            console.warn('Dataset Tagger JS: Select All button (#selectAllImagesBtn) not found during init.');
        }

        if (deselectAllButton) {
            deselectAllButton.replaceWith(deselectAllButton.cloneNode(true)); // Remove old listeners
            deselectAllButton = document.getElementById('deselectAllImagesBtn'); // Re-fetch after clone
            deselectAllButton.addEventListener('click', () => {
                const allImagesInGrid = imageGridContainer.querySelectorAll('img[data-filename]');
                if (allImagesInGrid.length === 0) return;
                allImagesInGrid.forEach(img => img.classList.remove('selected-image-outline'));
                updateSelectedImagesInput();
            });
        } else {
            console.warn('Dataset Tagger JS: Deselect All button (#deselectAllImagesBtn) not found during init.');
        }
    }

    // Initial setup
    initializeTagProcessingArea();
    initializeSelectButtons();

    const htmxTargetElement = document.getElementById('tag-processor');
    if (htmxTargetElement) {
        htmxTargetElement.addEventListener('htmx:afterSwap', () => {
            console.log('HTMX afterSwap event triggered on #tag-processor.');
            initializeTagProcessingArea(); // Re-init the input field reference and sync
            initializeSelectButtons();   // Re-init buttons and attach listeners to new buttons
        });
    }

    // Image click for selection
    imageGridContainer.addEventListener('click', (event) => {
        const clickedElement = event.target;
        if (clickedElement.tagName === 'IMG' && clickedElement.hasAttribute('data-filename') && imageGridContainer.contains(clickedElement)) {
            clickedElement.classList.toggle('selected-image-outline');
            updateSelectedImagesInput();
        }
    });
}); 
