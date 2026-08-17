---
slug: "segments-and-lists"
category: "contacts"
title: "Dynamic Rule-Based Segments vs Static Lists"
excerpt: "Target the right audience with real-time dynamic segments and curated static lists."
icon: "🎯"
readingTimeMinutes: 5
lastUpdated: "2026-08-17"
tags: ["segments", "dynamic-rules", "lists", "targeting"]
relatedSlugs: ["contact-management", "campaign-wizard"]
---

## Dynamic Segments vs Static Lists

- **Dynamic Segments**: Automatically recalculate membership in real time based on filter rules (e.g. `status == 'ACTIVE'` AND `created_at > 30 days ago` AND `tag == 'VIP'`). As new contacts join or change attributes, they automatically enter or leave the segment.
- **Static Lists**: Fixed subscriber groups (e.g. 'Newsletter Subscribers May 2026') where members are added or removed manually.

## Supported Rule Operators

When building dynamic segments, you can combine rules using operators:

- `EQUALS` / `NOT_EQUALS`
- `CONTAINS` / `NOT_CONTAINS`
- `GREATER_THAN` / `LESS_THAN` (for numbers and dates)
- `IS_SET` / `IS_NOT_SET`
