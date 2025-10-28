/**
 * File viewer page logic
 */

let currentPath = '/';
let currentSite = null;
let filesData = [];

// Load viewer on page load
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
    currentPath = currentSite.path;

    // Update header
    document.getElementById('currentPath').textContent = currentSite.name;

    // Load files
    await loadFiles(currentPath);
});

// Load files from current path
async function loadFiles(path) {
    const fileList = document.getElementById('fileList');
    const emptyState = document.getElementById('emptyState');

    // Show loading
    fileList.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading files...</p></div>';
    emptyState.style.display = 'none';

    try {
        const result = await API.browseFiles(path);
        filesData = result.items;
        currentPath = result.path;

        // Update breadcrumb
        updateBreadcrumb(currentPath);

        // Display files
        if (filesData.length === 0) {
            fileList.innerHTML = '';
            emptyState.style.display = 'flex';
        } else {
            displayFiles();
        }

    } catch (error) {
        console.error('Failed to load files:', error);
        showToast(error.message, 'error');
        fileList.innerHTML = `<div class="error-state"><p>${error.message}</p></div>`;
    }
}

// Display files in list
function displayFiles() {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';

    // Sort: directories first, then files
    const sorted = [...filesData].sort((a, b) => {
        if (a.type !== b.type) {
            return a.type === 'directory' ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
    });

    // Add parent directory if not at site root
    if (currentPath !== currentSite.path) {
        const parentItem = createFileItem({
            name: '..',
            type: 'directory',
            size: 0
        }, true);
        fileList.appendChild(parentItem);
    }

    sorted.forEach(file => {
        const fileItem = createFileItem(file);
        fileList.appendChild(fileItem);
    });
}

// Create file item element
function createFileItem(file, isParent = false) {
    const item = document.createElement('div');
    item.className = 'file-item';

    const icon = document.createElement('div');
    icon.className = 'file-icon';
    icon.innerHTML = getFileIcon(file.name, file.type === 'directory');

    const info = document.createElement('div');
    info.className = 'file-info';

    const name = document.createElement('div');
    name.className = 'file-name';
    name.textContent = file.name;

    const meta = document.createElement('div');
    meta.className = 'file-meta';

    if (!isParent) {
        const metaItems = [];
        if (file.type === 'file' && file.size !== undefined) {
            metaItems.push(formatFileSize(file.size));
        }
        if (file.modified) {
            metaItems.push(formatDate(file.modified));
        }
        meta.textContent = metaItems.join(' | ') || (file.type === 'directory' ? 'Folder' : 'File');
    } else {
        meta.textContent = 'Parent Directory';
    }

    info.appendChild(name);
    info.appendChild(meta);

    item.appendChild(icon);
    item.appendChild(info);

    // Click handler
    item.onclick = () => handleFileClick(file, isParent);

    return item;
}

// Handle file/folder click
async function handleFileClick(file, isParent = false) {
    if (file.type === 'directory' || isParent) {
        // Navigate to directory
        let newPath;
        if (isParent) {
            // Go to parent
            newPath = currentPath.substring(0, currentPath.lastIndexOf('/')) || currentSite.path;
        } else {
            // Go to subdirectory
            newPath = `${currentPath}/${file.name}`.replace('//', '/');
        }

        await loadFiles(newPath);
    } else {
        // File clicked - download
        await downloadFile(file);
    }
}

// Download file
async function downloadFile(file) {
    try {
        const filePath = `${currentPath}/${file.name}`.replace('//', '/');
        showToast(`Downloading ${file.name}...`, 'info');

        await API.downloadFile(filePath);

        showToast(`Downloaded ${file.name}`, 'success');
    } catch (error) {
        console.error('Download error:', error);
        showToast(`Failed to download: ${error.message}`, 'error');
    }
}

// Update breadcrumb
function updateBreadcrumb(path) {
    const breadcrumb = document.getElementById('breadcrumb');
    const parts = path.split('/').filter(Boolean);

    breadcrumb.innerHTML = '';

    parts.forEach((part, index) => {
        const item = document.createElement('span');
        item.className = 'breadcrumb-item';
        item.textContent = part;

        if (index < parts.length - 1) {
            item.style.cursor = 'pointer';
            item.style.color = 'var(--primary-color)';

            item.onclick = () => {
                const targetPath = '/' + parts.slice(0, index + 1).join('/');
                loadFiles(targetPath);
            };
        }

        breadcrumb.appendChild(item);
    });
}

// Refresh current view
async function refreshView() {
    await loadFiles(currentPath);
    showToast('Refreshed', 'success');
}

// Back to sites
function backToSites() {
    window.location.href = '/sites';
}

// Export functions
window.refreshView = refreshView;
window.backToSites = backToSites;
