/**
 * Login page logic
 */

// Update port when protocol changes
document.querySelectorAll('input[name="protocol"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        const defaultPorts = {
            'sftp': 22,
            'ftp': 21,
            'ftps': 990
        };
        document.getElementById('port').value = defaultPorts[e.target.value];
    });
});

// Handle login form submission
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const loginBtn = document.getElementById('loginBtn');
    const btnText = loginBtn.querySelector('.btn-text');
    const btnLoader = loginBtn.querySelector('.btn-loader');

    // Get form data
    const protocol = document.querySelector('input[name="protocol"]:checked').value;
    const host = document.getElementById('host').value.trim();
    const port = parseInt(document.getElementById('port').value);
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    // Validate
    if (!host || !username || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    if (port < 1 || port > 65535) {
        showToast('Invalid port number', 'error');
        return;
    }

    // Show loading state
    loginBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'flex';

    try {
        // Attempt login
        const credentials = { protocol, host, port, username, password };
        const result = await API.login(credentials);

        showToast('Login successful! Redirecting...', 'success');

        // Redirect to sites page
        setTimeout(() => {
            window.location.href = '/sites';
        }, 1000);

    } catch (error) {
        console.error('Login error:', error);
        showToast(error.message, 'error');

        // Reset button
        loginBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Check if already logged in
checkAuth().then(isAuthenticated => {
    if (isAuthenticated) {
        window.location.href = '/sites';
    }
});
