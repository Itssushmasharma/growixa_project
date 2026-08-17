---
slug: "importing-contacts"
category: "contacts"
title: "Importing Contacts via CSV & Field Mapping"
excerpt: "How to prepare CSV files, map columns, handle duplicates, and inspect import error reports."
icon: "📥"
readingTimeMinutes: 4
lastUpdated: "2026-08-17"
tags: ["import", "csv", "mapping", "subscribers"]
relatedSlugs: ["contact-management", "suppression-and-consent"]
---

## Preparing Your CSV File

Your CSV file should have a header row with columns like `email`, `first_name`, `last_name`, `phone`, and any custom fields. UTF-8 encoding is recommended.

## 3-Step Import Workflow

1. **Upload**: Drag and drop your `.csv` file in the Import Hub (`/dashboard/contacts/imports`).
2. **Map Columns**: Match your CSV header columns to Growixa contact fields (`Email`, `First Name`, `Last Name`, `Phone`, `Source`, `Custom Fields`).
3. **Process & Inspect**: Growixa processes rows in the background, updating existing contacts and flagging invalid rows with detailed error messages.
