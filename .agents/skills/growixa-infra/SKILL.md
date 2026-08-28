---
name: growixa-infra
description: >-
  Expert DevOps and infrastructure playbook for managing, debugging, and deploying
  Growixa multi-environment architecture (Production, UAT/Staging, Caddy auto-SSL,
  Docker Compose, and GitHub Actions CI/CD on OVH VPS 149.56.101.2).
---

# Growixa Infrastructure & DevOps Skill

This skill provides step-by-step instructions, runbooks, and architectures for deploying and maintaining Growixa across Production and UAT environments on the OVHcloud VPS (`149.56.101.2`).

---

## 1. Architecture Overview & Port Bindings

| Component | Production (`/opt/growixa`) | UAT / Staging (`/opt/growixa-uat`) | Local Dev (`deploy/docker/compose.local.yaml`) |
|---|---|---|---|
| **Domain** | `https://growixa.iitdeveloper.com` | `https://uat.growixa.iitdeveloper.com` | `http://localhost:3000` |
| **Web Frontend (Next.js)** | `127.0.0.1:3000` | `127.0.0.1:3001` | `3000` |
| **API Backend (FastAPI)** | `127.0.0.1:8000` | `127.0.0.1:8001` | `8000` |
| **PostgreSQL** | Docker-internal `postgres:5432` (`growixa`) | `127.0.0.1:5433` (`growixa_uat`) | `5432` |
| **RabbitMQ Broker** | `127.0.0.1:5672` / `15672` | `127.0.0.1:5673` / `15673` | `5672` / `15672` |
| **Redis Cache** | Internal Docker Network | Internal Docker Network | `6379` |
| **Reverse Proxy** | Host-level Caddy (`/etc/caddy/Caddyfile`) | Host-level Caddy (`/etc/caddy/Caddyfile`) | Direct localhost port access |

---

## 2. Release & Deployment Workflows

### Triggering Automated Deployments via Git Tags:

1. **Deploy to UAT (Staging)**:
   ```bash
   git tag v1.0.0-rc1
   git push origin v1.0.0-rc1
   ```
   - Workflow: `.github/workflows/deploy-uat.yml`
   - Packages images: `ghcr.io/iitdeveloper-git/growixa-*:v1.0.0-rc1` & `:uat`
   - Deploys to: `/opt/growixa-uat/`

2. **Deploy to Production**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   - Workflow: `.github/workflows/deploy-production.yml`
   - Packages images: `ghcr.io/iitdeveloper-git/growixa-*:v1.0.0` & `:latest`
   - Deploys to: `/opt/growixa/`
   - **Build once, promote**: the workflow first checks GHCR for
     `growixa-*:v1.0.0-rc1` (same version, `-rc1` — the convention above). If found, it
     retags that already-tested UAT image as `v1.0.0`/`latest` with no rebuild and no
     re-run of the test suite — production runs the exact bytes UAT verified. Only falls
     back to a full test + rebuild when no matching RC image exists (e.g. a production tag
     cut without a prior RC cycle). If the source RC's version number doesn't match the
     production tag (multiple RC rounds, a version bump during promotion), pass it
     explicitly via `workflow_dispatch`'s `source_rc_tag` input instead of relying on the
     `-rc1` default.

---

## 3. Server Management Runbook

### Connecting to the Server:
```bash
ssh ubuntu@149.56.101.2
```

### Checking Fleet Health & Logs:
```bash
# Production fleet status
cd /opt/growixa && sudo docker compose ps
sudo docker compose logs -f --tail=50 api web worker

# UAT fleet status
cd /opt/growixa-uat && sudo docker compose ps
sudo docker compose logs -f --tail=50 api web worker

# Caddy Reverse Proxy & SSL status
sudo systemctl status caddy
sudo journalctl -u caddy -n 50 --no-pager
```

### Manual Rollouts & Database Migrations:
```bash
# Production update
sudo /opt/growixa/deploy/scripts/deploy_prod.sh latest

# UAT update
sudo /opt/growixa-uat/deploy/scripts/deploy_uat.sh uat
```

### Database Backup & Retention:
```bash
# Runs daily dual-DB backup (Prod + UAT) with gzip & 14-day prune:
sudo /opt/growixa/deploy/scripts/backup_db.sh
```

---

## 4. Key Rules for Any Coding Agent Working on Infra

1. **Never commit real secrets**: All API keys, DB passwords, JWT secrets must be in `.env` files or GitHub Secrets (`OVH_VPS_HOST`, `OVH_VPS_USER`, `OVH_VPS_SSH_KEY`).
2. **Preserve Environment Isolation**: UAT must NEVER connect to production Postgres (`5432`) or production RabbitMQ (`5672`).
3. **CORS & Same-Origin Proxying**: Browser requests in `apps/web` must use `/api` relative path so Caddy proxies same-origin without CORS preflight overhead.
