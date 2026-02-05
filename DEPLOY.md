# Deployment (Phase 2 – No localhost/ngrok)

The evaluation system will **not** accept localhost or ngrok. Deploy to a cloud host with a stable URL and SSL.

## Requirements

- **Endpoint**: `https://your-domain.com/analyze` (HTTPS, not `http://IP:8000`)
- **Root**: `GET /` must return the professional landing page (already implemented)
- **PORT**: Render/Railway set `PORT`; the app uses `PORT` when set (see `app/main.py`)

## Recommended platforms

| Platform   | Notes |
|-----------|--------|
| **Render** | Add a Web Service, connect repo, build: `pip install -r requirements.txt`, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set env: `VIBHISHAN_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`. |
| **Railway** | Same: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Railway sets `PORT` automatically. |
| **AWS EC2 / DigitalOcean** | Install Python, run `uvicorn app.main:app --host 0.0.0.0 --port 8000` (or use gunicorn + reverse proxy). Put Nginx/Caddy in front for SSL and use a domain. |

## Warm-up (avoid cold start)

If using serverless or a sleeping dyno, the first request can be slow and fail the judge.

- **Option A**: Run the warm-up script on the same host (cron or background process):
  ```bash
  python scripts/warmup.py https://your-app.onrender.com
  ```
  (Pings `/health` every 2 minutes.)

- **Option B**: Use an external cron (e.g. cron-job.org) to GET your `/health` every 2–5 minutes.

## Checklist

- [ ] Deploy to Render / Railway / EC2 / DO (not ngrok)
- [ ] Use HTTPS and a real domain or platform URL
- [ ] Set `VIBHISHAN_API_KEY` (and LLM keys) in the environment
- [ ] Enable warm-up so the first request is fast
