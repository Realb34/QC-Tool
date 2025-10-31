/**
 * Utility functions
 */

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Get file icon based on extension
function getFileIcon(filename, isDirectory) {
    if (isDirectory) {
        return `<svg width="24" height="24" viewBox="0 0 16 16" fill="currentColor">
            <path d="M1.5 1.5A.5.5 0 0 1 2 1h4.586a1 1 0 0 1 .707.293l.915.914A.5.5 0 0 0 8.5 2.5H14a.5.5 0 0 1 .5.5v11a.5.5 0 0 1-.5.5H2a.5.5 0 0 1-.5-.5v-12z"/>
        </svg>`;
    }

    const ext = filename.split('.').pop().toLowerCase();

    const iconMap = {
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
        'pdf': '📄',
        'doc': '📝', 'docx': '📝',
        'xls': '📊', 'xlsx': '📊',
        'zip': '📦', 'rar': '📦', '7z': '📦',
        'txt': '📃',
        'mp4': '🎥', 'avi': '🎥', 'mov': '🎥',
        'mp3': '🎵', 'wav': '🎵',
    };

    return iconMap[ext] || '📄';
}

// Check if user is authenticated
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/status', {
            credentials: 'include'  // Required to send session cookie
        });
        const data = await response.json();

        if (data.authenticated) {
            // Update user info display
            const userInfo = document.getElementById('userInfo');
            const userDisplay = document.getElementById('userDisplay');

            if (userInfo && userDisplay) {
                userDisplay.textContent = `${data.username}@${data.host}`;
                userInfo.style.display = 'flex';
            }

            return true;
        } else {
            return false;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        return false;
    }
}

// Logout function
async function logout() {
    if (confirm('Are you sure you want to logout?')) {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'  // Required to send session cookie
            });
            showToast('Logged out successfully', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } catch (error) {
            console.error('Logout failed:', error);
            showToast('Logout failed', 'error');
        }
    }
}

// Redirect to login if not authenticated
async function requireAuth() {
    const isAuthenticated = await checkAuth();
    if (!isAuthenticated) {
        window.location.href = '/';
        return false;
    }
    return true;
}

// Export functions
window.showToast = showToast;
window.formatFileSize = formatFileSize;
window.formatDate = formatDate;
window.getFileIcon = getFileIcon;
window.checkAuth = checkAuth;
window.logout = logout;
window.requireAuth = requireAuth;
