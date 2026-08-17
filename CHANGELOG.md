# Changelog

All notable changes to **Growixa** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-17

> **Release Tag**: `v1.0.0`  
> **Release Date**: August 17, 2026  
> **Platform Status**: 🟢 **Production & UAT Staging Live**  
> **Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)  
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)  
> **Platform Admin Portal**: [https://growixa.iitdeveloper.com/platform/login](https://growixa.iitdeveloper.com/platform/login)

### 🚀 Added

#### 1. Multi-Tenant Customer SaaS & Platform Administration
- **Self-Service Onboarding**: Customer registration, email token verification, and session management (`/register`, `/verify-email`).
- **Super Admin Control Plane (`/platform`)**: Platform tenant management, provider credentials, and audit tracking.
- **Support Impersonation Sessions**: Audited time-boxed support sessions for customer assistance.
- **Billing & Subscriptions**: Plan tier quotas (Free, Starter, Pro, Enterprise), credit pack top-ups, and coupon discount engine.

#### 2. Audience CRM & Intelligence
- **Contact Management**: Contact tables, custom attributes, tags, and static lists.
- **Dynamic Segments**: Real-time rule-based audience segmentation.
- **CSV Bulk Importer**: Asynchronous streaming CSV contact ingestion with error reporting.
- **Suppression & Compliance**: Consent records, domain-level suppression, and soft-delete safeguards.

#### 3. Email Marketing & Automation
- **Visual Template Editor**: Rich email designer with versioning and dynamic merge tags.
- **Multi-Provider Integrations**: Postmark, Resend, SendGrid, and Custom SMTP with Fernet encryption.
- **Campaign Dispatch Engine**: RabbitMQ batch queue worker and RFC-compliant `List-Unsubscribe` headers.

#### 4. Social Media Automation
- **Multi-Account Channels**: Direct OAuth for Instagram, Facebook, LinkedIn, and Twitter/X.
- **Content Calendar**: Interactive scheduling calendar with mandatory approval workflows (`DRAFT` $\rightarrow$ `APPROVED` $\rightarrow$ `SCHEDULED` $\rightarrow$ `PUBLISHED`).

#### 5. AI Growth Studio
- **Multi-Model LLM Hub**: Unified OpenAI (GPT-4o), Anthropic (Claude 3.5), and Google Gemini interface.
- **Marketing Assistants**: Automated generation for email subjects, body copy, and social captions with token usage metering.

#### 6. Cloud Infrastructure & DevOps
- **Dedicated Hosting**: OVH VPS (`149.56.101.2`) with 100% Docker Compose containerization.
- **Dual-Domain Reverse Proxy**: Caddy auto-SSL for `growixa.iitdeveloper.com` and `uat.growixa.iitdeveloper.com`.
- **Automated CI/CD**: GitHub Actions workflows triggered on release tags (`v*.*.*` $\rightarrow$ Production, `v*-rc*` $\rightarrow$ UAT).
- **Automated Backups**: Daily dual-database backup cron with gzip compression and 14-day retention.
- **AI Agent Playbook**: Workspace skill in `.agents/skills/growixa-infra/SKILL.md`.
