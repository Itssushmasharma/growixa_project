# API Test Layout

Keep API tests grouped by the product or platform area they exercise:

- `ai/` - AI provider connections, generation, and provider validation.
- `analytics/` - analytics endpoints and reporting behavior.
- `audit/` - audit log behavior and immutability.
- `auth/` - customer auth, registration, refresh tokens, rate limits, and password reset.
- `billing/` - coupons, quota checks, webhooks, credits, and subscriptions.
- `campaigns/` - campaign APIs and scheduler behavior.
- `cli/` - command-line seed and maintenance scripts.
- `company/` - company and brand settings.
- `contacts/` - contacts, imports, lists, tags, segments, consent, and suppression.
- `dashboard/` - dashboard API aggregation.
- `email_delivery/` - delivery, notifications, SMTP transport, webhooks, and unsubscribe behavior.
- `email_validation/` - email validation APIs and provider configuration.
- `infrastructure/` - startup, health, jobs, Redis, and migrations.
- `integrations/` - customer integration connection behavior.
- `permissions/` - RBAC, route protection, and tenant isolation.
- `platform_admin/` - platform admin auth, monitoring, accounts, support sessions, and platform config.
- `social/` - social OAuth, posts, and scheduler behavior.
- `templates/` - email template APIs and versioning.
- `users/` - user management and invitations.

Shared fixtures stay in `conftest.py` at this root so pytest can provide them to every
subdirectory.
