---
slug: "suppression-and-consent"
category: "contacts"
title: "Suppression Lists, Bounces & Consent Compliance"
excerpt: "Comply with GDPR, CAN-SPAM, and CASL regulations with automatic unsubscribe suppression and audit trails."
icon: "🚫"
readingTimeMinutes: 4
lastUpdated: "2026-08-17"
tags: ["suppression", "unsubscribes", "bounces", "consent", "gdpr"]
relatedSlugs: ["contact-management", "segments-and-lists"]
---

## How Suppression Works in Growixa

Growixa maintains an immutable suppression list per tenant. When an email is suppressed (via unsubscribe link, spam complaint, hard bounce, or manual addition):

1. It is permanently blocked from receiving campaign emails.
2. Even if the email is re-imported from a CSV, it remains suppressed.
3. Archiving a contact never removes their suppression status.

## Domain-Level Suppression

You can also suppress entire domains (e.g. `@competitor.com` or `@disposable-inbox.net`) to prevent sending to specific organizations or temporary email services.
