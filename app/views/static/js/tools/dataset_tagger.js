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

    // New: Thumbnail Generation Logic
    const imageGridContainerForThumbs = document.getElementById('image-grid-container');
    const thumbnailProgressArea = document.getElementById('thumbnail-progress-area');
    const thumbnailProgressBar = document.getElementById('thumbnail-progress-bar');
    const thumbnailProgressStatus = document.getElementById('thumbnail-progress-status');

    if (imageGridContainerForThumbs && thumbnailProgressArea && thumbnailProgressBar && thumbnailProgressStatus) {
        const folderPath = imageGridContainerForThumbs.dataset.folderPath || document.body.dataset.folderPath; // Get folder_path
        if (!folderPath) {
            console.error("Thumbnail Generation: folder_path not found in data attributes.");
            return;
        }

        const imagesToGenerateThumbsFor = Array.from(imageGridContainerForThumbs.querySelectorAll('[data-thumbnail-exists="false"]'));

        if (imagesToGenerateThumbsFor.length > 0) {
            thumbnailProgressArea.style.display = 'block';
            let processedCount = 0;
            const totalToProcess = imagesToGenerateThumbsFor.length;
            thumbnailProgressStatus.textContent = `Preparing to generate ${totalToProcess} thumbnail(s)...`;

            async function processNextThumbnail() {
                if (imagesToGenerateThumbsFor.length === 0) {
                    thumbnailProgressStatus.textContent = `All ${totalToProcess} thumbnails processed.`;
                    thumbnailProgressBar.style.width = '100%';
                    thumbnailProgressBar.textContent = '100%';
                    // Hide progress area after a short delay (e.g., 1.5 seconds)
                    setTimeout(() => {
                        if (thumbnailProgressArea) { // Double check it still exists
                            thumbnailProgressArea.style.display = 'none';
                        }
                    }, 1500);
                    return;
                }

                const imageContainer = imagesToGenerateThumbsFor.shift(); // Process one by one
                const originalFilename = imageContainer.dataset.originalFilename;

                thumbnailProgressStatus.textContent = `Generating thumbnail for ${originalFilename} (${processedCount + 1} of ${totalToProcess})...`;

                const formData = new FormData();
                formData.append('folder_path', folderPath);
                formData.append('original_filename', originalFilename);

                try {
                    const response = await fetch('/tools/dataset-tagger/generate-thumbnail', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            // FastAPI typically uses 'X-CSRF-Token' if CSRF protection is enabled for forms
                            // However, if this is a simple POST and CSRF is handled via cookies for session, it might not be needed here.
                            // For now, assuming basic POST works. Add CSRF if required by your setup.
                        }
                    });

                    const result = await response.json();

                    if (response.ok && result.success && result.thumbnail_url) {
                        const newImg = document.createElement('img');
                        newImg.src = result.thumbnail_url;
                        newImg.alt = originalFilename;
                        newImg.classList.add('img-fluid', 'image-grid-item');
                        newImg.dataset.filename = originalFilename; // Crucial for selection logic
                        const filenameNoExt = originalFilename.split('.').slice(0, -1).join('.') || originalFilename;
                        newImg.id = `image-${filenameNoExt}`;
                        newImg.loading = 'lazy';

                        imageContainer.innerHTML = ''; // Clear placeholder
                        imageContainer.appendChild(newImg);
                        imageContainer.dataset.thumbnailExists = 'true'; // Mark as generated
                    } else {
                        console.error(`Failed to generate thumbnail for ${originalFilename}: ${result.message || 'Unknown error'}`);
                        const placeholder = imageContainer.querySelector('.thumbnail-placeholder');
                        if (placeholder) placeholder.innerHTML = `<small class="text-danger">Error</small>`;
                    }
                } catch (error) {
                    console.error(`Error fetching/generating thumbnail for ${originalFilename}:`, error);
                    const placeholder = imageContainer.querySelector('.thumbnail-placeholder');
                    if (placeholder) placeholder.innerHTML = `<small class="text-danger">Network Error</small>`;
                }

                processedCount++;
                const progressPercentage = Math.round((processedCount / totalToProcess) * 100);
                thumbnailProgressBar.style.width = `${progressPercentage}%`;
                thumbnailProgressBar.textContent = `${progressPercentage}%`;

                // Process next image
                // Using a small timeout to allow UI to update and prevent blocking
                setTimeout(processNextThumbnail, 50);
            }

            processNextThumbnail(); // Start the generation chain
        }
    }
}); 
