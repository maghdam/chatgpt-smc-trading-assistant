# 🐳 Docker Usage Guide for ChatGPT SMC Trading Assistant

This guide helps you build, run, and manage the backend for the ChatGPT-based SMC trading assistant using Docker.


---

## 🐳 Dockerfile

Create `Dockerfile` with:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## 📜 requirements.txt

```
fastapi
uvicorn
notion-client
ctrader-open-api
twisted
service_identity
```

---

## 🧪 First-Time Setup

```bash
# Clone the repository
git clone https://github.com/your-username/chatgpt-smc-trading-assistant.git
cd chatgpt-smc-trading-assistant

# Build all containers (ctrader-bot + ngrok)
docker-compose up --build
```

---

## 🚀 Run All Services

```bash
# Start both ctrader-bot and ngrok
docker-compose up
```

Or run in background:

```bash
docker-compose up -d
```

---

## 🔄 Development / Update Commands

### ▶️ Rebuild Only Backend

```bash
docker-compose up --build ctrader-bot
```

### 🔁 Restart Backend for Code Changes

```bash
docker-compose restart ctrader-bot
```

Or manually trigger reload:

```bash
docker exec -it ctrader-bot touch /app/app.py
```

---

## 🔍 Logs

```bash
docker-compose logs -f ctrader-bot
docker-compose logs -f ngrok
```

---

## 🐚 Access Container Shell

```bash
docker exec -it ctrader-bot bash
```

---

## 🛑 Stop & Clean

```bash
# Stop all
docker-compose down

# Stop just backend
docker-compose stop ctrader-bot

# Remove backend container
docker-compose rm -f ctrader-bot
```

---

## 🔐 Ngrok Token

Put in `.env` or `docker-compose.yml`:

```env
NGROK_AUTHTOKEN=your_token_here
```

---

## 🧠 When to Rebuild vs Restart

| 🔧 What Changed                          | 🏁 Action Needed                             |
|-----------------------------------------|----------------------------------------------|
| Python libraries (`requirements.txt`)   | `docker-compose up --build ctrader-bot`      |
| Python code (`*.py`)                    | `docker-compose restart ctrader-bot`         |
| Dockerfile or ENV vars                  | `docker-compose up --build`                  |
| Live editing via `.:/app` mount         | No restart needed                            |

---

## 🌐 Access Swagger UI

```
http://localhost:8000/docs
http://localhost:8000/redoc
```

---

## 🌍 Optional: Expose API with ngrok

```bash
ngrok http 8000
```

Then use the HTTPS URL in your GPT schema.

---

Happy hacking! 💻✨

