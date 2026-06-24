# UPSC Quiz App — Project Context

## What This Is

A full-stack web app that parses UPSC MCQ PDFs, extracts chapter/section-wise questions, and serves interactive quizzes with scoring and answer explanations.

Each new PDF upload replaces the entire database (single-document mode by design).

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, uvicorn |
| Database | MongoDB (Motor async driver) |
| PDF parsing | pdfplumber + regex, LLM validation via Ollama (lazy, per group) |
| Frontend | React 18, Vite, Tailwind CSS, axios |
| Deployment | Docker + docker-compose on AWS EC2 |

## GitHub Repo

- **URL:** https://github.com/sinhanaman2701/upsc-quiz
- **Default branch:** `main`

## Live Deployment

- **Platform:** AWS EC2, t3.small, ap-south-1 (Mumbai)
- **Instance ID:** i-0352115fb6eb3c682
- **Key pair:** `llm-router-chatbot-key.pem` (stored at `~/Downloads/` on dev Mac)
- **Current public IP:** 13.206.94.228 *(not static — changes on every stop/start)*
- **App URL:** http://13.206.94.228

> If the instance was stopped and restarted, get the new IP:
> ```bash
> aws ec2 describe-instances \
>   --instance-ids i-0352115fb6eb3c682 \
>   --query "Reservations[*].Instances[*].PublicIpAddress" \
>   --region ap-south-1 --output text
> ```

## Local Development

### Prerequisites

- Python 3.11+ with venv
- Node.js 20+
- MongoDB running on `localhost:27017`
- Ollama running on `localhost:11434` with `gpt-oss:120b-cloud` (optional — LLM validation degrades gracefully without it)

### Start backend

```bash
cd backend
source venv/bin/activate      # or: python3 -m venv venv && pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

### Start frontend

```bash
cd frontend
npm install
npm run dev                   # runs on http://localhost:5173
```

The frontend reads `VITE_API_BASE_URL` to know where the backend is. For local dev it defaults to `http://localhost:8002/api`.

## EC2 — Bring Online After Stop

```bash
# 1. Start the instance
aws ec2 start-instances --instance-ids i-0352115fb6eb3c682 --region ap-south-1

# 2. Get the new public IP
aws ec2 describe-instances \
  --instance-ids i-0352115fb6eb3c682 \
  --query "Reservations[*].Instances[*].PublicIpAddress" \
  --region ap-south-1 --output text

# 3. SSH in
ssh -i ~/Downloads/llm-router-chatbot-key.pem ubuntu@<new-ip>

# 4. Start containers
cd ~/upsc-quiz
sudo docker compose -f docker-compose.ec2.yml up -d

# 5. Verify
curl http://localhost/health
```

Update the IP in this file and in memory once you have it.

## Deployment Workflow

Make changes locally → push to GitHub → pull and rebuild on EC2.

```bash
# --- Local ---
git add <files>
git commit -m "your message"
git push origin main

# --- EC2 ---
ssh -i ~/Downloads/llm-router-chatbot-key.pem ubuntu@<ip>
cd ~/upsc-quiz
git pull origin main
sudo docker compose -f docker-compose.ec2.yml build
sudo docker compose -f docker-compose.ec2.yml up -d
```

Only rebuild the service that changed to save time:

```bash
# Backend change only
sudo docker compose -f docker-compose.ec2.yml build upsc-backend
sudo docker compose -f docker-compose.ec2.yml up -d --no-deps upsc-backend

# Frontend change only
sudo docker compose -f docker-compose.ec2.yml build upsc-frontend
sudo docker compose -f docker-compose.ec2.yml up -d --no-deps upsc-frontend
```

## EC2 Operations

```bash
# Container status
sudo docker compose -f docker-compose.ec2.yml ps

# Logs
sudo docker logs upsc-quiz-upsc-backend-1 --tail=50 -f
sudo docker logs upsc-quiz-upsc-frontend-1 --tail=50 -f

# Health check
curl http://localhost/health

# Restart everything
sudo docker compose -f docker-compose.ec2.yml restart

# Stop everything
sudo docker compose -f docker-compose.ec2.yml down
```

## Docker Architecture on EC2

| Container | Image | Role | Port |
|---|---|---|---|
| `upsc-quiz-upsc-mongodb-1` | `mongo:7` | Database | 27017 (internal) |
| `upsc-quiz-upsc-backend-1` | built from `backend/` | FastAPI API | 8000 (internal) |
| `upsc-quiz-upsc-frontend-1` | built from `frontend/` | nginx serving React + proxying `/api` | 80 (public) |

nginx proxies `/api/*` → backend:8000 and serves the React build for everything else.
MongoDB data is persisted in a Docker volume (`upsc-quiz_mongodb_data`).

## Environment Variables

### Backend (set in `docker-compose.ec2.yml`)

| Variable | Value on EC2 | Notes |
|---|---|---|
| `MONGODB_URI` | `mongodb+srv://upsc-app:...@upsc-quiz-cluster.g3gjjao.mongodb.net/upsc_quiz` | MongoDB Atlas — see credentials below |
| `DB_NAME` | `upsc_quiz` | |
| `UPLOAD_DIR` | `/tmp/upsc_uploads` | Temporary; files deleted after parsing |
| `CORS_ORIGINS` | `*` | Open on EC2; restrict to a domain if needed |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | No Ollama on EC2 — validation skipped gracefully |
| `OLLAMA_MODEL` | `gpt-oss:120b-cloud` | |
| `OLLAMA_API_KEY` | (empty) | |

## MongoDB Atlas

- **Project:** upsc-quiz (id: 6a37eb93afc546def6b872e2)
- **Cluster:** upsc-quiz-cluster
- **Connection string:** `mongodb+srv://upsc-quiz-cluster.g3gjjao.mongodb.net`
- **DB user:** `upsc-app`
- **Database:** `upsc_quiz`
- **Atlas API profile:** `upsc` (keys stored in `~/.config/atlascli/config.toml`)
- **IP whitelist:** dev machine + 13.206.94.228 (EC2)

> The `support` collection is NOT wiped on PDF upload — only `documents`, `groups`, `questions`, `attempts` are wiped.

### Frontend (baked in at Docker build time)

| Variable | Value | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | `/api` | Relative — nginx handles the proxy |

For local dev the default in `client.js` is `http://localhost:8002/api`.

## AWS Account

- **Account ID:** 874041194383
- **IAM user:** namansinha, region ap-south-1
- **Credentials:** `~/.aws/credentials`, `default` profile, no SSO needed

```bash
aws sts get-caller-identity    # verify you're authenticated
```

## Support Tickets

Users can submit support tickets via the `?` button in the app header. Tickets are stored in the `support` MongoDB collection with fields: `message`, `image_base64` (compressed JPEG), `resolved` (bool), `created_at`.

To review open tickets and mark resolved:

```bash
# List all tickets
curl http://<ip>/api/support

# Mark a ticket resolved
curl -X PATCH http://<ip>/api/support/<ticket_id>/resolve
```

When a user reports an issue: read the support table → fix in code → push → deploy → mark resolved.

## Key Design Decisions

- **Single-document mode:** uploading a new PDF wipes all previous documents, groups, questions, and attempts. The `support` collection is never wiped.
- **LLM validation is lazy:** runs once per chapter on the first quiz attempt, not at upload time. Gracefully skipped if Ollama is unavailable.
- **Support images are compressed:** resized to max 1200px and saved as JPEG at 70% quality before storing in MongoDB.
- **No static IP:** EC2 public IP changes on every stop/start. Use an Elastic IP if a permanent URL is needed.
