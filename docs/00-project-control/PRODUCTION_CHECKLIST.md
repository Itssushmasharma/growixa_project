# Production Checklist

Before officially launching Growixa to the public, the following external provider credentials, approvals, and environment variables must be securely configured.

> [!WARNING]
> DO NOT claim the platform is 100% production-ready for public users until these external dependencies are resolved.

## External Provider Approvals Required
- [ ] **Meta (WhatsApp Business API)**: Business verification and API access approval for `whatsapp_connections`.
- [ ] **Twilio (SMS)**: A2P 10DLC registration and verified toll-free/local sender numbers for `sms_connections`.
- [ ] **SendGrid / Postal**: Dedicated IP warmup and DKIM/SPF verification for high-volume email delivery.
- [ ] **Stripe**: Live mode activation and webhook endpoints configured in the Stripe Dashboard.

## Critical Environment Variables (`.env.production`)
Ensure the following are set in the production environment securely (e.g., via Doppler or AWS Secrets Manager):
```env
# Core Platform
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
SECRET_KEY=your_secure_random_string

# External APIs
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
META_APP_ID=...
META_APP_SECRET=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
```

## Security Reminders
- No secrets are hardcoded in the repository.
- Ensure strict tenant isolation is enforced at the database layer (via `account_id` mapping).
- All webhooks must validate inbound signatures (e.g., `X-Hub-Signature-256` for Meta).
