document.addEventListener('DOMContentLoaded', () => {
    const imageGridContainer = document.getElementById('image-grid-container');
    let selectedImagesInput = document.getElementById('selectedImagesInput'); // Make it `let` so it can be reassigned
    const selectAllButton = document.getElementById('selectAllImagesBtn');

    if (!imageGridContainer) {
        console.error('Dataset Tagger JS: Image grid container (#image-grid-container) not found.');
        return;
    }

    function initializeTagProcessingArea() {
        // Re-query for the input field in case it was swapped by HTMX
        selectedImagesInput = document.getElementById('selectedImagesInput');
        if (!selectedImagesInput) {
            console.error('Dataset Tagger JS: Selected images input (#selectedImagesInput) not found after HTMX swap or on initial load.');
        }
        // Call updateSelectedImagesInput to ensure the hidden field reflects current selections
        // This is important if selections persist visually but the input field was reloaded.
        updateSelectedImagesInput();
    }

    // Initial setup
    initializeTagProcessingArea();

    // Listen for HTMX afterSwap event on the main content area or a more specific parent
    // document.body or a container that holds the HTMX swapped content
    const htmxTargetElement = document.getElementById('tag-processor');
    if (htmxTargetElement) {
        htmxTargetElement.addEventListener('htmx:afterSwap', () => {
            console.log('HTMX afterSwap event triggered on #tag-processor. Re-initializing selectedImagesInput and updating.');
            initializeTagProcessingArea();
            // Re-attach selectAllButton listener if it was part of the swapped content 
            // (though in current setup it is not, it's good practice if it could be)
            // For now, selectAllButton is outside the swap, so its listener should persist.
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

    // Update hidden input field
    function updateSelectedImagesInput() {
        if (!selectedImagesInput) {
            // selectedImagesInput might be null if called before it's found post-swap
            // Try to re-query it one more time as a safeguard, though initializeTagProcessingArea should handle it.
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

    // Select All / Deselect All button functionality
    if (selectAllButton) {
        selectAllButton.addEventListener('click', () => {
            const allImagesInGrid = imageGridContainer.querySelectorAll('img[data-filename]');
            if (allImagesInGrid.length === 0) return;

            let allCurrentlySelected = true;
            if (allImagesInGrid.length > 0) {
                allImagesInGrid.forEach(img => {
                    if (!img.classList.contains('selected-image-outline')) {
                        allCurrentlySelected = false;
                    }
                });
            } else {
                allCurrentlySelected = false;
            }

            if (allCurrentlySelected) {
                allImagesInGrid.forEach(img => img.classList.remove('selected-image-outline'));
                selectAllButton.textContent = 'Select All Images';
            } else {
                allImagesInGrid.forEach(img => img.classList.add('selected-image-outline'));
                selectAllButton.textContent = 'Deselect All Images';
            }
            updateSelectedImagesInput();
        });
    } else {
        console.warn('Dataset Tagger JS: Select All button (#selectAllImagesBtn) not found.');
    }
}); 
