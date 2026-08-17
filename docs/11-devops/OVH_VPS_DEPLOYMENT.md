# Production Deployment Guide: OVHcloud VPS

- Document ID: DOC-DEVOPS-OVH-VPS
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-08-17
- Owner: Principal DevOps / Platform Engineer
- Related documents: [LOCAL_DEVELOPMENT](LOCAL_DEVELOPMENT.md), [PRODUCTION_DEPLOYMENT](PRODUCTION_DEPLOYMENT.md), [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md)

---

## 1. Overview & Hardware Topology

This guide defines the complete, production-grade installation, configuration, security hardening, automated backup, and zero-downtime deployment process for Growixa on an OVHcloud VPS instance.

### Target Server Baseline
- **Host**: `vps-a8199074.vps.ovh.ca`
- **IPv4 Address**: `149.56.101.2`
- **vCores**: 6 vCores
- **Memory**: 12 GB RAM
- **Storage**: 100 GB NVMe SSD
- **OS**: Ubuntu Linux (22.04 / 24.04 / 26.04 LTS)

### Service Architecture on the VPS

```mermaid
flowchart TB
    subgraph Public["Internet & Ingress"]
        Browser["User Browser / Client"]
        Webhooks["Provider Webhooks (Razorpay, Postmark)"]
    end

    subgraph Host["OVH VPS (149.56.101.2) — UFW: Ports 22, 80, 443 Only"]
        Caddy["Caddy Reverse Proxy<br/>Auto-TLS / Let's Encrypt<br/>(Ports 80 & 443)"]
        
        subgraph Docker["Private Docker Network (growixa-net)"]
            Web["Next.js Web Frontend<br/>(Port 3000)"]
            API["FastAPI Modular Monolith API<br/>(Port 8000)"]
            Worker["RabbitMQ Async Worker<br/>(Background Process)"]
            PG[("PostgreSQL 16 DB<br/>(Port 5432 - Internal Only)")]
            Redis[("Redis 7 Cache/Locks<br/>(Port 6379 - Internal Only)")]
            MQ[("RabbitMQ 3 Message Broker<br/>(Port 5672 - Internal Only)")]
        end
    end

    Browser -->|HTTPS :443| Caddy
    Webhooks -->|HTTPS :443| Caddy
    Caddy -->|app.growixa.com| Web
    Caddy -->|api.growixa.com| API
    API --> PG
    API --> Redis
    API -->|Publish Tasks| MQ
    Worker -->|Consume Tasks| MQ
    Worker --> PG
    Worker --> Redis
```

---

## 2. Pre-Deployment: DNS Records Setup

Configure the following `A` records in your DNS provider (e.g. Cloudflare, Route53, Namecheap):

| Record Type | Hostname / Subdomain | Target IP Address | TTL |
|---|---|---|---|
| `A` | `app.growixa.com` (or `@`) | `149.56.101.2` | Auto / 300s |
| `A` | `api.growixa.com` | `149.56.101.2` | Auto / 300s |

---

## 3. Server Provisioning & OS Hardening

### 3.1. SSH Connection & Base Updates
```bash
ssh root@149.56.101.2

# Update package repositories and base system
apt update && apt upgrade -y
apt install -y curl git ufw htop fail2ban unzip ca-certificates
```

### 3.2. Firewall Hardening (UFW)
Expose only SSH, HTTP, and HTTPS. Databases and message brokers must remain internal to Docker:
```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status verbose
```

### 3.3. Configure 4GB Swap Buffer
```bash
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## 4. Docker & Docker Compose Installation

Install Docker Engine from Docker's official Ubuntu repository:

```bash
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker
```

---

## 5. Growixa Application Setup

### 5.1. Clone Repository
```bash
mkdir -p /opt/growixa
cd /opt/growixa
git clone https://github.com/iitdeveloper-git/growixa.git .
```

### 5.2. Generate Secrets & Configure Environment
Generate cryptographically secure keys:
```bash
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
PG_PASSWORD=$(openssl rand -hex 16)
MQ_PASSWORD=$(openssl rand -hex 16)
```

Create `/opt/growixa/.env`:
```bash
cat <<EOF > /opt/growixa/.env
ENVIRONMENT=production
LOG_LEVEL=info

# PostgreSQL
POSTGRES_USER=growixa
POSTGRES_PASSWORD=${PG_PASSWORD}
POSTGRES_DB=growixa
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://growixa:${PG_PASSWORD}@postgres:5432/growixa

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_USER=growixa_user
RABBITMQ_PASSWORD=${MQ_PASSWORD}
RABBITMQ_URL=amqp://growixa_user:${MQ_PASSWORD}@rabbitmq:5672/

# Cryptographic Keys
JWT_SIGNING_KEY=${JWT_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=30

# URLs (Update with real domains)
FRONTEND_BASE_URL=https://app.growixa.com
API_PUBLIC_URL=https://api.growixa.com
NEXT_PUBLIC_API_URL=https://api.growixa.com

# Platform Super Admin Initial Credentials
PLATFORM_ADMIN_EMAIL=admin@growixa.com
PLATFORM_ADMIN_PASSWORD=SetAStrongPasswordHere123!
PLATFORM_ADMIN_FULL_NAME=Platform Owner

# Platform Transactional SMTP (Optional at startup, can be configured in UI)
PLATFORM_SMTP_HOST=
PLATFORM_SMTP_PORT=587
PLATFORM_SMTP_USERNAME=
PLATFORM_SMTP_PASSWORD=
PLATFORM_SMTP_FROM_EMAIL=noreply@growixa.com
PLATFORM_SMTP_FROM_NAME=Growixa

# 3rd Party Integrations
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
SUPABASE_STORAGE_URL=
SUPABASE_STORAGE_SERVICE_KEY=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
EOF

chmod 600 /opt/growixa/.env
```

---

## 6. Startup, Migrations & Bootstrap

```bash
cd /opt/growixa

# 1. Start backing data services
docker compose up -d postgres redis rabbitmq

# 2. Execute database migrations
docker compose run --rm api alembic upgrade head

# 3. Seed initial platform administrator
docker compose run --rm api python -m growixa_api.cli.seed_platform_admin

# 4. Launch all application containers
docker compose up -d --build
```

---

## 7. Caddy Reverse Proxy & Automatic SSL

### 7.1. Install Caddy
```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install -y caddy
```

### 7.2. Configure `/etc/caddy/Caddyfile`
```caddy
# Next.js Web Frontend
app.growixa.com {
    reverse_proxy localhost:3000
    encode zstd gzip
}

# FastAPI Backend API
api.growixa.com {
    reverse_proxy localhost:8000
    encode zstd gzip
}
```

### 7.3. Start Caddy
```bash
systemctl restart caddy
systemctl enable caddy
```

---

## 8. Automated Database Backups

The automated backup script is located at `scripts/backup_db.sh`. It performs an uncompressed stream dump, compresses with `gzip`, and enforces a 14-day retention cycle.

To enable nightly automated execution at 02:00 UTC:
```bash
chmod +x /opt/growixa/scripts/backup_db.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/growixa/scripts/backup_db.sh >> /var/log/growixa_backup.log 2>&1") | crontab -
```

---

## 9. 1-Click Deployment for Future Updates

To deploy new code updates seamlessly:
```bash
chmod +x /opt/growixa/scripts/deploy_vps.sh
/opt/growixa/scripts/deploy_vps.sh
```
