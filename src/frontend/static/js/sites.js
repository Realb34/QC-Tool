/**
 * Sites selection page with breadcrumb navigation
 * Allows users to drill down into folders and select specific site
 */

let sitesData = [];
let currentPath = '/';

// Load sites on page load
window.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const authenticated = await requireAuth();
    if (!authenticated) return;

    // Load initial directory
    await loadSites(currentPath);
});

// Load sites from server
async function loadSites(path = '/') {
    const loadingEl = document.getElementById('sitesLoading');
    const errorEl = document.getElementById('sitesError');
    const gridEl = document.getElementById('sitesGrid');
    const emptyEl = document.getElementById('sitesEmpty');

    // Show loading
    loadingEl.style.display = 'flex';
    errorEl.style.display = 'none';
    gridEl.style.display = 'none';
    emptyEl.style.display = 'none';

    try {
        const result = await API.listSites(path);
        sitesData = result.items;
        currentPath = result.path;

        // Update breadcrumb
        updateBreadcrumb(currentPath);

        // Hide loading
        loadingEl.style.display = 'none';

        if (sitesData.length === 0) {
            emptyEl.style.display = 'flex';
        } else {
            displaySites();
            gridEl.style.display = 'grid';
        }

        // Show/hide "Generate QC View" button based on path depth
        updateGenerateButton();

    } catch (error) {
        console.error('Failed to load sites:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'flex';
        document.getElementById('sitesErrorMessage').textContent = error.message;
    }
}

// Update breadcrumb navigation
function updateBreadcrumb(path) {
    const breadcrumbPath = document.getElementById('breadcrumbPath');
    const upButton = document.getElementById('upButton');

    // Split path into parts
    const parts = path.split('/').filter(Boolean);

    // Build breadcrumb HTML
    let breadcrumbHTML = '<span class="breadcrumb-item" onclick="loadSites(\'/\')">/</span>';

    parts.forEach((part, index) => {
        const partPath = '/' + parts.slice(0, index + 1).join('/');
        const isActive = index === parts.length - 1;
        const className = isActive ? 'breadcrumb-item active' : 'breadcrumb-item';

        breadcrumbHTML += `<span class="${className}" onclick="loadSites('${partPath}')">${part}</span>`;
    });

    breadcrumbPath.innerHTML = breadcrumbHTML;

    // Show/hide up button
    upButton.style.display = path === '/' ? 'none' : 'inline-block';
}

// Update "Generate QC View" button visibility
function updateGenerateButton() {
    const generateButton = document.getElementById('generateQCButton');

    // Show button if we're at least 2 levels deep
    // Example: /homes/JasonDunwoody/10001291-08-20-2025-ATT
    const parts = currentPath.split('/').filter(Boolean);

    // Check if path looks like a site folder
    // Should have at least: homes / pilot name / site folder
    const isSiteLevel = parts.length >= 3;

    // Also check if current folder name contains a site ID (8-10 digits)
    const lastPart = parts[parts.length - 1] || '';
    const hasSiteID = /\d{8,10}/.test(lastPart);

    if (isSiteLevel && hasSiteID) {
        generateButton.style.display = 'inline-block';
        generateButton.textContent = `🚀 Generate QC View for ${lastPart}`;
    } else {
        generateButton.style.display = 'none';
    }
}

// Display sites in grid
function displaySites() {
    const gridEl = document.getElementById('sitesGrid');
    gridEl.innerHTML = '';

    // Only show directories
    const directories = sitesData.filter(item => item.type === 'directory');

    // Sort alphabetically
    const sortedSites = directories.sort((a, b) => a.name.localeCompare(b.name));

    sortedSites.forEach(site => {
        const siteCard = createSiteCard(site);
        gridEl.appendChild(siteCard);
    });
}

// Create site card element
function createSiteCard(site) {
    const card = document.createElement('div');
    card.className = 'site-card';
    card.onclick = () => navigateToFolder(site);

    const icon = document.createElement('div');
    icon.className = 'site-icon';
    icon.textContent = '📁';

    const name = document.createElement('div');
    name.className = 'site-name';
    name.textContent = site.name;

    const meta = document.createElement('div');
    meta.className = 'site-meta';

    const metaItems = [];
    if (site.modified) {
        metaItems.push(`Modified: ${formatDate(site.modified)}`);
    }

    // Check if this looks like a site folder (contains site ID)
    if (/\d{8,10}/.test(site.name)) {
        metaItems.push('📍 Site Folder');
    }

    meta.textContent = metaItems.join(' | ') || 'Folder';

    card.appendChild(icon);
    card.appendChild(name);
    card.appendChild(meta);

    return card;
}

// Navigate to folder
async function navigateToFolder(site) {
    const newPath = `${currentPath}/${site.name}`.replace('//', '/');
    await loadSites(newPath);
}

// Navigate up one level
async function navigateUp() {
    if (currentPath === '/') return;

    const parts = currentPath.split('/').filter(Boolean);
    parts.pop(); // Remove last part

    const newPath = parts.length > 0 ? '/' + parts.join('/') : '/';
    await loadSites(newPath);
}

// Generate QC View for current folder
async function generateQCView() {
    try {
        // Extract site name from current path
        const parts = currentPath.split('/').filter(Boolean);
        const siteName = parts[parts.length - 1];

        showToast(`Generating QC View for ${siteName}...`, 'info');

        // Select this site
        await API.selectSite(siteName, currentPath);

        showToast(`Selected ${siteName}`, 'success');

        // Redirect to QC viewer
        setTimeout(() => {
            window.location.href = '/qc-viewer';
        }, 500);

    } catch (error) {
        console.error('Failed to generate QC view:', error);
        showToast(error.message, 'error');
    }
}

// Make functions globally accessible
window.loadSites = loadSites;
window.navigateUp = navigateUp;
window.generateQCView = generateQCView;
