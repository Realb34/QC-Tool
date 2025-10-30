# Render Deployment Guide

## Quick Setup

### Step 1: Configure Render Dashboard

1. Go to your Render dashboard: https://dashboard.render.com/web/srv-d40esh75r7bs73c34ueg

2. Click **Settings** tab

3. Configure the following:

#### Build & Deploy
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python src/backend/app.py`

#### Environment
- **Python Version**: Select Python 3.10

#### Environment Variables
Add these environment variables (click "Add Environment Variable"):

| Key | Value |
|-----|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | Generate a secure key (see below) |
| `PORT` | `10000` (Render default) |

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste as SECRET_KEY value.

#### Health Check
- **Health Check Path**: `/health`

### Step 2: Deploy

Click **Manual Deploy** > **Deploy latest commit**

Or set up auto-deploy:
- Go to **Settings** > **Build & Deploy**
- Enable **Auto-Deploy**: Yes
- **Branch**: `main`

### Step 3: Monitor Deployment

Watch the deployment logs in the Render dashboard. You should see:

```
==> Building...
Collecting Flask==2.3.3
Collecting paramiko==3.3.1
...
Successfully installed Flask-2.3.3 ...

==> Starting...
Starting QC Tool Web Application in production mode
Running on http://0.0.0.0:10000
```

### Step 4: Access Your Application

Once deployed, Render will provide a URL like:
`https://qc-tool-XXXX.onrender.com`

Click the URL in the Render dashboard to access your application.

---

## Configuration Details

### Render-Specific Files

The following files have been added for Render deployment:

1. **render.yaml** - Render service configuration
2. **requirements.txt** (root) - Python dependencies
3. **Procfile** - Process definition
4. **runtime.txt** - Python version specification

### Important Notes

#### Performance Considerations

Render's **Starter plan** has limitations:
- **512 MB RAM** - May limit connection pool to ~20 workers instead of 50
- **0.5 CPU** - Slower performance than dedicated server
- **Spins down after inactivity** - First request after idle will be slow

**Recommended Render Plan for Production:**
- **Standard Plus** ($25/month) or higher
- 2 GB RAM - Supports full 50 worker pool
- 1 CPU - Better performance
- No spin down

#### Worker Adjustment for Starter Plan

If using Starter plan, reduce workers:

Edit `src/backend/services/site_analysis_service.py` line 515:

```python
# For Render Starter (512 MB RAM)
num_workers = min(20, max(8, image_count // 8))

# Original (for 2+ GB RAM)
# num_workers = min(50, max(10, image_count // 5))
```

#### Session Storage

Render uses **ephemeral storage** - sessions are lost on restart.

For persistent sessions, consider:
- Redis (Render add-on)
- PostgreSQL (Render add-on)

To add Redis sessions:

1. Add Redis add-on in Render dashboard
2. Add to requirements.txt:
```
redis==5.0.1
flask-redis==0.4.0
```

3. Update `src/backend/config.py`:
```python
import os

SESSION_TYPE = 'redis'
SESSION_REDIS = os.environ.get('REDIS_URL')
```

---

## Deployment Commands

### Manual Deploy
In Render dashboard: **Manual Deploy** > **Deploy latest commit**

### Auto-Deploy (Recommended)
Automatically deploys when you push to GitHub main branch.

Enable in: **Settings** > **Build & Deploy** > **Auto-Deploy**: Yes

### Rollback
In Render dashboard: **Events** tab > Click on previous deployment > **Rollback**

---

## Monitoring

### View Logs
In Render dashboard: **Logs** tab

Watch for:
```
🚀 Using X parallel workers for MAXIMUM speed
♻️  Reusing X cached connections (saved ~Xs)
📊 Extracted X/X GPS points from folder
Analysis complete: X folders, X images, X GPS points
```

### Health Check
Render automatically checks `/health` endpoint every 30 seconds.

Manually check:
```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{"status":"healthy","version":"2.0.0"}
```

### Performance Metrics
In Render dashboard: **Metrics** tab
- CPU usage
- Memory usage
- Response times

---

## Troubleshooting

### Deployment Fails

**Error: "Requirements installation failed"**

Check requirements.txt exists in root directory:
```bash
git add requirements.txt
git commit -m "Add requirements.txt"
git push origin main
```

**Error: "Module not found"**

Ensure all dependencies in requirements.txt:
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push origin main
```

### Application Crashes

**"Out of memory" errors**

Reduce workers (see above) or upgrade to Standard plan.

**"Connection refused" to SFTP**

Check that Render allows outbound SFTP (port 22). Should work by default.

### Slow Performance

**Site analysis taking 5+ minutes**

Expected on Starter plan (512 MB RAM, 0.5 CPU).

Options:
1. Upgrade to Standard Plus plan ($25/month)
2. Reduce workers (see configuration above)
3. Use dedicated server instead of Render

**First request after idle is slow (1-2 minutes)**

Render Starter spins down after inactivity. Upgrade to Standard+ to prevent.

---

## Cost Optimization

### Starter Plan (Free)
- Good for: Testing, development, low usage
- Limitations: 512 MB RAM, 0.5 CPU, spins down
- Recommended workers: 15-20

### Standard Plan ($7/month)
- Good for: Light production use
- 512 MB RAM, 0.5 CPU, no spin down
- Recommended workers: 15-20

### Standard Plus ($25/month)
- **Recommended for production**
- 2 GB RAM, 1 CPU, no spin down
- Supports full 50 workers
- Better performance

### Pro Plan ($85/month)
- Best performance
- 4 GB RAM, 2 CPU
- Can support 100+ workers if needed

---

## Updating Application

### Method 1: Auto-Deploy (Recommended)

1. Make changes locally
2. Commit and push to GitHub:
```bash
git add -A
git commit -m "Update: description"
git push origin main
```
3. Render automatically deploys

### Method 2: Manual Deploy

1. Push changes to GitHub
2. In Render dashboard: **Manual Deploy** > **Deploy latest commit**

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `FLASK_ENV` | Yes | Environment mode | `production` |
| `SECRET_KEY` | Yes | Session encryption key | Generated 64-char hex |
| `PORT` | No | Port to listen on | `10000` (Render default) |
| `PYTHON_VERSION` | No | Python version | `3.10.0` |

---

## Security Considerations

### HTTPS
Render provides automatic HTTPS with SSL certificate.
Your app will be accessible at: `https://your-app.onrender.com`

### Firewall
Render handles firewall configuration automatically.

### Secret Key
**IMPORTANT:** Generate a secure SECRET_KEY and add to environment variables.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Never commit SECRET_KEY to git!

---

## Support

### Render Support
- Dashboard: https://dashboard.render.com
- Docs: https://render.com/docs
- Status: https://status.render.com

### QC Tool Issues
- GitHub: https://github.com/Realb34/QC-Tool/issues
- Logs: Check Render dashboard > Logs tab

---

## Summary

✅ Add environment variables (FLASK_ENV, SECRET_KEY)
✅ Configure build command: `pip install -r requirements.txt`
✅ Configure start command: `python src/backend/app.py`
✅ Enable auto-deploy from main branch
✅ Monitor logs for successful startup
✅ Test health check: https://your-app.onrender.com/health
✅ Access application: https://your-app.onrender.com

🚀 **Your QC Tool is ready on Render!**
