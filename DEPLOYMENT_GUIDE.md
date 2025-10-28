# Web Deployment Guide - QC Tool

This guide covers deploying your QC Tool to the web so it's accessible from anywhere.

## 🎯 Deployment Options Overview

| Option | Difficulty | Cost | Best For |
|--------|-----------|------|----------|
| **Render.com** | ⭐ Easy | Free/$7/mo | Quick deployment, free tier |
| **Railway.app** | ⭐ Easy | Free/$5/mo | Simple, modern platform |
| **Heroku** | ⭐⭐ Medium | $5-7/mo | Established platform |
| **DigitalOcean** | ⭐⭐⭐ Advanced | $6/mo | Full control, VPS |
| **AWS/Google Cloud** | ⭐⭐⭐ Advanced | $5-10/mo | Enterprise, scalable |

---

## 🚀 Option 1: Render.com (Recommended for Beginners)

**Pros**: Easiest deployment, free tier available, automatic HTTPS
**Cost**: Free (with limitations) or $7/month

### Step 1: Prepare Your Project

1. **Create a `render.yaml` file** in your project root:

```yaml
services:
  - type: web
    name: qc-tool
    env: python
    region: oregon
    plan: free  # or 'starter' for $7/mo
    buildCommand: pip install -r src/backend/requirements.txt
    startCommand: cd src/backend && gunicorn --bind 0.0.0.0:$PORT app:create_app()
    envVars:
      - key: FLASK_ENV
        value: production
      - key: DEBUG
        value: False
      - key: SESSION_COOKIE_SECURE
        value: True
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_ORIGINS
        value: https://your-app-name.onrender.com
```

2. **Create `.gitignore`** (if not exists):

```
venv/
__pycache__/
*.pyc
.env
.env.local
logs/
flask_session/
*.log
.DS_Store
```

3. **Initialize Git repository**:

```bash
cd "/Users/rileybellin/Desktop/QC TOOL WEB BASED"
git init
git add .
git commit -m "Initial commit - QC Tool Web Application"
```

### Step 2: Push to GitHub

1. Create a new repository on [GitHub.com](https://github.com/new)
2. Push your code:

```bash
git remote add origin https://github.com/YOUR_USERNAME/qc-tool.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Render

1. Go to [Render.com](https://render.com) and sign up
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Render will auto-detect the `render.yaml` and configure everything
5. Click **"Create Web Service"**
6. Wait 5-10 minutes for deployment

### Step 4: Access Your App

Your app will be live at: `https://your-app-name.onrender.com`

**Important Notes**:
- Free tier apps sleep after 15 minutes of inactivity (first request takes ~30 seconds)
- Upgrade to $7/mo for always-on service
- HTTPS is automatically configured

---

## 🚄 Option 2: Railway.app (Modern & Easy)

**Pros**: Modern UI, generous free tier, easy setup
**Cost**: $5/month after free trial

### Step 1: Prepare Project

1. **Create `Procfile`** in project root:

```
web: cd src/backend && gunicorn --bind 0.0.0.0:$PORT app:create_app()
```

2. **Create `railway.json`**:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd src/backend && gunicorn --bind 0.0.0.0:$PORT app:create_app()",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 2: Deploy

1. Push code to GitHub (see Option 1, Step 2)
2. Go to [Railway.app](https://railway.app) and sign up
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your repository
5. Add environment variables in Railway dashboard:
   - `FLASK_ENV=production`
   - `DEBUG=False`
   - `SESSION_COOKIE_SECURE=True`
   - `SECRET_KEY=<generate-random-string>`
   - `ALLOWED_ORIGINS=https://your-app.railway.app`

6. Railway will automatically deploy

### Step 3: Get Your URL

1. Click on your service
2. Go to **"Settings"** → **"Networking"**
3. Click **"Generate Domain"**
4. Your app is live at: `https://your-app.railway.app`

---

## 🐳 Option 3: DigitalOcean (Full Control)

**Pros**: Complete control, predictable pricing, good performance
**Cost**: $6/month for basic droplet

### Step 1: Create Droplet

1. Sign up at [DigitalOcean](https://digitalocean.com)
2. Create a new Droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic $6/month (1GB RAM)
   - **Region**: Choose nearest to users
   - **Authentication**: SSH keys (recommended)

3. Note your droplet's IP address

### Step 2: Connect to Server

```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python, pip, nginx
apt install -y python3 python3-pip python3-venv nginx

# Install Docker (optional but recommended)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install -y docker-compose
```

### Step 4: Deploy Application

**Option A: Using Docker** (Recommended)

```bash
# Clone your repository
cd /var/www
git clone https://github.com/YOUR_USERNAME/qc-tool.git
cd qc-tool

# Create .env file
cp src/backend/.env.example src/backend/.env
nano src/backend/.env  # Edit and set values

# Build and run
docker-compose -f docker-compose.new.yml up -d --build
```

**Option B: Manual Setup**

```bash
# Clone repository
cd /var/www
git clone https://github.com/YOUR_USERNAME/qc-tool.git
cd qc-tool

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r src/backend/requirements.txt

# Configure environment
cp src/backend/.env.example src/backend/.env
nano src/backend/.env  # Edit values

# Create systemd service
nano /etc/systemd/system/qc-tool.service
```

**Service file content:**

```ini
[Unit]
Description=QC Tool Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/qc-tool/src/backend
Environment="PATH=/var/www/qc-tool/venv/bin"
ExecStart=/var/www/qc-tool/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
systemctl daemon-reload
systemctl enable qc-tool
systemctl start qc-tool
```

### Step 5: Configure Nginx

```bash
nano /etc/nginx/sites-available/qc-tool
```

**Nginx configuration:**

```nginx
server {
    listen 80;
    server_name YOUR_DROPLET_IP;  # or your-domain.com

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/qc-tool /etc/nginx/sites-enabled/
nginx -t  # Test configuration
systemctl restart nginx
```

### Step 6: Enable HTTPS (Free SSL)

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate (requires domain name)
certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Step 7: Configure Firewall

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
```

**Access your app at**: `http://YOUR_DROPLET_IP` or `https://your-domain.com`

---

## 📋 Production Checklist

Before going live, ensure:

### Security
- [ ] Set strong `SECRET_KEY` in .env
- [ ] Set `DEBUG=False`
- [ ] Enable `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Configure `ALLOWED_ORIGINS` with your domain
- [ ] Enable HTTPS/SSL certificate
- [ ] Configure firewall (only ports 22, 80, 443)
- [ ] Use environment variables for all secrets

### Configuration
- [ ] Set `FLASK_ENV=production`
- [ ] Configure proper logging
- [ ] Set up log rotation
- [ ] Configure session timeout
- [ ] Set file size limits

### Monitoring
- [ ] Set up application monitoring
- [ ] Configure error alerting
- [ ] Monitor disk space
- [ ] Monitor memory usage
- [ ] Set up uptime monitoring

### Backup
- [ ] Backup strategy in place
- [ ] Test restore procedure
- [ ] Backup environment configuration

---

## 🔐 Environment Variables for Production

Create `src/backend/.env` with these values:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<use-secrets-token-hex-32>
DEBUG=False

# Session Configuration
SESSION_COOKIE_SECURE=True  # Requires HTTPS

# CORS (use your actual domain)
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Logging
LOG_LEVEL=INFO

# Server
PORT=5000
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🌐 Custom Domain Setup

### For Render/Railway/Heroku

1. Buy domain from Namecheap, Google Domains, etc.
2. In domain DNS settings, add CNAME record:
   - **Name**: `@` or `www`
   - **Value**: Your app URL (e.g., `your-app.onrender.com`)
3. In platform dashboard, add custom domain
4. Wait for DNS propagation (5-60 minutes)

### For DigitalOcean/VPS

1. Buy domain
2. In domain DNS settings, add A record:
   - **Name**: `@`
   - **Value**: Your droplet IP address
3. Add www subdomain (optional):
   - **Name**: `www`
   - **Value**: Your droplet IP address
4. Update Nginx config with your domain
5. Get SSL certificate with Certbot

---

## 🔄 Updating Your Application

### Render/Railway (Automatic)

```bash
# Just push to GitHub
git add .
git commit -m "Update application"
git push

# Platform auto-deploys
```

### DigitalOcean/VPS (Manual)

```bash
# SSH into server
ssh root@YOUR_DROPLET_IP

# Navigate to app directory
cd /var/www/qc-tool

# Pull latest changes
git pull

# If using Docker
docker-compose -f docker-compose.new.yml down
docker-compose -f docker-compose.new.yml up -d --build

# If using systemd
systemctl restart qc-tool
```

---

## 💰 Cost Comparison

### Free Tier Options

**Render.com Free**
- Cost: $0
- Limitations: Sleeps after 15 min inactivity, 750 hours/month
- Best for: Testing, low-traffic apps

**Railway.app Trial**
- Cost: $0 (with credit card)
- Limitations: $5 credit/month
- Best for: Testing, development

### Paid Options

**Render.com Starter**: $7/month
- Always on
- Custom domain
- Automatic SSL
- Good performance

**Railway.app**: $5/month
- Usage-based pricing
- Modern platform
- Excellent developer experience

**DigitalOcean Droplet**: $6/month
- Full control
- Predictable pricing
- Scalable
- Requires more setup

**Heroku Basic**: $7/month
- Established platform
- Easy deployment
- Good documentation

---

## 🚨 Troubleshooting

### App won't start

**Check logs:**

Render/Railway: View in dashboard
DigitalOcean: `journalctl -u qc-tool -f`

**Common issues:**
- Missing environment variables
- Wrong Python version
- Dependency conflicts
- Port binding issues

### Can't access app

**Check:**
1. Firewall allows traffic
2. Nginx is running: `systemctl status nginx`
3. App is running: `systemctl status qc-tool`
4. DNS is configured correctly

### SSL errors

**Solutions:**
1. Ensure domain points to server
2. Wait for DNS propagation
3. Re-run Certbot
4. Check Nginx configuration

---

## 📞 Support Resources

### Render.com
- Docs: https://render.com/docs
- Discord: https://render.com/discord

### Railway.app
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

### DigitalOcean
- Docs: https://docs.digitalocean.com
- Community: https://www.digitalocean.com/community

---

## ✅ Recommended Deployment Path

For most users, I recommend this order:

1. **Start with Render.com Free Tier**
   - Test your app live
   - No credit card needed
   - Learn deployment basics

2. **Upgrade to Render Starter ($7/mo)**
   - When you need always-on service
   - Still very easy to manage

3. **Move to DigitalOcean ($6/mo)**
   - When you need full control
   - Better performance per dollar
   - Requires more technical knowledge

---

## 🎉 You're Ready!

Choose your deployment option and follow the steps above. Your QC Tool will be live on the web in under 30 minutes!

**Need help?** Check the troubleshooting section or review platform documentation.
