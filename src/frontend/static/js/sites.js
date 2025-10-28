/**
 * Sites selection page logic
 */

let sitesData = [];

// Load sites on page load
window.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const authenticated = await requireAuth();
    if (!authenticated) return;

    // Load sites
    await loadSites();
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

        // Hide loading
        loadingEl.style.display = 'none';

        if (sitesData.length === 0) {
            emptyEl.style.display = 'flex';
        } else {
            displaySites();
            gridEl.style.display = 'grid';
        }

    } catch (error) {
        console.error('Failed to load sites:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'flex';
        document.getElementById('sitesErrorMessage').textContent = error.message;
    }
}

// Display sites in grid
function displaySites() {
    const gridEl = document.getElementById('sitesGrid');
    gridEl.innerHTML = '';

    // Sort sites alphabetically
    const sortedSites = [...sitesData].sort((a, b) => a.name.localeCompare(b.name));

    sortedSites.forEach(site => {
        const siteCard = createSiteCard(site);
        gridEl.appendChild(siteCard);
    });
}

// Create site card element
function createSiteCard(site) {
    const card = document.createElement('div');
    card.className = 'site-card';
    card.onclick = () => selectSite(site);

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
    if (site.size !== undefined) {
        metaItems.push(`Size: ${formatFileSize(site.size)}`);
    }
    meta.textContent = metaItems.join(' | ') || 'Directory';

    card.appendChild(icon);
    card.appendChild(name);
    card.appendChild(meta);

    return card;
}

// Select a site
async function selectSite(site) {
    try {
        showToast(`Selecting ${site.name}...`, 'info');

        // Construct site path
        const sitePath = `/${site.name}`;

        await API.selectSite(site.name, sitePath);

        showToast(`Selected ${site.name}`, 'success');

        // Redirect to viewer
        setTimeout(() => {
            window.location.href = '/viewer';
        }, 500);

    } catch (error) {
        console.error('Failed to select site:', error);
        showToast(error.message, 'error');
    }
}

// Make loadSites globally accessible for retry button
window.loadSites = loadSites;
