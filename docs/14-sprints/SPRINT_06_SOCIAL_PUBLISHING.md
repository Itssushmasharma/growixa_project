# Sprint 06 — Social Publishing

- Document ID: DOC-SPRINT-06
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-08-12
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [DECISIONS §DEC-GRX-010](../00-project-control/DECISIONS.md), [DECISIONS §DEC-GRX-023/024/025](../00-project-control/DECISIONS.md)

This is the 6th sprint *file* chronologically, but it implements product **Slice 5**
(Social Publishing) per [DEC-GRX-010](../00-project-control/DECISIONS.md) — sprint-file
numbering and product-slice numbering diverged when the unplanned multi-tenancy retrofit
consumed the "Sprint 5" filename ([DEC-GRX-017](../00-project-control/DECISIONS.md);
`DATA_MODEL.md` hit and documented this same collision first). Its job is to let any
Growixa customer connect their own Instagram Business account and publish or schedule a
single-image post to it, self-serve, with no IITDEVELOPER intervention per customer.

## Included

Per [MVP_SCOPE.md §D](../01-product/MVP_SCOPE.md), narrowed to a single image per post
for this sprint (confirmed with the product owner — see `DEC-GRX-023`'s consequences):

1. Instagram Business OAuth connect flow (via the Meta Graph API), view connection status,
   reconnect
2. Create a post: caption + exactly one JPEG image (≤8MB), save as a draft
3. Publish a draft immediately
4. Schedule a draft for a future time; cancel a scheduled post before it fires
5. Retry a failed post
6. A social-only content calendar / post list showing status and provider error visibility
7. Frontend UI for all of the above, gated by the new `social.manage` / `social.publish` /
   `social.view` permissions (connecting the account itself reuses the existing
   `integrations.manage` code from Slice 3)

Full data model: [DATA_MODEL.md §Slice 5 entities](../05-data/DATA_MODEL.md#slice-5-entities-full-detail),
[DATABASE_SCHEMA.md §Slice 5](../05-data/DATABASE_SCHEMA.md#slice-5-social-publishing-tables),
[ERD.md §Slice 5 additions](../05-data/ERD.md#slice-5-social-publishing-additions). RBAC:
[RBAC.md §Slice 5](../08-security/RBAC.md#slice-5-permission-codes). Threat model:
[THREAT_MODEL.md §Slice 5](../08-security/THREAT_MODEL.md#slice-5-social-publishing-scope).

Full task breakdown with dependencies: [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md)
(`GRX-SOCIAL-*`).

## Explicitly excluded from Sprint 6

- Video and carousel (multi-image) posts — the `social_post_media` schema is
  carousel/video-ready, but the service layer enforces exactly one JPEG this sprint.
  Instagram's video status-polling window is materially longer and a genuinely different
  reliability story; revisit as a separate, deliberately-scoped task.
- A proactive daily token-refresh background job — this sprint refreshes a near-expiry
  Instagram token inline, at publish time, in the worker. Simpler and ships now; revisit
  only if scheduled-far-in-advance posts start failing on dead tokens in practice.
- A multi-Page/multi-Instagram-account picker — the OAuth flow takes the first Facebook
  Page with a linked Instagram Business Account. Matches the product owner's current
  single-account scenario; a picker UI is additive later, not a rework.
- Platform-admin oversight tooling for social connections/posts across customer accounts
  (a future capability comparable to `GRX-SAAS-007`) — explicitly deferred; this sprint is
  the customer-facing, self-serve feature only. Confirmed with the product owner.
- A unified email+social content calendar (the `content_calendar` module
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md) already anticipates) —
  this sprint's calendar is social-only, matching MVP_SCOPE.md's literal placement of the
  calendar bullet under Social. Revisit only if a real unified-view need is articulated.
- Meta App Review for production-scale use beyond the developer's own test users — a
  rollout/timeline concern (typically 1–2+ weeks, requires business verification), not a
  build blocker. The connect flow works end-to-end in development mode against test users
  regardless.
- Rate-limiting beyond the existing `usage_records` audit trail (see `THREAT_MODEL.md`
  T50) and any entitlement/limit enforcement — same "recording, not enforcing" posture
  Slice 3 established for `usage_records`.

If implementing a Sprint 6 task seems to require touching any of the above, stop and flag
it — it means the task is scoped wrong, not that a shortcut through excluded territory is
warranted.

## Sprint 6 acceptance criteria

- An Admin/Marketing Manager can connect their account's own Instagram Business account
  via OAuth; the connection's status (connected, username, last error) is visible without
  reconnecting.
- An Admin/Marketing Manager/Content Creator can create a post draft — caption + one JPEG
  image — and edit it while it remains a draft.
- Attempting to save a post with no media, more than one media item, a non-JPEG image, or
  an image over 8MB is rejected with a clear error (negative test).
- An Admin/Marketing Manager can publish a draft immediately; it appears on the real
  connected Instagram account, and the post's stored `ig_media_id`/`ig_permalink` reflect
  the real published post.
- An Admin/Marketing Manager can schedule a draft; the worker's dispatch pipeline
  publishes it automatically at (or shortly after) the scheduled time with no manual
  action.
- An Admin/Marketing Manager can cancel a still-`DRAFT`/`SCHEDULED` post before it fires,
  and retry a `FAILED` post.
- A user with `social.view` only can see posts/connection status/calendar but gets 403
  attempting to create, edit, publish, schedule, cancel, or retry anything (negative
  test).
- A user with `social.manage` but not `social.publish` (Content Creator's exact grant) can
  create and edit a draft but gets 403 attempting to publish or schedule it — same
  draft-vs-publish gate shape Slice 3 established (negative test).
- Only a user with `integrations.manage` can connect/reconnect the Instagram account;
  every other role gets 403 (negative test — same shape as Slice 3's provider-connection
  gate).
- A cross-account attempt to read or act on another account's `social_connections`/
  `social_posts`/`social_post_media` row 404s, added to
  `test_cross_tenant_isolation.py`.
- An expired/revoked Instagram token causes a clean, immediately-surfaced failure
  ("reconnect required") rather than silently retrying a doomed publish three times.
- Automated backend, worker, and frontend tests pass; CI passes.

## Definition of done for this sprint

[DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md) applies to every task
in this sprint individually — the sprint itself is done only when every task in
[MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md) tagged
`GRX-SOCIAL-*` is `DONE`, not merely attempted. Per
[DEC-GRX-011](../00-project-control/DECISIONS.md), no task is marked `DONE` on
mocked-provider evidence — publish verification must be a real post to the product
owner's test-mode Instagram Business Account (or, if that account isn't reachable during
a given work session, explicitly flagged as an evidence gap rather than silently
assumed).
