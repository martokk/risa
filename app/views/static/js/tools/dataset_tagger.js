function adjustGridItemLayout() {
    console.log('[adjustGridItemLayout] Called');
    const gridContainer = document.getElementById('image-grid-container');
    const grid = gridContainer ? gridContainer.querySelector('.dynamic-image-grid') : null;
    if (!gridContainer || !grid) {
        console.warn('[adjustGridItemLayout] Grid container or grid not found.');
        return;
    }

    const items = grid.querySelectorAll('.dynamic-image-grid-item');
    const itemCount = items.length;
    if (itemCount === 0) {
        console.log('[adjustGridItemLayout] No items to adjust.');
        return;
    }
    console.log(`[adjustGridItemLayout] Item count: ${itemCount}`);

    const containerWidth = gridContainer.clientWidth;
    const containerHeight = gridContainer.clientHeight;
    console.log(`[adjustGridItemLayout] Container dimensions: width=${containerWidth}px, height=${containerHeight}px`);

    if (containerHeight <= 0 || containerWidth <= 0) {
        console.warn('[adjustGridItemLayout] Container has zero or negative dimensions. Aborting.');
        return;
    }

    const gapStyle = getComputedStyle(grid).gap;
    const gap = parseFloat(gapStyle) || 0.3;
    console.log(`[adjustGridItemLayout] Calculated gap: ${gap}px`);

    const itemAspectRatioWbyH = 2 / 3; // Width divided by Height

    let bestFit = {
        cols: 0,
        rows: 0,
        itemWidth: 0,
        itemHeight: 0,
        maximizedArea: 0
    };
    console.log('[adjustGridItemLayout] Initial bestFit:', JSON.parse(JSON.stringify(bestFit)));

    const maxColsToTest = Math.min(itemCount, 40);
    console.log(`[adjustGridItemLayout] Max columns to test: ${maxColsToTest}`);

    for (let currentCols = 1; currentCols <= maxColsToTest; currentCols++) {
        const currentRows = Math.ceil(itemCount / currentCols);

        let calculatedItemWidth = (containerWidth - (currentCols - 1) * gap) / currentCols;
        let calculatedItemHeight = calculatedItemWidth / itemAspectRatioWbyH;
        // console.log(`[adjustGridItemLayout] Testing ${currentCols} cols, ${currentRows} rows: Initial calc W=${calculatedItemWidth.toFixed(2)}, H=${calculatedItemHeight.toFixed(2)}`);

        let totalPredictedHeight = currentRows * calculatedItemHeight + (currentRows - 1) * gap;

        if (totalPredictedHeight > containerHeight) {
            // console.log(`[adjustGridItemLayout] Overflow for ${currentCols} cols. Initial totalH=${totalPredictedHeight.toFixed(2)}. Shrinking items to fit containerH=${containerHeight}`);
            calculatedItemHeight = (containerHeight - (currentRows - 1) * gap) / currentRows;
            calculatedItemWidth = calculatedItemHeight * itemAspectRatioWbyH;
            // console.log(`[adjustGridItemLayout] Shrunk to: W=${calculatedItemWidth.toFixed(2)}, H=${calculatedItemHeight.toFixed(2)}`);
        }

        if (calculatedItemWidth <= 1 || calculatedItemHeight <= 1) {
            // console.log(`[adjustGridItemLayout] Items too small for ${currentCols} cols. Skipping.`);
            continue;
        }

        const totalPredictedWidth = currentCols * calculatedItemWidth + (currentCols - 1) * gap;
        if (totalPredictedWidth > (containerWidth + 1.5)) { // Increased tolerance slightly
            // console.log(`[adjustGridItemLayout] Width overflow for ${currentCols} cols after height adjust. totalW=${totalPredictedWidth.toFixed(2)}, containerW=${containerWidth}. Skipping.`);
            continue;
        }

        const currentItemArea = calculatedItemWidth * calculatedItemHeight;
        // console.log(`[adjustGridItemLayout] For ${currentCols} cols: Area=${currentItemArea.toFixed(2)}, currentBestArea=${bestFit.maximizedArea.toFixed(2)}`);
        if (currentItemArea > bestFit.maximizedArea) {
            bestFit.cols = currentCols;
            bestFit.rows = currentRows;
            bestFit.itemWidth = calculatedItemWidth;
            bestFit.itemHeight = calculatedItemHeight;
            bestFit.maximizedArea = currentItemArea;
            console.log('[adjustGridItemLayout] Updated bestFit:', JSON.parse(JSON.stringify(bestFit)));
        }
    }

    console.log('[adjustGridItemLayout] Final bestFit calculated:', JSON.parse(JSON.stringify(bestFit)));

    if (bestFit.cols > 0 && bestFit.itemWidth > 1 && bestFit.itemHeight > 1) {
        console.log(`[adjustGridItemLayout] Applying styles: ${bestFit.cols} cols, itemW=${bestFit.itemWidth.toFixed(2)}px, itemH=${bestFit.itemHeight.toFixed(2)}px`);
        grid.style.gridTemplateColumns = `repeat(${bestFit.cols}, ${bestFit.itemWidth.toFixed(2)}px)`;

        items.forEach(item => {
            item.style.width = `${bestFit.itemWidth.toFixed(2)}px`;
            item.style.height = `${bestFit.itemHeight.toFixed(2)}px`;
        });
    } else {
        console.warn('[adjustGridItemLayout] No suitable layout found. Applying fallback styles.');
        const fallbackCols = Math.max(1, Math.floor(Math.sqrt(itemCount)));
        grid.style.gridTemplateColumns = `repeat(${fallbackCols}, 1fr)`;
        items.forEach(item => {
            item.style.width = '';
            item.style.height = '';
        });
    }
    console.log('[adjustGridItemLayout] Finished');
}

// Call it on initial load (after HTMX content is loaded if grid is part of it)
document.addEventListener('DOMContentLoaded', () => {
    console.log('[DOMContentLoaded] Fired. Calling adjustGridItemLayout.');
    // Ensure grid is actually in DOM. For complex pages, a small delay or MutationObserver might be needed
    // if gridContainer is populated dynamically *after* DOMContentLoaded but before images load.
    setTimeout(adjustGridItemLayout, 100); // Small delay to ensure layout is somewhat stable
});

// And on window resize (debounced)
let resizeTimeout;
window.addEventListener('resize', () => {
    // console.log('[resize] Event fired');
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        console.log('[resize] Debounced. Calling adjustGridItemLayout.');
        adjustGridItemLayout();
    }, 250); // Increased debounce delay slightly
});

// If you have specific HTMX events that load/update the grid, listen to them too:
document.body.addEventListener('htmx:afterSwap', function (event) {
    if (event.detail.target.id === 'image-grid-container' || event.detail.target.querySelector('.dynamic-image-grid')) {
        console.log('[htmx:afterSwap] Event fired. Calling adjustGridItemLayout.');
        adjustGridItemLayout();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const imageGridContainer = document.getElementById('image-grid-container');
    let selectedImagesInput = document.getElementById('selectedImagesInput'); // Make it `let` so it can be reassigned
    let selectAllButton = document.getElementById('selectAllImagesBtn'); // Make 'let'
    let deselectAllButton = document.getElementById('deselectAllImagesBtn'); // Make 'let'
    let selectTaggedButton = document.getElementById('selectTaggedBtn'); // Make 'let'

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
        selectTaggedButton = document.getElementById('selectTaggedBtn');

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

        if (selectTaggedButton) {
            selectTaggedButton.replaceWith(selectTaggedButton.cloneNode(true)); // Remove old listeners
            selectTaggedButton = document.getElementById('selectTaggedBtn'); // Re-fetch after clone
            selectTaggedButton.addEventListener('click', () => {
                const currentTagElement = document.getElementById('currentDisplayedTagContent');
                const currentTag = currentTagElement ? currentTagElement.textContent.trim() : null;

                if (!currentTag) {
                    console.warn('Dataset Tagger JS: No current tag displayed to select by.');
                    // Optionally, provide user feedback e.g., a small alert or console message
                    return;
                }

                // It's good practice to also check if the displayed item is actually a tag.
                // This requires knowing the 'initial_item_type' from the HTML. 
                // For now, we assume if currentDisplayedTagContent has text, it's the tag.
                // A more robust way would be to have initial_item_type in a data attribute of a parent element.

                const allImageItems = imageGridContainer.querySelectorAll('.dynamic-image-grid-item[data-tags]');
                if (allImageItems.length === 0) return;

                allImageItems.forEach(item => {
                    const tagsAttribute = item.dataset.tags;
                    const imageTags = tagsAttribute ? tagsAttribute.split(',') : [];
                    const imgElement = item.querySelector('img[data-filename]');

                    if (imgElement && imageTags.includes(currentTag)) {
                        imgElement.classList.add('selected-image-outline');
                    } else if (imgElement) {
                        // Optional: deselect if not tagged with the current tag if that's desired behavior.
                        imgElement.classList.remove('selected-image-outline');
                    }
                });
                updateSelectedImagesInput();
            });
        } else {
            console.warn('Dataset Tagger JS: Select Tagged button (#selectTaggedBtn) not found during init.');
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

    // HTMX event listener for tagsUpdated
    document.body.addEventListener('tagsUpdated', function (event) {
        console.log('[tagsUpdated] Event received:', event.detail);
        // Access the actual array from event.detail.value
        const updates = event.detail && event.detail.value ? event.detail.value : null;

        if (updates && Array.isArray(updates)) {
            updates.forEach(update => {
                if (update.filename && Array.isArray(update.tags)) {
                    const imageItem = imageGridContainer.querySelector(`.dynamic-image-grid-item[data-original-filename="${update.filename}"]`);
                    if (imageItem) {
                        imageItem.dataset.tags = update.tags.join(',');
                        console.log(`[tagsUpdated] Updated data-tags for ${update.filename} to: ${imageItem.dataset.tags}`);
                    } else {
                        console.warn(`[tagsUpdated] Could not find image item for filename: ${update.filename}`);
                    }
                } else {
                    console.warn('[tagsUpdated] Invalid update object received:', update);
                }
            });
        } else {
            console.warn('[tagsUpdated] Event detail.value is not an array or is missing.', event.detail);
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
                            adjustGridItemLayout();
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
                setTimeout(processNextThumbnail, 25);
            }

            processNextThumbnail(); // Start the generation chain
        }
    }
});


