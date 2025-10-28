## QC Tool Web Application v2.0

A modern, modular web-based application for viewing and managing drone inspection site files via FTP/SFTP connections.

## 🎯 Overview

This application provides a secure, user-friendly web interface to:
1. **Login** - Connect to your FTP/SFTP server
2. **Browse Sites** - Select from available inspection sites
3. **View Files** - Navigate folders and download files

## ✨ Features

- **Secure Authentication** - SFTP/FTP/FTPS support with encrypted credentials
- **Three-Page Flow** - Login → Site Selection → File Viewer
- **Modern UI** - Clean, responsive interface
- **Modular Architecture** - Separated backend API and frontend
- **Session Management** - Persistent sessions with automatic cleanup
- **File Operations** - Browse directories, preview files, download content

## 🏗️ Architecture

```
QC TOOL WEB BASED/
├── src/
│   ├── backend/                 # Flask API Backend
│   │   ├── api/                # API Blueprints
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── sites.py        # Site selection endpoints
│   │   │   └── files.py        # File operations endpoints
│   │   ├── models/             # Data Models
│   │   │   └── connection.py   # Connection model
│   │   ├── services/           # Business Logic
│   │   │   ├── connection_service.py  # FTP/SFTP management
│   │   │   └── file_service.py        # File operations
│   │   ├── utils/              # Utilities
│   │   │   └── logging_config.py
│   │   ├── app.py              # Application factory
│   │   ├── config.py           # Configuration
│   │   └── requirements.txt    # Python dependencies
│   │
│   └── frontend/               # Web Frontend
│       ├── templates/          # HTML Templates
│       │   ├── base.html       # Base template
│       │   ├── login.html      # Login page
│       │   ├── sites.html      # Site selection page
│       │   └── viewer.html     # File viewer page
│       └── static/             # Static Assets
│           ├── css/
│           │   └── main.css    # Styles
│           └── js/
│               ├── utils.js    # Utility functions
│               ├── api.js      # API client
│               ├── login.js    # Login page logic
│               ├── sites.js    # Sites page logic
│               └── viewer.js   # Viewer page logic
│
├── Dockerfile.new              # Docker configuration
├── docker-compose.new.yml      # Docker Compose setup
├── run.sh                      # Development startup script
└── README_NEW.md              # This file
```

## 🚀 Quick Start

### Option 1: Development Mode (Local)

```bash
# Run the startup script
./run.sh

# Or manually:
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
cd src/backend
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY

# 4. Run application
python app.py

# Access at http://localhost:5000
```

### Option 2: Docker

```bash
# Copy and configure environment
cp src/backend/.env.example src/backend/.env
# Edit .env file

# Build and run
docker-compose -f docker-compose.new.yml up --build

# Access at http://localhost:5000
```

## 📖 User Guide

### 1. Login Page (`/`)

Enter your FTP/SFTP server credentials:
- **Protocol**: Choose SFTP, FTP, or FTPS
- **Server Address**: Your server hostname/IP
- **Port**: Connection port (22 for SFTP, 21 for FTP, 990 for FTPS)
- **Username**: Your username
- **Password**: Your password

Click "Connect to Server" to authenticate.

### 2. Site Selection Page (`/sites`)

- Browse available site directories
- Click on a site card to select it
- Automatically redirects to file viewer

### 3. File Viewer Page (`/viewer`)

- **Sidebar**: Navigate directory tree with breadcrumbs
- **Main Area**: View files and folders
- **Actions**:
  - Click folders to navigate
  - Click files to download
  - Use breadcrumb to jump to parent directories
  - Refresh button to reload current view

## 🔧 Configuration

### Environment Variables

Edit `src/backend/.env`:

```env
# Flask Environment
FLASK_ENV=development          # or 'production'
SECRET_KEY=<generate-this>     # Use secrets.token_hex(32)

# Debug Mode
DEBUG=False                    # True only in development

# Session Security
SESSION_COOKIE_SECURE=False    # True in production with HTTPS

# CORS Origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:5000

# Logging
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR

# Server Port
PORT=5000
```

### Generate SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 📡 API Endpoints

### Authentication

- `POST /api/auth/login` - Login to FTP/SFTP server
- `POST /api/auth/logout` - Logout and close connection
- `GET /api/auth/status` - Check authentication status
- `GET /api/auth/validate` - Validate session

### Sites

- `POST /api/sites/list` - List available sites/directories
- `POST /api/sites/select` - Select a site for viewing
- `GET /api/sites/current` - Get currently selected site

### Files

- `POST /api/files/browse` - Browse directory contents
- `POST /api/files/download` - Download a file
- `POST /api/files/info` - Get file information
- `POST /api/files/preview` - Preview file content

### Health

- `GET /health` - Application health check

## 🔒 Security Features

- **No Client-Side Credentials** - Passwords never stored in browser
- **HTTPS Support** - Secure transmission (configure in production)
- **Session Management** - HTTP-only cookies, automatic expiration
- **Input Validation** - All user input validated and sanitized
- **Rate Limiting** - Protection against brute force (add Flask-Limiter if needed)
- **Secure Defaults** - Sessions expire after 4 hours of inactivity

## 🛠️ Development

### Project Structure

The application follows a modular architecture:

**Backend** (Flask):
- `api/` - REST API endpoints (blueprints)
- `services/` - Business logic layer
- `models/` - Data models
- `utils/` - Helper functions

**Frontend** (Vanilla JS):
- Templates use Jinja2
- JavaScript modules for each page
- Shared utilities and API client

### Adding New Features

1. **New API Endpoint**:
   - Add route in appropriate blueprint (`api/`)
   - Implement logic in service layer (`services/`)
   - Update API client (`frontend/static/js/api.js`)

2. **New Page**:
   - Create template in `frontend/templates/`
   - Add route in `app.py`
   - Create page-specific JS in `frontend/static/js/`

3. **New Service**:
   - Create service class in `services/`
   - Export in `services/__init__.py`
   - Use in API endpoints

## 📦 Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Enable `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Configure `ALLOWED_ORIGINS` with production domain
- [ ] Set up reverse proxy (nginx)
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall
- [ ] Set up logging and monitoring
- [ ] Regular security updates

### Docker Production

```bash
# Build
docker-compose -f docker-compose.new.yml build

# Run in background
docker-compose -f docker-compose.new.yml up -d

# View logs
docker-compose -f docker-compose.new.yml logs -f

# Stop
docker-compose -f docker-compose.new.yml down
```

## 🐛 Troubleshooting

### Connection Issues

**Problem**: Can't connect to FTP server

**Solutions**:
1. Verify credentials are correct
2. Check port number matches protocol
3. Ensure server allows connections from your IP
4. Check firewall settings

### Session Expired

**Problem**: Session expired error

**Solutions**:
1. Sessions expire after 4 hours of inactivity
2. Simply log in again
3. Adjust `PERMANENT_SESSION_LIFETIME` in `config.py`

### Import Errors

**Problem**: Module not found errors

**Solutions**:
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Install dependencies
pip install -r src/backend/requirements.txt

# Set PYTHONPATH
export PYTHONPATH=/path/to/src/backend
```

## 📝 Development Notes

### Key Differences from Original

This version is a complete rewrite with:
- **Modular structure** instead of monolithic script
- **Web-based UI** instead of Tkinter desktop
- **Three-page workflow** for better UX
- **RESTful API** for frontend-backend separation
- **Modern JavaScript** with async/await
- **Responsive CSS** for all devices

### Technologies Used

- **Backend**: Python 3.11+, Flask, Paramiko (SFTP)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Deployment**: Docker, Gunicorn
- **Security**: Flask-Session, HTTPS support

## 🤝 Contributing

To contribute:
1. Follow the modular architecture
2. Add appropriate error handling
3. Update documentation
4. Test all three pages (Login, Sites, Viewer)
5. Ensure backward compatibility

## 📄 License

[Your License Here]

## 🆘 Support

For issues or questions:
1. Check this README
2. Review application logs: `src/backend/logs/app.log`
3. Check browser console for frontend errors
4. Verify environment configuration

---

**Version**: 2.0.0
**Last Updated**: 2024
