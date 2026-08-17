---
slug: "smtp-setup"
category: "integrations"
title: "Custom SMTP & Mail Server Configuration"
excerpt: "Connect any standard SMTP provider (for example Amazon SES, SendGrid, Mailgun, or your own mail server)."
icon: "⚙️"
readingTimeMinutes: 4
lastUpdated: "2026-08-17"
tags: ["smtp", "ses", "sendgrid", "mailgun"]
relatedSlugs: ["postmark-setup", "domain-verification"]
---

## SMTP Parameters

- **Host**: SMTP server host (e.g. `email-smtp.us-east-1.amazonaws.com`).
- **Port**: Typically `587` (STARTTLS) or `465` (SSL/TLS).
- **Username & Password**: Mail authentication credentials.
- **Use TLS**: Check this box for encrypted transport.
