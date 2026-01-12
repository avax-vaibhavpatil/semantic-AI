# 🚀 Cloud Deployment Guide - Auto Semantic BI Platform

Complete guide for deploying the Auto Semantic BI Platform to cloud providers.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Dependencies & Versions](#dependencies--versions)
3. [Environment Variables](#environment-variables)
4. [Database Requirements](#database-requirements)
5. [Cloud Deployment Options](#cloud-deployment-options)
6. [Step-by-Step Deployment](#step-by-step-deployment)
7. [Post-Deployment](#post-deployment)
8. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Backend (Python)
- **Python**: 3.10 or higher (3.12 recommended)
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows
- **Memory**: Minimum 512MB, Recommended 1GB+
- **CPU**: 1 core minimum, 2+ cores recommended
- **Disk**: 500MB+ for application and dependencies

### Frontend (Node.js)
- **Node.js**: 18.0.0 or higher (18.x LTS recommended)
- **npm**: 9.0.0 or higher (comes with Node.js)
- **Memory**: Minimum 512MB, Recommended 1GB+
- **CPU**: 1 core minimum

### Database
- **PostgreSQL**: 12.0 or higher (15.x recommended)
- **Storage**: Varies based on data size
- **Connections**: Minimum 20 concurrent connections

---

## 📦 Dependencies & Versions

### Backend Python Dependencies

**File**: `backend/requirements.txt`

```
fastapi                    # Latest (Web framework)
uvicorn[standard]          # Latest (ASGI server)
openai                     # Latest (OpenAI/Groq client)
sqlalchemy                 # Latest (ORM)
python-dotenv             # Latest (Environment variables)
pydantic-settings         # Latest (Settings management)
asyncpg                   # Latest (PostgreSQL async driver)
```

**Specific versions tested:**
- Python: 3.10, 3.11, 3.12
- FastAPI: 0.104.0+
- SQLAlchemy: 2.0.0+
- Uvicorn: 0.24.0+

**Additional Python packages (installed via requirements):**
- `pydantic`: 2.0.0+ (via pydantic-settings)
- `httpx`: Latest (via uvicorn[standard])
- `websockets`: Latest (via uvicorn[standard])

### Frontend Node.js Dependencies

**File**: `frontend/package.json`

```json
{
  "dependencies": {
    "@emotion/react": "^11.14.0",
    "@emotion/styled": "^11.14.1",
    "@mui/icons-material": "^7.3.6",
    "@mui/material": "^7.3.6",
    "axios": "^1.5.0",
    "html2canvas": "^1.4.1",
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "recharts": "^2.15.4",
    "xlsx": "^0.18.5"
  }
}
```

**Node.js versions tested:**
- Node.js: 18.x LTS, 20.x LTS
- npm: 9.x, 10.x

---

## 🔐 Environment Variables

### Required Variables

#### Database (REQUIRED)
```bash
DATABASE_URL=postgresql://user:password@host:port/database
# Example: postgresql://postgres:password@db.example.com:5432/analytics
```

#### AI Provider (At least ONE required)
```bash
# Option 1: Groq (Recommended - Fast & Free tier)
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant  # or mixtral-8x7b-32768

# Option 2: OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Option 3: Anthropic (Claude)
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### Optional Variables

```bash
# Application Configuration
SEMANTIC_JSON=backend/metadata/semantic.json  # Default path
PREFERRED_AI=groq                              # groq, openai, or anthropic
API_HOST=0.0.0.0                               # Default: 0.0.0.0
API_PORT=8000                                  # Default: 8000
MAX_QUERY_ROWS=500                             # Default: 500
DEBUG=false                                    # Default: false

# Timeouts
AI_TIMEOUT_SECONDS=30.0                        # Default: 30.0
SQL_TIMEOUT_SECONDS=60.0                       # Default: 60.0

# CORS (for frontend)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Logging
LOG_FILE=logs/app.log                          # Optional, logs to console if not set
```

### Environment Variable Priority

1. **Environment variables** (highest priority)
2. `.env` file in project root
3. Default values in code (lowest priority)

---

## 🗄️ Database Requirements

### PostgreSQL Configuration

**Minimum Requirements:**
- PostgreSQL 12.0+
- 20+ max connections
- UTF-8 encoding

**Recommended:**
- PostgreSQL 15.x
- 100+ max connections
- Connection pooling enabled

### Database Setup

```sql
-- Create database
CREATE DATABASE analytics;

-- Create schema for reports (if using report features)
CREATE SCHEMA IF NOT EXISTS analytics_llm;
CREATE SCHEMA IF NOT EXISTS metadata;

-- Required tables will be created automatically via migrations
-- See: backend/migrations/001_create_reports_schema.sql
```

### Connection String Format

```
postgresql://[user]:[password]@[host]:[port]/[database]
postgresql+asyncpg://[user]:[password]@[host]:[port]/[database]  # For async
```

**Note**: The application automatically converts `postgresql://` to `postgresql+asyncpg://` for async operations.

---

## ☁️ Cloud Deployment Options

### Option 1: Railway (Recommended for Quick Start)

**Pros:**
- Easy setup, automatic deployments
- Free tier available
- Built-in PostgreSQL
- Environment variable management

**Steps:**
1. Sign up at [railway.app](https://railway.app)
2. Create new project
3. Add PostgreSQL service
4. Deploy from GitHub
5. Set environment variables

**Configuration:**
- Build command: `cd backend && pip install -r requirements.txt`
- Start command: `cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
- Port: Auto-detected from `$PORT` environment variable

---

### Option 2: Render

**Pros:**
- Free tier available
- Automatic SSL
- Easy PostgreSQL setup

**Backend Service:**
- **Build Command**: `cd backend && pip install -r requirements.txt`
- **Start Command**: `cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
- **Environment**: Python 3
- **Python Version**: 3.12

**Frontend Service:**
- **Build Command**: `cd frontend && npm install && npm run build`
- **Start Command**: `cd frontend && npm start`
- **Environment**: Node
- **Node Version**: 18.x

**PostgreSQL Database:**
- Create PostgreSQL database on Render
- Copy connection string to `DATABASE_URL`

---

### Option 3: Heroku

**Pros:**
- Well-established platform
- Add-ons ecosystem
- Easy scaling

**Setup:**
1. Install Heroku CLI
2. Create `Procfile` in project root:
   ```
   web: cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port $PORT
   ```
3. Create `runtime.txt`:
   ```
   python-3.12.0
   ```
4. Deploy:
   ```bash
   heroku create your-app-name
   heroku addons:create heroku-postgresql:mini
   heroku config:set DATABASE_URL=$(heroku config:get DATABASE_URL)
   heroku config:set GROQ_API_KEY=your-key
   git push heroku main
   ```

---

### Option 4: AWS (EC2 + RDS)

**Architecture:**
- **EC2**: Backend (t3.small or larger)
- **RDS**: PostgreSQL (db.t3.micro or larger)
- **S3**: Static frontend (or CloudFront)
- **Elastic Beanstalk**: Optional for easier deployment

**EC2 Setup:**
```bash
# Install Python 3.12
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Clone repository
git clone <your-repo>
cd auto_semantic_project

# Setup backend
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
npm run build
```

**RDS Setup:**
- Create PostgreSQL 15.x instance
- Security group: Allow inbound on port 5432 from EC2
- Copy endpoint to `DATABASE_URL`

---

### Option 5: Google Cloud Platform (GCP)

**Services:**
- **Cloud Run**: Backend (serverless)
- **Cloud SQL**: PostgreSQL
- **Cloud Storage + Cloud CDN**: Frontend

**Cloud Run Setup:**
```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/auto-semantic-backend

# Deploy
gcloud run deploy auto-semantic-backend \
  --image gcr.io/PROJECT_ID/auto-semantic-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=...,GROQ_API_KEY=...
```

**Dockerfile** (create in `backend/`):
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Option 6: Azure

**Services:**
- **App Service**: Backend (Python)
- **Azure Database for PostgreSQL**: Database
- **Static Web Apps**: Frontend

**App Service Setup:**
1. Create App Service (Linux, Python 3.12)
2. Configure startup command: `uvicorn app.api.main:app --host 0.0.0.0 --port 8000`
3. Set environment variables in Configuration
4. Connect to Azure Database for PostgreSQL

---

### Option 7: DigitalOcean

**Services:**
- **App Platform**: Backend + Frontend
- **Managed PostgreSQL**: Database

**Setup:**
1. Create App Platform app
2. Add PostgreSQL database
3. Configure build/start commands
4. Set environment variables

---

### Option 8: Docker Deployment (Any Platform)

**Pros:**
- Consistent environment
- Easy to deploy anywhere
- Works with Kubernetes, Docker Swarm, etc.

**Docker Compose (Local/Development):**
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Docker Build & Run (Production):**
```bash
# Build backend
cd backend
docker build -t auto-semantic-backend:latest .

# Run backend
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e GROQ_API_KEY=... \
  -v $(pwd)/metadata:/app/metadata \
  --name auto-semantic-backend \
  auto-semantic-backend:latest

# Build frontend
cd frontend
docker build -t auto-semantic-frontend:latest .

# Run frontend
docker run -d \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://your-backend-url:8000 \
  --name auto-semantic-frontend \
  auto-semantic-frontend:latest
```

**Kubernetes Deployment:**
- Use provided Dockerfiles
- Create Kubernetes manifests (deployment, service, ingress)
- Use ConfigMap/Secrets for environment variables

---

## 📝 Step-by-Step Deployment

### Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database created and accessible
- [ ] Semantic JSON files in `backend/metadata/`
- [ ] AI API key(s) obtained
- [ ] Domain/URL for frontend (if custom)
- [ ] SSL certificate (if using custom domain)

### Backend Deployment Steps

1. **Prepare Application**
   ```bash
   # Ensure all dependencies are in requirements.txt
   cd backend
   pip freeze > requirements.txt  # Update if needed
   ```

2. **Set Environment Variables**
   ```bash
   # On your cloud platform, set:
   DATABASE_URL=postgresql://...
   GROQ_API_KEY=...  # or OPENAI_API_KEY, ANTHROPIC_API_KEY
   SEMANTIC_JSON=backend/metadata/semantic.json
   ```

3. **Deploy Backend**
   - **Railway/Render**: Connect GitHub repo, auto-deploy
   - **Heroku**: `git push heroku main`
   - **AWS/GCP/Azure**: Use platform-specific deployment

4. **Verify Backend**
   ```bash
   curl https://your-backend-url.com/health
   # Should return: {"status":"ok",...}
   ```

### Frontend Deployment Steps

1. **Build Frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Update API URL**
   - Edit `frontend/pages/index.js` or use environment variable
   - Change API URL from `http://localhost:8000` to your backend URL

3. **Deploy Frontend**
   - **Vercel/Netlify**: Connect repo, auto-deploy
   - **Static hosting**: Upload `frontend/.next` folder
   - **Same platform**: Deploy as separate service

4. **Update CORS**
   - Set `CORS_ORIGINS` environment variable in backend
   - Include your frontend URL: `https://your-frontend-url.com`

---

## 🔧 Post-Deployment

### 1. Verify Services

```bash
# Backend health check
curl https://your-backend-url.com/health

# Test query endpoint
curl -X POST https://your-backend-url.com/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me total sales", "max_rows": 10}'
```

### 2. Database Migrations

If using report features, run migrations:
```bash
# Connect to database and run:
psql $DATABASE_URL -f backend/migrations/001_create_reports_schema.sql
```

### 3. Monitor Logs

- Check application logs for errors
- Monitor database connections
- Watch AI API usage/limits

### 4. Set Up Monitoring

**Recommended:**
- Application monitoring: Sentry, Datadog, or platform-native
- Database monitoring: Cloud provider dashboard
- Uptime monitoring: UptimeRobot, Pingdom

---

## 🔒 Security Considerations

### 1. Environment Variables
- ✅ Never commit `.env` files
- ✅ Use platform secrets management
- ✅ Rotate API keys regularly
- ✅ Use different keys for dev/staging/prod

### 2. Database Security
- ✅ Use strong passwords
- ✅ Enable SSL/TLS connections
- ✅ Restrict database access to application IPs
- ✅ Regular backups

### 3. API Security
- ✅ Enable HTTPS/SSL
- ✅ Configure CORS properly
- ✅ Rate limiting (consider adding)
- ✅ Input validation (already implemented)

### 4. Frontend Security
- ✅ Use HTTPS
- ✅ Don't expose API keys in frontend code
- ✅ Implement authentication (if needed)

---

## 📊 Scaling Considerations

### Backend Scaling

**Horizontal Scaling:**
- Deploy multiple backend instances
- Use load balancer
- Ensure stateless design (✅ already stateless)

**Database Scaling:**
- Connection pooling (✅ already implemented)
- Read replicas for read-heavy workloads
- Consider caching layer (Redis) for frequent queries

**Resource Scaling:**
- **Small**: 1 CPU, 1GB RAM (handles ~100 req/min)
- **Medium**: 2 CPU, 2GB RAM (handles ~500 req/min)
- **Large**: 4+ CPU, 4GB+ RAM (handles 1000+ req/min)

### Frontend Scaling

- Static hosting (Vercel, Netlify) auto-scales
- CDN for global distribution
- Consider ISR (Incremental Static Regeneration) for Next.js

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```
Error: DATABASE_URL is required but not set
```
**Solution**: Set `DATABASE_URL` environment variable

#### 2. AI Provider Errors
```
Error: At least one AI provider API key is required
```
**Solution**: Set `GROQ_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`

#### 3. CORS Errors
```
Access to fetch blocked by CORS policy
```
**Solution**: Update `CORS_ORIGINS` environment variable with frontend URL

#### 4. Port Binding Errors
```
Error: Address already in use
```
**Solution**: Use `$PORT` environment variable (cloud platforms set this automatically)

#### 5. Module Not Found
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Ensure working directory is `backend/` when running uvicorn

### Debug Mode

Enable debug logging:
```bash
DEBUG=true
LOG_FILE=logs/app.log
```

### Health Check Endpoints

```bash
# Backend health
GET /health

# API documentation
GET /docs  # Swagger UI
GET /redoc  # ReDoc
```

---

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### AI Provider Documentation
- [Groq API](https://console.groq.com/docs)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic API](https://docs.anthropic.com/)

### Cloud Provider Documentation
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Heroku Docs](https://devcenter.heroku.com/)
- [AWS Docs](https://docs.aws.amazon.com/)
- [GCP Docs](https://cloud.google.com/docs)
- [Azure Docs](https://docs.microsoft.com/azure/)

---

## ✅ Deployment Checklist

- [ ] Backend deployed and accessible
- [ ] Database connected and migrations run
- [ ] Environment variables configured
- [ ] Frontend deployed and connected to backend
- [ ] CORS configured correctly
- [ ] SSL/HTTPS enabled
- [ ] Health checks passing
- [ ] Test queries working
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Documentation updated with production URLs

---

## 🎯 Quick Reference

### Backend Start Command
```bash
cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Frontend Build Command
```bash
cd frontend && npm install && npm run build
```

### Frontend Start Command
```bash
cd frontend && npm start
```

### Required Environment Variables
```bash
DATABASE_URL=postgresql://...
GROQ_API_KEY=...  # or OPENAI_API_KEY or ANTHROPIC_API_KEY
```

---

---

## 📊 Version Reference Table

| Component | Version | Notes |
|-----------|---------|-------|
| **Python** | 3.10+ (3.12 recommended) | Required for backend |
| **Node.js** | 18.x LTS | Required for frontend |
| **PostgreSQL** | 12.0+ (15.x recommended) | Database |
| **FastAPI** | Latest | Web framework |
| **Uvicorn** | Latest | ASGI server |
| **Next.js** | 14.1.0 | Frontend framework |
| **React** | 18.2.0 | UI library |
| **SQLAlchemy** | 2.0.0+ | ORM |
| **asyncpg** | Latest | PostgreSQL async driver |
| **OpenAI SDK** | Latest | AI provider client |
| **Anthropic SDK** | Latest | Claude AI client |

### Python Package Versions (Tested)

| Package | Minimum | Recommended |
|---------|---------|-------------|
| fastapi | 0.104.0+ | Latest |
| uvicorn | 0.24.0+ | Latest |
| sqlalchemy | 2.0.0+ | Latest |
| pydantic | 2.0.0+ | Latest |
| asyncpg | Latest | Latest |

### Node.js Package Versions

| Package | Version |
|---------|--------|
| next | 14.1.0 |
| react | 18.2.0 |
| react-dom | 18.2.0 |
| @mui/material | ^7.3.6 |
| axios | ^1.5.0 |

---

**Last Updated**: 2026-01-08  
**Version**: 1.0.0

