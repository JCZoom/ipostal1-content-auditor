# Deploy to Streamlit Cloud - Quick Guide

Your code is now on GitHub: https://github.com/JCZoom/ipostal1-content-auditor

## 🚀 Deploy in 3 Minutes

### Step 1: Go to Streamlit Cloud
Visit: https://share.streamlit.io/

### Step 2: Sign in with GitHub
- Click "Sign in with GitHub"
- Authorize Streamlit Cloud

### Step 3: Deploy New App
1. Click **"New app"** button
2. Fill in:
   - **Repository**: `JCZoom/ipostal1-content-auditor`
   - **Branch**: `main`
   - **Main file path**: `auditor_app.py`
3. Click **"Advanced settings"**

### Step 4: Add Secrets
Paste this in the Secrets section:

```toml
OPENAI_API_KEY = "your-openai-api-key-here"
APP_PASSWORD = "your-secure-password-here"
```

### Step 5: Deploy
- Click **"Deploy!"**
- Wait 2-3 minutes for build
- Get your public URL: `https://[app-name].streamlit.app`

---

## 🔐 Login Credentials

Once deployed, access with:
- **Password**: `iPostal2025`

---

## ✅ What's Included

All files are in GitHub:
- ✅ Main application (`auditor_app.py`)
- ✅ Knowledge base (33MB - automatically uploaded)
- ✅ Brand rules and overrides
- ✅ Requirements.txt
- ✅ Logo and assets

---

## 🔄 Future Updates

To update the live app:
```bash
cd /Users/Jeffrey.Coy/Downloads/iPostal1_First_Pass
git add .
git commit -m "Your update message"
git push
```

Streamlit Cloud will auto-redeploy within 1 minute!

---

## 📞 Need Help?

The deployment is fully automated. If you get any errors, check:
1. Secrets are pasted correctly (no extra spaces)
2. Repository access is granted to Streamlit
3. Branch name is exactly `main`
