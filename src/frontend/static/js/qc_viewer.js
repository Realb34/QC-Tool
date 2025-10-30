/**
 * Enhanced QC Viewer with 3D Flight Path Visualization
 * MVP Version - Displays GPS data and folder analysis
 */

let currentSite = null;
let analysisData = null;

// Load QC viewer on page load
window.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const authenticated = await requireAuth();
    if (!authenticated) return;

    // Get current site
    const siteResult = await API.getCurrentSite();
    if (!siteResult.site) {
        showToast('No site selected', 'error');
        setTimeout(() => window.location.href = '/sites', 1500);
        return;
    }

    currentSite = siteResult.site;

    // Show loading state
    showLoadingState();

    // Analyze site and generate visualization
    await analyzeSite();
});

// Show loading state
function showLoadingState() {
    const container = document.getElementById('qcViewerContainer');
    container.innerHTML = `
        <div class="qc-loading-state">
            <div class="spinner-large"></div>
            <h2>Analyzing Site...</h2>
            <p>Extracting GPS data from images and building 3D visualization</p>
            <p class="loading-detail">This may take a few minutes depending on site size</p>
        </div>
    `;
}

// Analyze site
async function analyzeSite() {
    try {
        const response = await fetch('/api/sites/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                site_path: currentSite.path
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Analysis failed');
        }

        analysisData = await response.json();

        // Display results
        displayAnalysisResults();

        showToast('Site analysis complete!', 'success');

    } catch (error) {
        console.error('Analysis error:', error);
        showError(error.message);
    }
}

// Display analysis results
function displayAnalysisResults() {
    const container = document.getElementById('qcViewerContainer');

    const siteInfo = analysisData.site_info;
    const folders = analysisData.folders;
    const visualization = analysisData.visualization_html;

    // Build folder summary
    let folderSummaryHTML = '';
    for (const [folderName, folderData] of Object.entries(folders)) {
        const sizeMB = (folderData.total_size / (1024 * 1024)).toFixed(2);
        const hasImages = folderData.sample_images && folderData.sample_images.length > 0;
        folderSummaryHTML += `
            <div class="folder-summary-card" style="border-left: 4px solid ${folderData.color}">
                <div class="folder-summary-name">${folderName}</div>
                <div class="folder-summary-stats">
                    <span>${folderData.image_count} images</span>
                    <span>${sizeMB} MB</span>
                    <span>${folderData.gps_count} GPS points</span>
                </div>
                ${hasImages ? `<button class="folder-view-images-btn" onclick="showFolderImages('${folderName}')">View Images</button>` : ''}
            </div>
        `;
    }

    container.innerHTML = `
        <div class="qc-viewer-layout">
            <!-- Header -->
            <div class="qc-header">
                <div class="qc-header-left">
                    <button onclick="backToSites()" class="btn btn-small btn-secondary">
                        ← Back to Sites
                    </button>
                </div>
                <div class="qc-header-center">
                    <h1>Site ${siteInfo.site_id}</h1>
                    <p class="qc-pilot-name">Pilot: ${siteInfo.pilot_name}</p>
                </div>
                <div class="qc-header-right">
                    <button onclick="refreshAnalysis()" class="btn btn-small btn-secondary">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                            <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                            <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
                        </svg>
                        Refresh
                    </button>
                </div>
            </div>

            <!-- Stats Summary -->
            <div class="qc-stats-summary">
                <div class="qc-stat-card">
                    <div class="qc-stat-value">${analysisData.total_images}</div>
                    <div class="qc-stat-label">Total Images</div>
                </div>
                <div class="qc-stat-card">
                    <div class="qc-stat-value">${Object.keys(folders).length}</div>
                    <div class="qc-stat-label">Folders</div>
                </div>
                <div class="qc-stat-card">
                    <div class="qc-stat-value">${(analysisData.total_size / (1024 * 1024)).toFixed(1)} MB</div>
                    <div class="qc-stat-label">Total Size</div>
                </div>
                <div class="qc-stat-card">
                    <div class="qc-stat-value">${analysisData.gps_point_count}</div>
                    <div class="qc-stat-label">GPS Points</div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="qc-main-content">
                <!-- Sidebar with Folder List -->
                <aside class="qc-sidebar">
                    <h3>Folders</h3>
                    <div class="folder-summary-list">
                        ${folderSummaryHTML}
                    </div>
                </aside>

                <!-- 3D Visualization -->
                <main class="qc-visualization">
                    <div class="qc-viz-header">
                        <h2>3D Flight Path Visualization</h2>
                        <p>Interactive map showing drone photo locations colored by folder</p>
                    </div>
                    <div class="qc-viz-container" id="plotlyVisualization">
                        <div id="flight-path-plot" style="width:100%;height:800px;"></div>
                    </div>
                </main>
            </div>
        </div>

        <!-- Image Carousel Modal -->
        <div id="imageCarouselModal" class="carousel-modal" style="display:none;">
            <div class="carousel-modal-content">
                <div class="carousel-header">
                    <h2 id="carouselFolderName">Folder Images</h2>
                    <button class="carousel-close-btn" onclick="closeCarousel()">&times;</button>
                </div>
                <div class="carousel-body">
                    <button class="carousel-nav-btn carousel-prev" onclick="carouselPrev()">&#10094;</button>
                    <div class="carousel-image-container">
                        <img id="carouselImage" src="" alt="Image">
                        <div class="carousel-image-info">
                            <span id="carouselImageName"></span>
                            <span id="carouselImageCounter"></span>
                        </div>
                    </div>
                    <button class="carousel-nav-btn carousel-next" onclick="carouselNext()">&#10095;</button>
                </div>
                <div class="carousel-thumbnails" id="carouselThumbnails">
                    <!-- Thumbnails will be inserted here -->
                </div>
            </div>
        </div>
    `;

    // Render Plotly visualization (must be done AFTER DOM insertion)
    renderPlotlyVisualization(visualization);
}

// Render Plotly visualization by extracting and executing the script
function renderPlotlyVisualization(htmlString) {
    setTimeout(() => {
        try {
            console.log('=== PLOTLY RENDER ===');
            console.log('Plotly library loaded:', typeof window.Plotly !== 'undefined');

            if (!window.Plotly) {
                console.error('❌ Plotly library NOT loaded!');
                return;
            }

            const plotDiv = document.getElementById('flight-path-plot');
            if (!plotDiv) {
                console.error('❌ Plot div #flight-path-plot not found!');
                return;
            }

            console.log('✓ Plot div found');

            // Extract the Plotly.newPlot call from the HTML string
            // The HTML from backend contains: Plotly.newPlot("flight-path-plot", [...data...], {...layout...}, {...config...})

            // Method 1: Try to extract and eval the script content
            const scriptMatch = htmlString.match(/Plotly\.newPlot\s*\(\s*"flight-path-plot"\s*,\s*(\[[\s\S]*?\])\s*,\s*(\{[\s\S]*?\})\s*,\s*(\{[\s\S]*?\})\s*\)/);

            if (scriptMatch) {
                console.log('✓ Found Plotly.newPlot call in HTML');

                // Extract data, layout, config
                const dataStr = scriptMatch[1];
                const layoutStr = scriptMatch[2];
                const configStr = scriptMatch[3];

                console.log('  Data string length:', dataStr.length);
                console.log('  Layout string length:', layoutStr.length);

                // Parse JSON safely
                const data = JSON.parse(dataStr);
                const layout = JSON.parse(layoutStr);
                const config = JSON.parse(configStr);

                console.log('✓ Parsed Plotly data:', data.length, 'traces');

                // Render the plot
                window.Plotly.newPlot(plotDiv, data, layout, config);

                console.log('✓ Plotly visualization rendered!');
                console.log('=== END PLOTLY RENDER ===');
            } else {
                console.error('❌ Could not extract Plotly.newPlot call from HTML');
                console.log('HTML preview:', htmlString.substring(0, 500));

                // Fallback: Insert HTML and try to execute script manually
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = htmlString;

                const scripts = tempDiv.getElementsByTagName('script');
                console.log('Found', scripts.length, 'script tags');

                if (scripts.length > 0) {
                    // Execute the script
                    const scriptContent = scripts[scripts.length - 1].textContent;
                    console.log('Executing script, length:', scriptContent.length);
                    eval(scriptContent);
                    console.log('✓ Script executed via eval');
                }
            }

        } catch (e) {
            console.error('❌ Plotly render error:', e);
            console.error('Stack:', e.stack);
        }
    }, 500); // Reduced timeout for faster rendering
}

// Carousel state
let currentCarouselFolder = null;
let currentCarouselIndex = 0;
let currentCarouselImages = [];

// Show folder images in carousel
function showFolderImages(folderName) {
    const folderData = analysisData.folders[folderName];
    if (!folderData || !folderData.sample_images || folderData.sample_images.length === 0) {
        showToast('No images available for this folder', 'warning');
        return;
    }

    currentCarouselFolder = folderName;
    currentCarouselImages = folderData.sample_images;
    currentCarouselIndex = 0;

    const modal = document.getElementById('imageCarouselModal');
    const folderNameEl = document.getElementById('carouselFolderName');

    folderNameEl.textContent = `${folderData.folder_name} - ${currentCarouselImages.length} Sample Images (Total: ${folderData.image_count})`;
    modal.style.display = 'flex';

    // Build file list (no thumbnails - faster)
    buildImageFileList();

    // Show first image
    showCarouselImage(0);
}

// Build thumbnail grid (uses cached thumbnails - instant display!)
function buildImageFileList() {
    const container = document.getElementById('carouselThumbnails');
    container.innerHTML = '';
    container.style.display = 'flex';
    container.style.flexDirection = 'row';
    container.style.gap = '10px';
    container.style.padding = '15px';
    container.style.overflowX = 'auto';
    container.style.overflowY = 'hidden';

    currentCarouselImages.forEach((img, index) => {
        const thumbDiv = document.createElement('div');
        thumbDiv.className = 'carousel-thumbnail';
        thumbDiv.style.cssText = `
            flex-shrink: 0;
            width: 100px;
            height: 80px;
            cursor: pointer;
            border: 3px solid ${index === currentCarouselIndex ? '#2ecc40' : '#3a3a4e'};
            border-radius: 6px;
            overflow: hidden;
            transition: all 0.2s;
            background: #1a1a2e;
        `;

        // Create thumbnail image
        const thumbImg = document.createElement('img');
        thumbImg.style.cssText = 'width:100%;height:100%;object-fit:cover;';

        // Use pre-generated thumbnail (created during analysis) or fallback to on-demand
        if (img.thumbnail) {
            thumbImg.src = `/api/files/thumbnail?file_path=${encodeURIComponent(img.path)}`;
        } else {
            // Fallback: generate on-demand if not pre-cached
            thumbImg.src = `/api/files/thumbnail?file_path=${encodeURIComponent(img.path)}`;
        }
        thumbImg.alt = img.name;

        thumbImg.onerror = function() {
            // If thumbnail fails to load, show placeholder
            this.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="80"><rect fill="%23333" width="100" height="80"/><text x="50%" y="50%" fill="%23f44" text-anchor="middle" font-size="10" dy=".3em">Failed</text></svg>';
        };

        thumbDiv.appendChild(thumbImg);

        // Hover effect
        thumbDiv.onmouseenter = function() {
            if (index !== currentCarouselIndex) {
                this.style.borderColor = '#555';
                this.style.transform = 'scale(1.05)';
            }
        };
        thumbDiv.onmouseleave = function() {
            if (index !== currentCarouselIndex) {
                this.style.borderColor = '#3a3a4e';
                this.style.transform = 'scale(1)';
            }
        };

        // Click to show full image
        thumbDiv.onclick = () => showCarouselImage(index);

        container.appendChild(thumbDiv);
    });
}

// Show specific carousel image
function showCarouselImage(index) {
    if (index < 0 || index >= currentCarouselImages.length) return;

    currentCarouselIndex = index;
    const img = currentCarouselImages[index];

    const imgEl = document.getElementById('carouselImage');
    const nameEl = document.getElementById('carouselImageName');
    const counterEl = document.getElementById('carouselImageCounter');

    // Show loading state
    imgEl.style.opacity = '0.3';
    nameEl.textContent = 'Loading... (This may take 30-60 seconds for large images)';
    counterEl.textContent = `${index + 1} / ${currentCarouselImages.length}`;

    // Use full preview endpoint (slower but works reliably)
    const newImg = new Image();
    newImg.onload = function() {
        imgEl.src = this.src;
        imgEl.style.opacity = '1';
        nameEl.textContent = img.name;
        console.log('Image loaded:', img.name);
    };
    newImg.onerror = function() {
        imgEl.style.opacity = '1';
        imgEl.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect fill="%23333" width="800" height="600"/><text x="50%" y="50%" fill="%23fff" text-anchor="middle" font-size="24" dy=".3em">Failed to load image</text></svg>';
        nameEl.textContent = img.name + ' (Failed to load)';
        console.error('Failed to load image:', img.path);
    };
    newImg.src = `/api/files/preview?file_path=${encodeURIComponent(img.path)}`;

    // Update thumbnail highlighting
    document.querySelectorAll('.carousel-thumbnail').forEach((thumb, i) => {
        if (i === index) {
            thumb.style.borderColor = '#2ecc40';
            thumb.style.transform = 'scale(1.05)';
            thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        } else {
            thumb.style.borderColor = '#3a3a4e';
            thumb.style.transform = 'scale(1)';
        }
    });
}

// Carousel navigation
function carouselPrev() {
    const newIndex = currentCarouselIndex - 1;
    if (newIndex >= 0) {
        showCarouselImage(newIndex);
    }
}

function carouselNext() {
    const newIndex = currentCarouselIndex + 1;
    if (newIndex < currentCarouselImages.length) {
        showCarouselImage(newIndex);
    }
}

// Close carousel
function closeCarousel() {
    const modal = document.getElementById('imageCarouselModal');
    modal.style.display = 'none';
    currentCarouselFolder = null;
    currentCarouselImages = [];
    currentCarouselIndex = 0;
}

// Show error
function showError(message) {
    const container = document.getElementById('qcViewerContainer');
    container.innerHTML = `
        <div class="qc-error-state">
            <svg width="64" height="64" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
            </svg>
            <h2>Analysis Failed</h2>
            <p>${message}</p>
            <button onclick="backToSites()" class="btn btn-primary">Back to Sites</button>
            <button onclick="refreshAnalysis()" class="btn btn-secondary">Try Again</button>
        </div>
    `;
}

// Refresh analysis
async function refreshAnalysis() {
    showLoadingState();
    await analyzeSite();
}

// Back to sites
function backToSites() {
    window.location.href = '/sites';
}

// Export functions
window.backToSites = backToSites;
window.refreshAnalysis = refreshAnalysis;
window.showFolderImages = showFolderImages;
window.closeCarousel = closeCarousel;
window.carouselPrev = carouselPrev;
window.carouselNext = carouselNext;
