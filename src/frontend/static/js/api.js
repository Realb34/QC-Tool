/**
 * API client functions
 */

const API = {
    // Authentication
    async login(credentials) {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Login failed');
        }

        return await response.json();
    },

    async logout() {
        const response = await fetch('/api/auth/logout', { method: 'POST' });
        return await response.json();
    },

    async getAuthStatus() {
        const response = await fetch('/api/auth/status');
        return await response.json();
    },

    // Sites
    async listSites(path = '/') {
        const response = await fetch('/api/sites/list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to load sites');
        }

        return await response.json();
    },

    async selectSite(siteName, sitePath) {
        const response = await fetch('/api/sites/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ site_name: siteName, site_path: sitePath })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to select site');
        }

        return await response.json();
    },

    async getCurrentSite() {
        const response = await fetch('/api/sites/current');
        return await response.json();
    },

    // Files
    async browseFiles(path) {
        const response = await fetch('/api/files/browse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to browse files');
        }

        return await response.json();
    },

    async downloadFile(filePath) {
        const response = await fetch('/api/files/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to download file');
        }

        // Get filename from path
        const filename = filePath.split('/').pop();

        // Create blob and download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    },

    async getFileInfo(filePath) {
        const response = await fetch('/api/files/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get file info');
        }

        return await response.json();
    },

    async previewFile(filePath) {
        const response = await fetch('/api/files/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to preview file');
        }

        return response;
    }
};

// Export API
window.API = API;
