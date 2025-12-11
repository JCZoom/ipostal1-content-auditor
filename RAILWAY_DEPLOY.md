# Deploy to Railway (Private Repo Supported) 🚂

Railway supports **private GitHub repositories** on the free tier, making it perfect for internal work apps.

## 🚀 Deploy in 5 Minutes

### Step 1: Go to Railway
Visit: https://railway.app/new

### Step 2: Sign in with GitHub
- Click **"Login with GitHub"**
- Authorize Railway to access your repositories

### Step 3: Deploy from GitHub
1. Click **"Deploy from GitHub repo"**
2. **Select repository**: `JCZoom/ipostal1-content-auditor` 
   - If you don't see it, click **"Configure GitHub App"** to grant Railway access to this repo
3. Click **"Deploy Now"**

### Step 4: Add Environment Variables
After deployment starts:
1. Click on your new project
2. Go to **Variables** tab
3. Click **"+ New Variable"** and add these two:

   **Variable 1:**
   ```
   Name: OPENAI_API_KEY
   Value: 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
   ```

   **Variable 2:**
   ```
   Name: APP_PASSWORD
   Value: iPostal2025
   ```

### Step 5: Generate Public Domain
1. Go to **Settings** tab
2. Scroll to **Networking** section
3. Click **"Generate Domain"**
4. Your public URL will be: `https://[app-name].up.railway.app`

### Step 6: Wait for Build
- Railway auto-detects Python/Streamlit
- Build takes 2-3 minutes
- Watch the **Deployments** tab for progress

---

## 🎉 Done!

Your app will be live at: `https://[app-name].up.railway.app`
- Login password: `iPostal2025`
- Repository stays **private** ✅
- Auto-deploys on every `git push`

---

## 💰 Pricing

- **Free tier**: $5 credit per month
- Typical usage: $5-15/month for this app
- No credit card required to start

---

## 🔄 Future Updates

Just push to GitHub:
```bash
git add .
git commit -m "Update message"
git push
```
Railway auto-deploys within 2 minutes.

---

## ⚙️ Troubleshooting

**Can't see repository?**
- Go to https://github.com/settings/installations
- Find "Railway"
- Click **Configure**
- Grant access to `ipostal1-content-auditor`

**Build failing?**
- Check that `requirements.txt` is in the root
- Verify environment variables are set correctly

**App not starting?**
- Railway auto-detects the port (8501)
- Check logs in the Deployments tab for errors
