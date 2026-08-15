# Production Deployment

- Document ID: DOC-DEVOPS-PRODUCTION
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-08-14
- Owner: Coding agent
- Related documents: [LOCAL_DEVELOPMENT](LOCAL_DEVELOPMENT.md), [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md)

The actual deployed stack, replacing the abandoned Render plan (`render.yaml`/
`RENDER_DEPLOYMENT.md`, deleted per `GRX-SAAS-013`). Written after a real incident where
the two independent deploy paths below diverged and the live site silently called the
wrong backend for a period — see `CHANGELOG.md`'s 2026-08-14 entries for the full
narrative. This document must not drift from what's actually configured; if you change
either deploy path's environment variables, update this file in the same change.

## Topology

- **Backend (API + worker)**: a single Hugging Face Space, `iitdeveloper/growixa`
  (`https://iitdeveloper-growixa.hf.space`), Docker SDK. One container runs both the
  FastAPI API and the worker consumer loop (`start.sh`: `python -m growixa_worker.main &`
  in the background, `uvicorn ... --port 7860` in the foreground). Deployed via
  `.github/workflows/deploy-backend-huggingface.yml` (triggered by `deploy-prod.yml` on
  push to `main`), using `Dockerfile.space`. Postgres/Redis/RabbitMQ are external managed
  services, not hosted on HF.
- **Frontend (web)**: Netlify, site `growixa.netlify.app`. Next.js, deployed via
  `@netlify/plugin-nextjs`.

## Frontend has two independent deploy paths — keep their config in sync

This is the exact divergence that caused the earlier incident: these are two genuinely
separate systems with separate environment-variable stores, and nothing enforces they
agree.

1. **GitHub Actions**: `.github/workflows/deploy-frontend-netlify.yml`, triggered by
   `deploy-prod.yml` on push to `main`. Builds with `npm run build --prefix apps/web`,
   deploys with `netlify-cli deploy --build --prod --dir=apps/web/.next`. Its build-time
   env vars come from the GitHub repo's own **Variables** settings
   (`${{ vars.NEXT_PUBLIC_API_URL }}`) plus a hardcoded `API_INTERNAL_URL` in the
   workflow file itself.
2. **Netlify's own native GitHub integration**: configured directly in the Netlify
   dashboard ("Deploys from GitHub with Next.js"), reading `netlify.toml` at the repo
   root for build config and its **own separately-configured** environment variables
   (Site settings → Environment variables, with per-deploy-context values: Production /
   Deploy Previews / Branch deploys / Local dev). This is the path that's actually live
   today.

**When changing `NEXT_PUBLIC_API_URL` or `API_INTERNAL_URL`, update both:** the GitHub
repo Variable (Settings → Secrets and variables → Actions → Variables) *and* the Netlify
dashboard env var (all deploy contexts, at minimum Production). `NEXT_PUBLIC_API_URL` is
a Next.js **build-time** value — changing it requires a fresh build to take effect
(Netlify: "Trigger deploy" → "Clear cache and deploy site", not a plain redeploy).

## Same-origin API proxy (CORS workaround, `GRX-SAAS-013`)

The browser talks to the API through Netlify's own edge, not directly cross-origin:

- `netlify.toml`'s `[[redirects]]` rule proxies `/api/*` on `growixa.netlify.app` to the
  HF backend server-side. From the browser's perspective this is a same-origin request —
  no CORS, no preflight, cookies work without `SameSite=None`.
- `NEXT_PUBLIC_API_URL` **must be `/api`** (a relative path) in both deploy paths' env
  vars for this to be used — `apps/web/src/lib/env.ts`'s `getApiUrl()` just returns it
  verbatim, and `apps/web/src/lib/api-client.ts` prefixes every browser fetch with it.
- Server-side calls (Server Components, e.g. `apps/web/src/lib/auth.ts`'s
  `getCurrentUser`) bypass the proxy and hit the backend directly via
  `API_INTERNAL_URL` (set to the full HF URL) — no browser involved, so no CORS concern,
  same shape as `compose.yaml`'s `API_INTERNAL_URL: http://api:8000` for local Compose.

**Why this exists**: Hugging Face's Space ingress answers the browser's CORS preflight
(`OPTIONS`) itself, before the request reaches the container, and its answer omits
`Access-Control-Allow-Credentials` — confirmed by comparing an `OPTIONS` request against
the live HF Space (missing the header, no `x-proxied-*`/`server: uvicorn` markers,
meaning it never reached the app) against the identical request against local Compose
(header present, correct). This is not fixable by changing `apps/api`'s own
`CORSMiddleware` config — the request never reaches it. Proxying through Netlify's edge
removes the need for cross-origin credentialed requests (and therefore CORS preflights)
entirely, rather than depending on HF forwarding them correctly.

## Verifying a deploy

```bash
curl -s https://iitdeveloper-growixa.hf.space/health
# {"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}

curl -s -o /dev/null -w "%{http_code}\n" https://growixa.netlify.app/api/health
# 200 — confirms the Netlify proxy is live and reaching the backend
```

A real login/register attempt through the actual browser is the only way to confirm the
CORS workaround itself works — `curl`/scripted HTTP clients don't enforce CORS the way a
browser does, so they can't catch this class of bug.
