# Feature Specification: SMS Marketing & Twilio Integration

- Document ID: DOC-FEAT-SMS-001
- Feature Code: `GRX-FEAT-SMS-001`
- Status: ACTIVE (Specified)
- Target Release: Release 1.2
- Owner: Product Owner / Architecture
- Related Documents: [PRD](../01-product/PRD.md), [MVP_SCOPE](../01-product/MVP_SCOPE.md), [ROADMAP](../01-product/ROADMAP.md), [MODULE_BOUNDARIES](../04-architecture/MODULE_BOUNDARIES.md), [SECURITY_ARCHITECTURE](../08-security/SECURITY_ARCHITECTURE.md)

---

## 1. Executive Summary

`GRX-FEAT-SMS-001` adds native SMS marketing automation capabilities to Growixa via a official **Twilio Integration**. It allows Admins to securely configure Twilio credentials in the web dashboard, manage contact phone numbers and SMS consent, compose and schedule SMS campaigns with live segment calculators, and handle automated TCPA/GDPR opt-out webhooks.

---

## 2. Functional Requirements

### 2.1 Admin Provider Configuration (`integrations` module)
- **Settings UI Screen**: An Admin user configures Twilio credentials under `Settings ➔ Integrations ➔ Twilio`:
  - `Account SID` (string)
  - `Auth Token` (encrypted secret token)
  - `From Phone Number` or `Messaging Service SID`
- **Security & Encryption**: Credentials are stored AES-GCM encrypted in the database via the `integrations` module. They are never exposed in plain text to non-admins and are automatically redacted (`[REDACTED]`) from system logs.
- **Connection Verification**: A "Test Connection" button sends a test ping to Twilio API to verify credential validity.

### 2.2 Contact Phone Number & Consent Management (`contacts` module)
- **E.164 Validation**: Phone numbers are validated and normalized to international E.164 format (e.g., `+14155552671`).
- **SMS Consent Tracking**: Contacts maintain distinct SMS consent states:
  - `OPTED_IN`: Explicit SMS opt-in recorded.
  - `OPTED_OUT`: Unsubscribed or sent opt-out keyword.
  - `NOT_SET`: Phone number present but explicit consent pending.
- **CSV Import Mapping**: Phone number & SMS consent columns are supported in CSV contact imports.

### 2.3 SMS Campaign Composer & Scheduler (`campaigns` & `sms_delivery`)
- **Composer UI**:
  - Live character counter and GSM-7 segment calculator (160 chars for single segment, 153 chars/segment for multi-part messages, Unicode/UCS-2 detection).
  - Personalization tags (e.g., `{{contact.first_name}}`).
- **Execution & Safety**:
  - Pre-send checks enforce `sms_consent_status == OPTED_IN` and `sms_suppressed == False`.
  - Scheduled dispatch via RabbitMQ worker queue.

### 2.4 Webhook Handling & TCPA/GDPR Compliance (`sms_delivery` module)
- **Delivery Status Reports (DLR)**:
  - Endpoint: `POST /webhooks/twilio/dlr`
  - Updates campaign message status: `sent`, `delivered`, `failed`, `undelivered`.
- **Automated Opt-Out Processing**:
  - Endpoint: `POST /webhooks/twilio/inbound`
  - When an inbound message contains standard opt-out keywords (`STOP`, `UNSUBSCRIBE`, `CANCEL`, `QUIT`), the system automatically updates the contact's consent status to `OPTED_OUT` and sets `sms_suppressed = True`.
- **Security Verification**: Webhooks validate the `X-Twilio-Signature` header using the configured Auth Token.

---

## 3. Data Model Requirements

```text
Table: provider_credentials (integrations module)
- id: UUID (PK)
- provider_name: VARCHAR ("twilio")
- credentials_encrypted: JSONB (AES-256 encrypted Account SID, Auth Token, From Number)
- status: VARCHAR ("ACTIVE", "DISABLED")
- created_at / updated_at: TIMESTAMPTZ

Table: sms_delivery_attempts (sms_delivery module)
- id: UUID (PK)
- campaign_id: UUID (FK -> campaigns.id, nullable)
- contact_id: UUID (FK -> contacts.id)
- provider_message_sid: VARCHAR (Twilio Message SID)
- status: VARCHAR ("QUEUED", "SENT", "DELIVERED", "FAILED", "UNDELIVERED")
- segment_count: INT
- error_code / error_message: TEXT
- sent_at / delivered_at: TIMESTAMPTZ

Table: sms_consent_logs (audit/contacts module)
- id: UUID (PK)
- contact_id: UUID (FK -> contacts.id)
- action: VARCHAR ("OPT_IN", "OPT_OUT_VIA_KEYWORD", "ADMIN_SUPPRESSED")
- source: VARCHAR ("WEBHOOK", "CSV_IMPORT", "MANUAL_EDIT")
- created_at: TIMESTAMPTZ
```

---

## 4. Audit & Metering Events

The system records immutable audit log entries:
- `integrations.twilio_updated`: When an admin updates Twilio credentials.
- `sms.campaign_created`: When an SMS campaign is drafted or scheduled.
- `sms.sent`: When an SMS segment is dispatched.
- `sms.opted_out`: When a contact opts out via `STOP` webhook.
