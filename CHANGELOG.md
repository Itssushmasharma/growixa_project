# Changelog

All notable changes to **Growixa** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-17

### 🚀 Added
- **Multi-Tenant SaaS Foundation**:
  - Self-service customer registration with email token verification.
  - Multi-tenant data isolation via `account_id` foreign keys across all entities.
  - Dedicated Platform Admin suite at `/platform` with role hierarchy and support session impersonation.
  - Subscription tiers (Free, Starter, Pro, Enterprise), credit pack top-ups, and coupon discount code redemption.
- **Audience & Contact CRM**:
  - Contact management with custom attributes, static lists, and dynamic smart segments.
  - Asynchronous streaming CSV contact import with progress polling and error reporting.
  - Consent tracking, suppression lists, domain-level blocking, and soft-delete recovery safeguards.
- **Email Marketing & Campaigns**:
  - Email template designer with versioning and dynamic merge tags.
  - Multi-provider support for Postmark, Resend, SendGrid, and Custom SMTP with AES-Fernet encryption.
  - Campaign scheduler with RabbitMQ batch queue worker and RFC-compliant unsubscribe headers.
- **Social Media Automation**:
  - Multi-account OAuth connection for Instagram, Facebook, LinkedIn, and Twitter/X.
  - Interactive social post calendar with scheduled publication and mandatory approval workflows.
- **AI Growth Studio**:
  - Unified multi-model AI assistant powered by OpenAI GPT-4o, Claude 3.5, and Google Gemini.
  - Multi-variation generation for subject lines, email copy, and social captions with token usage metering.
- **DevOps & Cloud Infrastructure**:
  - Production and UAT multi-environment deployment on dedicated OVH VPS (`149.56.101.2`).
  - Host-level Caddy reverse proxy with automated Let's Encrypt TLS for `growixa.iitdeveloper.com` and `uat.growixa.iitdeveloper.com`.
  - GitHub Actions automated CI/CD pipeline triggered by Git release tags (`v*.*.*` $\rightarrow$ Production, `v*-rc*` $\rightarrow$ UAT).
  - Daily automated PostgreSQL backup script with gzip compression and 14-day retention pruning.
- **Universal Coding Agent Skill**:
  - Created `.agents/skills/growixa-infra/SKILL.md` for seamless DevOps pair programming across all coding agents.
