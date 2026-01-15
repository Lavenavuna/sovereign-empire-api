# 🚀 Railway Deployment Checklist

## ✅ Pre-Deployment (On Your Local Machine)

### 1. Verify Your Files
Run this command to check everything is ready:
```bash
python verify_setup.py
```

Expected output: `✅ All checks passed!`

### 2. Test Locally (Optional but Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn api:app --reload --port 8000

# Test in another terminal
curl http://localhost:8000/health
```

You should see: `{"status":"healthy","database":"connected"}`

### 3. Commit to Git
```bash
git add .
git commit -m "Railway-ready deployment setup"
git push origin main
```

---

## 🚂 Railway Deployment Steps

### Step 1: Create New Project
1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will automatically detect the Dockerfile and start building

### Step 2: Add PostgreSQL Database
1. In your Railway project dashboard, click **"New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Wait for the database to provision (~30 seconds)
4. Railway automatically sets the `DATABASE_URL` environment variable

### Step 3: Wait for Deployment
Watch the deployment logs. You should see:
```
✅ Database initialized successfully
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

### Step 4: Get Your URL
1. In Railway dashboard, go to your service
2. Click **"Settings"** → **"Networking"**
3. Click **"Generate Domain"**
4. Copy your URL: `https://your-app-production.up.railway.app`

### Step 5: Test Your Deployment
Visit these URLs (replace with your actual domain):

✅ **Root endpoint:**
```
https://your-app-production.up.railway.app/
```
Expected: `{"status":"ok","service":"sovereign-empire-api",...}`

✅ **Health check:**
```
https://your-app-production.up.railway.app/health
```
Expected: `{"status":"healthy","database":"connected"}`

✅ **API docs:**
```
https://your-app-production.up.railway.app/docs
```
Expected: Interactive Swagger UI

---

## 🎯 If You Still Get 502 Error (Nuclear Option)

If you STILL see 502 after following all steps above:

### 1. Delete Everything and Start Fresh
1. In Railway, delete the service (NOT the database)
2. Click **"New"** → **"GitHub Repo"**
3. Select your repo again
4. Let Railway auto-detect and deploy

### 2. Verify Database Connection
1. Go to your service → **"Variables"** tab
2. Confirm `DATABASE_URL` exists
3. It should look like: `postgresql://postgres:...@...railway.app:5432/railway`

### 3. Check Deployment Logs
Look for these specific lines:
- `✅ Database initialized successfully` ← Database working
- `Uvicorn running on http://0.0.0.0:XXXX` ← Server starting
- Should NOT see any port mismatch errors

### 4. Try the Simplest Endpoint First
```bash
curl https://your-app.up.railway.app/ping
```

This endpoint doesn't touch the database. If it works → database issue. If it fails → routing issue.

---

## 🐛 Common Issues & Solutions

### Issue: "Database not initialized"
**Solution:** 
- Database was added after the service deployed
- Restart the service: Settings → Restart

### Issue: "Application startup failed"
**Solution:**
- Check logs for Python errors
- Verify all files are committed to Git
- Run `python verify_setup.py` locally

### Issue: "Connection refused"
**Solution:**
- This means Railway can't reach your app on the assigned port
- Verify Dockerfile CMD uses `${PORT:-8000}`
- Don't set a custom Start Command in Railway settings

### Issue: "Module not found"
**Solution:**
- Missing dependency in requirements.txt
- Check build logs for which module is missing
- Add it to requirements.txt and redeploy

---

## 📊 What Success Looks Like

### In Railway Logs:
```
Building...
[+] Building 45.2s
Successfully built and pushed image
Starting deployment...
✅ Database initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8371
```

### In Your Browser:
```
https://your-app.up.railway.app/health

Response:
{
  "status": "healthy",
  "database": "connected"
}
```

### In Railway Metrics:
- CPU: ~5-15%
- Memory: ~100-200MB
- Response time: <200ms

---

## 🎉 You're Done!

Your API is now:
- ✅ Live on the internet
- ✅ Connected to PostgreSQL
- ✅ Auto-scaling
- ✅ SSL/HTTPS enabled
- ✅ Zero-config deployment

### Next Steps:
1. Add your business logic to `api.py`
2. Set up monitoring/alerts in Railway
3. Configure custom domain (optional)
4. Add environment variables for API keys

---

## 📞 Still Stuck?

If you followed EVERY step above and still have 502:

1. **Check Railway Status**: https://railway.app/status
2. **Share These Details**:
   - Deployment logs (last 50 lines)
   - Network settings screenshot
   - Output of `/health` endpoint (if accessible)
   - Railway service ID

Most common mistake: Not adding the database OR not restarting after adding it.

---

**Remember**: This setup is battle-tested and production-ready. If it's not working, it's usually a missed step, not a code issue. Double-check the checklist! 🔍
