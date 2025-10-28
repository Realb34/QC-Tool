# QC Tool Web Application - Project Structure

## Complete File Tree

```
QC TOOL WEB BASED/
│
├── 📁 src/                              # Source code root
│   │
│   ├── 📁 backend/                      # Backend API (Python/Flask)
│   │   ├── __init__.py                  # Package initialization
│   │   ├── app.py                       # Application factory & main entry
│   │   ├── config.py                    # Configuration classes
│   │   ├── requirements.txt             # Python dependencies
│   │   ├── .env.example                 # Environment template
│   │   │
│   │   ├── 📁 api/                      # REST API Endpoints
│   │   │   ├── __init__.py              # Export blueprints
│   │   │   ├── auth.py                  # Authentication API
│   │   │   ├── sites.py                 # Site selection API
│   │   │   └── files.py                 # File operations API
│   │   │
│   │   ├── 📁 models/                   # Data Models
│   │   │   ├── __init__.py              # Export models
│   │   │   └── connection.py            # Connection model & enum
│   │   │
│   │   ├── 📁 services/                 # Business Logic Layer
│   │   │   ├── __init__.py              # Export services
│   │   │   ├── connection_service.py    # FTP/SFTP connection management
│   │   │   └── file_service.py          # File operations service
│   │   │
│   │   └── 📁 utils/                    # Utility Functions
│   │       └── logging_config.py        # Logging setup
│   │
│   └── 📁 frontend/                     # Frontend Web Application
│       │
│       ├── 📁 templates/                # Jinja2 HTML Templates
│       │   ├── base.html                # Base template (header/footer)
│       │   ├── login.html               # Login page
│       │   ├── sites.html               # Site selection page
│       │   └── viewer.html              # File viewer page
│       │
│       └── 📁 static/                   # Static Assets
│           │
│           ├── 📁 css/
│           │   └── main.css             # Application styles
│           │
│           ├── 📁 js/
│           │   ├── utils.js             # Utility functions
│           │   ├── api.js               # API client
│           │   ├── login.js             # Login page logic
│           │   ├── sites.js             # Sites page logic
│           │   └── viewer.js            # Viewer page logic
│           │
│           └── 📁 images/               # Images (if any)
│
├── 📄 Dockerfile.new                    # Docker container config
├── 📄 docker-compose.new.yml            # Docker Compose setup
├── 📄 run.sh                            # Development startup script
├── 📄 README_NEW.md                     # Main documentation
├── 📄 PROJECT_STRUCTURE.md              # This file
│
└── 📄 FlightPathViewer.py               # Original script (preserved)
```

## Module Overview

### Backend Modules

#### `app.py` - Application Factory
- Creates and configures Flask app
- Registers blueprints
- Sets up routes for pages
- Error handlers
- Health check endpoint

#### `config.py` - Configuration
- Base configuration class
- Development config
- Production config
- Environment variable loading

#### `api/` - REST API Blueprints

**`auth.py`** - Authentication
- `POST /api/auth/login` - FTP/SFTP login
- `POST /api/auth/logout` - Logout & disconnect
- `GET /api/auth/status` - Check auth status
- `GET /api/auth/validate` - Validate session

**`sites.py`** - Site Management
- `POST /api/sites/list` - List site directories
- `POST /api/sites/select` - Select a site
- `GET /api/sites/current` - Get current site

**`files.py`** - File Operations
- `POST /api/files/browse` - Browse directory
- `POST /api/files/download` - Download file
- `POST /api/files/info` - Get file metadata
- `POST /api/files/preview` - Preview file

#### `models/` - Data Models

**`connection.py`**
- `ConnectionType` enum (SFTP, FTP, FTPS)
- `Connection` class - Represents active server connection
  - Session management
  - Timeout handling
  - Metadata storage

#### `services/` - Business Logic

**`connection_service.py`**
- `ConnectionService` class
  - `connect()` - Establish FTP/SFTP connection
  - `disconnect()` - Close connection
  - `get_connection()` - Get active connection
  - `cleanup_expired()` - Remove expired connections
- Protocol-specific connection methods
- Global connection pool

**`file_service.py`**
- `FileService` class
  - `list_directory()` - List directory contents
  - `download_file()` - Download file to buffer
  - `get_file_info()` - Get file metadata
  - `change_directory()` - Navigate directories
- Protocol-specific implementations (SFTP vs FTP)

#### `utils/` - Utilities

**`logging_config.py`**
- Configure application logging
- File and console handlers
- Log rotation
- Formatting

### Frontend Modules

#### Templates (Jinja2)

**`base.html`**
- Common layout structure
- Header with app title & user info
- Footer
- Toast notification container
- Shared script includes

**`login.html`**
- Server connection form
- Protocol selection (SFTP/FTP/FTPS)
- Server credentials input
- Security notice

**`sites.html`**
- Site directory grid display
- Loading/error/empty states
- Site selection cards

**`viewer.html`**
- File browser sidebar
- Breadcrumb navigation
- File list main area
- File preview area
- Empty state

#### Static Assets

**CSS (`main.css`)**
- CSS variables for theming
- Component styles
- Responsive design
- Animations

**JavaScript**

**`utils.js`** - Utilities
- `showToast()` - Toast notifications
- `formatFileSize()` - Format bytes
- `formatDate()` - Format timestamps
- `getFileIcon()` - File type icons
- `checkAuth()` - Authentication check
- `requireAuth()` - Auth guard
- `logout()` - Logout function

**`api.js`** - API Client
- `API.login()` - Login request
- `API.listSites()` - Get sites
- `API.selectSite()` - Select site
- `API.browseFiles()` - Browse files
- `API.downloadFile()` - Download file
- `API.getFileInfo()` - File metadata
- `API.previewFile()` - File preview

**`login.js`** - Login Page
- Protocol change handler
- Form submission
- Validation
- Loading states
- Auto-redirect if authenticated

**`sites.js`** - Sites Page
- Load sites on mount
- Display site grid
- Site selection handler
- Loading/error states

**`viewer.js`** - Viewer Page
- Load files for selected site
- Breadcrumb navigation
- File/folder click handlers
- Download functionality
- Refresh view

## Data Flow

### 1. Login Flow

```
User Input (login.html)
    ↓
login.js validates and calls API.login()
    ↓
/api/auth/login endpoint (auth.py)
    ↓
connection_service.connect() (connection_service.py)
    ↓
Paramiko/ftplib establishes connection
    ↓
Session created, stored in connection pool
    ↓
Session ID returned to frontend
    ↓
User redirected to /sites
```

### 2. Site Selection Flow

```
Page Load (sites.html)
    ↓
sites.js calls API.listSites()
    ↓
/api/sites/list endpoint (sites.py)
    ↓
file_service.list_directory() (file_service.py)
    ↓
FTP/SFTP LIST command
    ↓
Directory items returned
    ↓
Displayed in site grid
    ↓
User clicks site → API.selectSite()
    ↓
Site stored in session
    ↓
User redirected to /viewer
```

### 3. File Viewing Flow

```
Page Load (viewer.html)
    ↓
viewer.js calls API.browseFiles()
    ↓
/api/files/browse endpoint (files.py)
    ↓
file_service.list_directory() (file_service.py)
    ↓
FTP/SFTP LIST command
    ↓
File list returned and displayed
    ↓
User clicks file → API.downloadFile()
    ↓
/api/files/download endpoint (files.py)
    ↓
file_service.download_file() (file_service.py)
    ↓
FTP/SFTP RETR command
    ↓
File streamed to browser
```

## Session Management

```
Login
  ↓
Session Created
  ├─ session_id (UUID)
  ├─ connection object stored
  ├─ Flask session cookie set
  └─ 4-hour timeout started

Activity
  ↓
Session Updated
  └─ last_activity timestamp refreshed

Timeout (4 hours idle)
  ↓
Session Expired
  ├─ Connection closed
  ├─ Session removed from pool
  └─ User must re-login

Logout
  ↓
Session Destroyed
  ├─ Connection closed
  ├─ Session cleared
  └─ User redirected to login
```

## Key Design Patterns

1. **Application Factory** - `create_app()` in `app.py`
2. **Blueprint Registration** - Modular API endpoints
3. **Service Layer** - Business logic separated from routes
4. **Repository Pattern** - Services handle data access
5. **Singleton Services** - Global instances exported from modules
6. **MVC-like** - Templates (View), API (Controller), Services (Model)

## Dependencies

### Python (Backend)
- Flask - Web framework
- Flask-CORS - CORS handling
- Flask-Session - Server-side sessions
- Paramiko - SFTP client
- Gunicorn - WSGI server

### JavaScript (Frontend)
- Vanilla JS (ES6+)
- Fetch API
- No frameworks/libraries required

## Development Workflow

1. **Backend Changes**:
   - Modify service → Update API → Test endpoint

2. **Frontend Changes**:
   - Modify template → Update JS → Test in browser

3. **New Feature**:
   - Add service method
   - Add API endpoint
   - Update frontend API client
   - Add UI elements
   - Wire up event handlers

## File Naming Conventions

- **Python**: `snake_case.py`
- **JavaScript**: `camelCase.js`
- **HTML**: `lowercase.html`
- **CSS**: `kebab-case.css`
- **Folders**: `lowercase`

## Code Organization Principles

1. **Separation of Concerns** - API, Services, Models separate
2. **Single Responsibility** - Each module has one purpose
3. **DRY** - Shared utilities in `utils.js` and `utils/`
4. **Modularity** - Easy to add/remove features
5. **Testability** - Services can be tested independently

---

This structure provides a clean, maintainable codebase that's easy to understand, extend, and deploy.
