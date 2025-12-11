# iPostal1 Content Auditor

A Streamlit-based content auditing application that validates content against SEO/AEO best practices and brand guidelines for iPostal1.

## Features

- **SEO/AEO Structure Audit**: Validates headings, paragraph length, keyword placement, and content structure
- **Facts & Grammar Checking**: Uses GPT-4 and DSPy to verify claims against a knowledge base
- **Brand Compliance**: Enforces Larry's Rules and overrides for brand-specific terminology
- **Interactive Editing**: Rich text editor with real-time feedback
- **HTML Report Export**: Generate shareable audit reports

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in `requirements.txt`

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-bitbucket-repo-url>
   cd iPostal1_First_Pass
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure secrets**
   - Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   - Add your OpenAI API key and app password:
   ```toml
   OPENAI_API_KEY = "your-openai-api-key"
   APP_PASSWORD = "your-secure-password"
   ```

4. **Run locally**
   ```bash
   streamlit run auditor_app.py
   ```
   Or use the launcher:
   ```bash
   ./Launch_Auditor.command
   ```

## Project Structure

```
iPostal1_First_Pass/
├── auditor_app.py              # Main application
├── ipostal1_knowledge_base.json # Knowledge base (33MB)
├── larry_rules.json            # Brand rule enforcement
├── overrides.json              # Exception rules
├── ipostal1_logo.png           # Brand logo
├── requirements.txt            # Python dependencies
└── .streamlit/
    └── secrets.toml            # API keys (not in git)
```

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended - Free)

**Pros**: Free, easy setup, automatic deployments from Git
**Cons**: Public repos only (or paid Streamlit plan)

1. Push to Bitbucket
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your Bitbucket account
4. Deploy from repository
5. Add secrets in Streamlit dashboard

### Option 2: Cloudflare Pages + Python Workers

**Pros**: Cloudflare infrastructure, custom domains
**Cons**: Requires containerization, more complex setup

Not ideal for Streamlit apps - better for static sites or Next.js

### Option 3: Self-Hosted (Docker + VPS)

**Pros**: Full control, private deployment
**Cons**: Requires server management

Deploy to DigitalOcean, AWS, or company VPS using Docker.

### Option 4: Heroku

**Pros**: Simple deployment, good for Python apps
**Cons**: Paid plans required

## Recommended Deployment: Streamlit Cloud

**Step-by-step:**

1. **Push to Bitbucket** (see instructions below)
2. **Sign up at [share.streamlit.io](https://share.streamlit.io)**
3. **New app** → Select your Bitbucket repo
4. **Add secrets** in Advanced Settings:
   - `OPENAI_API_KEY`
   - `APP_PASSWORD`
5. **Deploy** - your app will be live at `https://<your-app>.streamlit.app`

## Security Notes

- Never commit `secrets.toml` to version control
- The `.gitignore` file is configured to exclude sensitive files
- Rotate API keys if accidentally exposed

## Version History

- v6: Current production version
- v1-v5: Development iterations (excluded from git)

## Support

For questions or issues, contact the development team.
