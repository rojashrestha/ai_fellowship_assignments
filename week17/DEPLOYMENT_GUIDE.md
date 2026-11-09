# 🚀 Cloud Deployment Guide (Week 17 MLOps Projects)

This repository is fully configured for deployment on free cloud platforms as well as standard container runtimes.

---

## 📦 What Was Prepared for Deployment

1. **Docker Configurations**:
   - [`track_a/Dockerfile`](file:///c:/Users/acer/Desktop/week17/track_a/Dockerfile): Container for the Telco Churn prediction FastAPI service.
   - [`track_b/Dockerfile`](file:///c:/Users/acer/Desktop/week17/track_b/Dockerfile): Container for the Agentic AI Assistant (supports both FastAPI backend & Streamlit UI).
   - `.dockerignore` files to keep image sizes minimal.
2. **Dependencies**:
   - Clean, standard [`track_a/requirements.txt`](file:///c:/Users/acer/Desktop/week17/track_a/requirements.txt) and [`track_b/requirements.txt`](file:///c:/Users/acer/Desktop/week17/track_b/requirements.txt) exported from `uv.lock`.
3. **Infrastructure as Code**:
   - [`render.yaml`](file:///c:/Users/acer/Desktop/week17/render.yaml): Blueprint for 1-click free deployment of Track A API, Track B API, and Track B Streamlit UI on Render.
   - [`.gitignore`](file:///c:/Users/acer/Desktop/week17/.gitignore): Ensures `.venv` and environment secrets are never pushed to GitHub.

---

## 🛠️ Step 1: Push This Code to GitHub

All free cloud providers (Render, Streamlit Cloud, Hugging Face) deploy directly from GitHub repositories.

Run the following commands in PowerShell from the project root (`c:\Users\acer\Desktop\week17`):

```powershell
# 1. Initialize Git repository
git init

# 2. Add files and commit
git add .
git commit -m "feat: setup cloud deployment for Track A and Track B"

# 3. Create a repository on https://github.com/new (e.g. week17-mlops)
# 4. Link and push to GitHub:
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```

---

## 🌐 Method A: Deploy on Render (Recommended — Free Tier)

Render can deploy all 3 services automatically using the provided [`render.yaml`](file:///c:/Users/acer/Desktop/week17/render.yaml) blueprint:

1. Sign up for a free account at [render.com](https://render.com).
2. Go to your **Dashboard** → Click **New +** → Select **Blueprint**.
3. Connect your GitHub repository.
4. Render will detect [`render.yaml`](file:///c:/Users/acer/Desktop/week17/render.yaml) and declare the 3 services:
   - `telco-churn-api` (Track A)
   - `agentic-ai-backend` (Track B API)
   - `agentic-ai-ui` (Track B Streamlit Frontend)
5. Fill in your environment variables for Track B:
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `OPENAI_API_KEY`: *(Optional)* If using OpenAI as fallback.
6. Click **Apply**. Render will automatically build the Docker containers and deploy your live URLs (e.g., `https://agentic-ai-ui.onrender.com`).

---

## 🎈 Method B: Deploy Streamlit UI on Streamlit Community Cloud (100% Free)

If you want the Streamlit UI to run on a dedicated free hosting service that never goes to sleep:

1. Sign up at [share.streamlit.io](https://share.streamlit.io).
2. Click **New app**.
3. Select your GitHub repository.
4. Set:
   - **Main file path**: `track_b/app/ui/streamlit_app.py`
   - **App URL**: Choose a custom subdomain.
5. In **Advanced settings** → **Secrets**, add:
   ```toml
   API_URL = "https://agentic-ai-backend.onrender.com"
   ```
   *(Point this to your deployed Render or Cloud Run backend API)*
6. Click **Deploy**.

---

## 🤗 Method C: Deploy on Hugging Face Spaces (Free)

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Choose **Streamlit** (or **Docker**) as the Space SDK.
3. Push the `track_b` code or connect your GitHub repo.
4. Under Space Settings → **Variables and Secrets**, add your `GEMINI_API_KEY`.
5. Hugging Face will host your app with a public shareable URL.

---

## 💻 Method D: Run Locally with Docker Compose

To test the entire containerized setup locally on your computer before pushing to the cloud:

```powershell
cd track_b

# 1. Create .env with your API keys
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY

# 2. Build and launch services
docker compose up --build
```
- API will be accessible at: `http://localhost:8000/docs`
- UI will be accessible at: `http://localhost:8501`
