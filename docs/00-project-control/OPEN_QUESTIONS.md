# Open Questions

- Document ID: DOC-OPEN-QUESTIONS
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [DECISIONS](DECISIONS.md), [ASSUMPTIONS](ASSUMPTIONS.md), [BLOCKERS](BLOCKERS.md)

Questions that block a specific decision gate (see [DECISIONS.md](DECISIONS.md) §"Decision
gates"). A task that depends on an unresolved question here must be marked `BLOCKED`, not
guessed.

| ID | Question | Blocks | Status |
|---|---|---|---|
| OQ-001 | Which authentication approach: self-hosted email/password + sessions, or an external auth provider (e.g. Auth0/Clerk)? | Slice 1 (Foundation) | OPEN |
| OQ-002 | Which email provider is the one production adapter for MVP (e.g. SES, Postmark, SendGrid, Mailgun)? | Slice 3 (First Email Campaign) | OPEN |
| OQ-003 | Which single social platform is the first integration (LinkedIn, Facebook Pages, Instagram Business, X)? | Slice 5 (Social Publishing) | OPEN |
| OQ-004 | Which AI provider(s) and default model(s) for the content assistant? | Slice 6 (AI Assistant) | OPEN |
| OQ-005 | Which S3-compatible object storage provider/target for local dev vs. production? | Slice 1 / Slice 5 (media) | OPEN |
| OQ-006 | Production cloud/hosting target? | DevOps setup | OPEN |
| OQ-007 | Is there a billing/payment provider requirement for MVP, or is usage metering internal-only for now (per ASM-008)? | Usage metering scope | OPEN |
| OQ-008 | Default data-retention periods for contacts, campaign history, AI generation history, audit logs? | Data model, retention policy | OPEN |
| OQ-009 | Email editor: build a minimal rich-text editor, or adopt an existing open-source email-builder library? | Email template feature | OPEN |
| OQ-010 | Social scheduling policy: fixed queue times, user-chosen times only, or AI-suggested times (estimate only, per PRD §19)? | Social scheduling feature | OPEN |
| OQ-011 | Target dependency-aware order for future-release SEO/AEO/GEO work relative to V1.1/V1.2 marketing features — confirm V1.5+ staging in [ROADMAP.md](../01-product/ROADMAP.md) is acceptable. | Long-term roadmap sequencing | OPEN |

When a question is resolved, move it into [DECISIONS.md](DECISIONS.md) as a logged decision
and mark it `RESOLVED` here with a link to the decision ID.
