# Deployment Guide

This guide walks you through deploying the iPostal1 Content Auditor to a publicly accessible URL.

## Prerequisites

- [x] Bitbucket account (or GitHub)
- [x] OpenAI API key
- [ ] Choose your hosting platform

---

## Part 1: Push to Bitbucket

### 1. Initialize Git Repository (if not done)

```bash
cd /Users/Jeffrey.Coy/Downloads/iPostal1_First_Pass
git init
git add .
git commit -m "Initial commit: iPostal1 Content Auditor"
```

### 2. Create Bitbucket Repository

1. Go to [bitbucket.org](https://bitbucket.org)
2. Click **Create** → **Repository**
3. Name: `ipostal1-content-auditor`
4. Access: Choose **Private** or **Public**
5. Click **Create repository**

### 3. Push to Bitbucket

```bash
# Replace YOUR_WORKSPACE and YOUR_REPO with your actual values
git remote add origin https://bitbucket.org/YOUR_WORKSPACE/ipostal1-content-auditor.git
git branch -M main
git push -u origin main
```

---

## Part 2: Choose Hosting Platform

### 🌟 Recommended: Streamlit Community Cloud (FREE)

**Best for:** Quick deployment, free tier, no server management

#### Setup Steps:

1. **Go to** [share.streamlit.io](https://share.streamlit.io)

2. **Sign in** with GitHub (you'll need to mirror to GitHub or use GitHub instead of Bitbucket)
   - *Note: Streamlit Cloud directly supports GitHub. For Bitbucket, see Alternative below.*

3. **Click "New app"**

4. **Configure:**
   - Repository: Select your repo
   - Branch: `main`
   - Main file path: `auditor_app.py`

5. **Add Secrets** (Advanced settings):
   ```toml
   OPENAI_API_KEY = "sk-..."
   APP_PASSWORD = "your-password"
   ```

6. **Deploy** - Live in ~5 minutes at `https://your-app-name.streamlit.app`

#### Bitbucket Alternative:
Since Streamlit Cloud requires GitHub, you have two options:
- **Option A**: Mirror your Bitbucket repo to GitHub
- **Option B**: Use a different hosting solution below

---

### Alternative 1: Docker + Cloud Run (Google Cloud)

**Best for:** Company infrastructure, scalable, pay-as-you-go

#### Files Needed:

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "auditor_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Create `.dockerignore`:
```
.git
.streamlit/secrets.toml
__pycache__
*.pyc
auditor_app_v*.py
```

#### Deploy Commands:
```bash
# Build and test locally
docker build -t ipostal-auditor .
docker run -p 8501:8501 -e OPENAI_API_KEY="..." -e APP_PASSWORD="..." ipostal-auditor

# Deploy to Google Cloud Run
gcloud run deploy ipostal-auditor \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY="your-key",APP_PASSWORD="your-password"
```

**Result:** Your own URL like `https://ipostal-auditor-xxx.run.app`

---

### Alternative 2: Railway.app

**Best for:** Simple deployment from Git, free tier available

#### Steps:

1. Go to [railway.app](https://railway.app)
2. **New Project** → **Deploy from Bitbucket**
3. Select your repository
4. Railway auto-detects Python/Streamlit
5. Add environment variables:
   - `OPENAI_API_KEY`
   - `APP_PASSWORD`
6. Deploy - get URL like `https://your-app.up.railway.app`

**Cost:** Free tier includes $5/month credit, then ~$10-20/month

---

### Alternative 3: Company VPS/Server

**Best for:** Full control, existing infrastructure

#### Requirements:
- Ubuntu/Debian server with public IP
- Nginx as reverse proxy
- SSL certificate (Let's Encrypt)

#### Quick Setup:
```bash
# On server
git clone https://bitbucket.org/YOUR_WORKSPACE/ipostal1-content-auditor.git
cd ipostal1-content-auditor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create secrets file
mkdir -p .streamlit
nano .streamlit/secrets.toml  # Add your keys

# Run with nohup or systemd
nohup streamlit run auditor_app.py --server.port=8501 &
```

Configure Nginx to proxy to port 8501.

---

## Part 3: Post-Deployment Setup

### 1. Test the Deployment
- Navigate to your public URL
- Enter password: (use your APP_PASSWORD)
- Upload test content
- Verify audit runs successfully

### 2. Configure Custom Domain (Optional)
- Point your domain DNS to hosting provider
- Add SSL certificate
- Update any hardcoded URLs

### 3. Set Up Monitoring
- Enable error tracking
- Monitor OpenAI API usage
- Set up alerts for downtime

### 4. Share with Team
- Distribute public URL
- Document login credentials (securely)
- Create user guide if needed

---

## Comparison Table

| Platform | Cost | Setup Time | Best For | Bitbucket Support |
|----------|------|------------|----------|-------------------|
| Streamlit Cloud | Free | 10 min | Quick deployments | No (GitHub only) |
| Railway | $5-20/mo | 15 min | Easy Git deploys | Yes ✅ |
| Google Cloud Run | Pay-per-use | 30 min | Scalability | Yes ✅ |
| Company VPS | Variable | 1+ hours | Full control | Yes ✅ |

---

## Troubleshooting

### "Module not found" errors
- Ensure `requirements.txt` includes all dependencies
- Rebuild/redeploy after updating requirements

### "Secrets not found" errors
- Verify environment variables or secrets.toml is configured
- Check exact key names match code

### App is slow
- Knowledge base is 33MB - ensure sufficient memory
- Consider upgrading hosting tier
- Optimize embeddings loading

### OpenAI API errors
- Verify API key is valid and has credits
- Check rate limits
- Monitor usage in OpenAI dashboard

---

## Next Steps

1. ✅ Push code to Bitbucket
2. ⬜ Choose hosting platform
3. ⬜ Deploy application
4. ⬜ Test and verify
5. ⬜ Share with team

## Questions?

Contact your DevOps team or the application maintainer.
