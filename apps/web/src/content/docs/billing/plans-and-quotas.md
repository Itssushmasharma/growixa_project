---
slug: "plans-and-quotas"
category: "billing"
title: "Subscription Plans & Quota Limits"
excerpt: "Understand how contact quotas (max_contacts) and email send allowances work across plan tiers."
icon: "📊"
readingTimeMinutes: 4
lastUpdated: "2026-08-17"
tags: ["billing", "plans", "quotas", "limits", "pricing"]
relatedSlugs: ["upgrading-plan", "contact-management"]
---

## How Quotas Are Enforced

- **Active Contacts Quota**: Only contacts with `status == 'ACTIVE'` count toward your plan limit. Archived contacts do not consume quota.
- **Email Send Limits**: Monthly send allowances reset at each billing cycle rollover.
- **Real-Time Warning**: Reaching your quota prevents new contact creations with a clear upgrade prompt (`HTTP 402`).
