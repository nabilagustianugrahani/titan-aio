# TITAN AIO — Deployment Plan

## Stages

### Stage 1: Local Development (Current)
- **Database**: SQLite (aiosqlite)
- **Workers**: Simulated
- **Queue**: Redis (optional)
- **Entry**: `python -m titan.main`
- **MCP**: `python -c "from MCP.server import mcp; mcp.run()"`

### Stage 2: Kaggle Generation (Next)
- **Workers**: FLUX / Wan2.2 / LoRA on T4
- **Connectivity**: Redis queue + S3 storage
- **Secrets needed**: Kaggle API token, Redis URL, S3 credentials
- **Deploy**: Copy notebook files → Kaggle → Run

### Stage 3: VPS Production
- **Server**: VPS (DigitalOcean / Linode / Vultr)
  - 2 vCPU, 4GB RAM minimum
  - Ubuntu 22.04+
- **Database**: PostgreSQL 15+ (managed or Docker)
- **Queue**: Redis 7+ (managed or Docker)
- **Storage**: MinIO / S3
- **Reverse proxy**: Nginx + Cloudflare
- **Process manager**: systemd or Docker Compose
- **Domain**: titan-aio.example.com

### Stage 4: RunPod / Serverless GPU (Future)
- **Workers**: RunPod Serverless for FLUX/Wan generation
- **Reason**: Avoid Kaggle session limits
- **Cost**: ~$0.50/hr for T4 on RunPod

## Infrastructure as Code (Future)
- Docker Compose for local dev
- Terraform for VPS provisioning
- GitHub Actions for CI/CD

## Environment Variables (.env)

### Required
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/titan
REDIS_URL=redis://host:6379/0
```

### Storage
```
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=titan-assets
```

### Notion (optional)
```
NOTION_TOKEN=ntn_...
NOTION_CAMPAIGN_DB=...
NOTION_KNOWLEDGE_DB=...
NOTION_TASKS_DB=...
```

### Kaggle
```
KAGGLE_USERNAME=...
KAGGLE_KEY=...
```
