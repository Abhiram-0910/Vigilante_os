# 🚀 Deployment Guide for VIBHISHAN

This guide details how to deploy **VIBHISHAN** to a cloud environment (Render, Railway, or Heroku) for the National Cyber Hackathon.

## 📋 Prerequisites
- GitHub Repository (public or private)
- Account on [Render](https://render.com) or [Railway](https://railway.app)
- API Keys:
  - `GROQ_API_KEY` (Primary LLM)
  - `GEMINI_API_KEY` (Fallback LLM)
  - `VIBHISHAN_API_KEY` (Your secure access key)

## ☁️ Option 1: Deploy to Render (Recommended)

1. **New Web Service**:
   - Connect your GitHub repository.
   - **Name**: `vigilante-os`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**:
   Add the following under "Environment":
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `PYTHON_VERSION` | `3.11.10` | (Or use runtime.txt) |
   | `VIBHISHAN_API_KEY` | `gov_secure_access_2026` | Security Key |
   | `GROQ_API_KEY` | `gsk_...` | Required for fast responses |
   | `GEMINI_API_KEY` | `AIza...` | Required for fallback |
   | `ENVIRONMENT` | `production` | Enables prod safeguards |

3. **Verify Deployment**:
   - Wait for the build to finish.
   - Visit `https://<your-app>.onrender.com/health`.
   - You should see `{"status": "ready", ...}`.

## 🚂 Option 2: Deploy to Railway

1. **New Project** → **Deploy from GitHub repo**.
2. Railway automatically detects `Procfile`.
3. Go to **Variables** and add the API Keys listed above.
4. Go to **Settings** → **Generate Domain** to get your public URL.

## 🛠️ Configuration Files

- **`Procfile`**: Defines the start command (`web: uvicorn ...`).
- **`requirements.txt`**: Python dependencies.
- **`runtime.txt`**: Python version (3.11.10).

## 🚨 Troubleshooting

- **Timeout / Slow Responses**:
  - Ensure `GROQ_API_KEY` is valid. The system falls back to Gemini if Groq fails, which might be slower.
- **Memory Issues**:
  - This app is optimized for 512MB RAM. If you see OOM kills, disable `numpy` heavy operations in `fusion.py` (not currently active).

## 🛡️ Post-Deployment Check
Run the simulation against your live URL:
```bash
export BASE_URL="https://your-app.onrender.com"
python simulate_competition.py
```
