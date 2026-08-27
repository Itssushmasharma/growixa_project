Task: GRX-COMPANY-003 — AI Brand Control Center redesign
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: feature/FRONTEND/GRX-COMPANY-003
Worktree: .worktrees/grx-company-003-brand-redesign
Base Commit: ae188536140e94fa71c307e307288c1705fa210a
Latest Commit: 872ef73f9fbf8d709536de603297ae589b96589f
Status: APPROVED

## What Changed

Redesigned `/dashboard/company-settings` from a single flat form into a tabbed
"AI Brand Control Center": Company Profile / Brand Voice / AI Guardrails / AI
Preview. Two commits:

1. `e9f4538` — additive, nullable backend columns only (`company_profile.support_email`,
   `sender_name`, `business_address`, `description`; `brand_profiles.persona_tags`,
   `voice_settings`), migration `72e376f46c26`. No repository/service changes needed
   (`model_dump()`-driven upsert). Also pinned `mypy==1.18.2` (was floating unpinned and
   flagging unrelated pre-existing code red on `main`).
2. `872ef73` — the frontend redesign: new `components/` subfolder with one component per
   tab/widget (tabs, guardrail list, persona selector, voice sliders, logo uploader,
   sticky save bar, profile readiness, AI copy preview).

## Why

Direct product request to replace the flat settings form with a tabbed control center;
no `DEC-GRX-*` needed since it's UI-only over already-approved data (`GRX-COMPANY-001`/`002`).

## Important Files

- `apps/web/.../company-settings/company-settings-form.tsx` — orchestrator: load, dirty
  tracking, save (company then brand, sequential per existing pattern), permission gate.
- `apps/web/.../company-settings/components/guardrail-list.tsx` — structured add/remove
  rows over the existing `forbidden_claims`/`required_facts` `string[]` JSONB fields;
  wire format unchanged.
- `apps/web/.../company-settings/components/ai-copy-preview.tsx` — calls the real
  `POST /ai/generate/{capability}` (no separate preview endpoint); honest "not connected"
  state on HTTP 409; client-side forbidden-claims substring check against the actual
  generated text. Deliberately no tone/readability scores (nothing in the API computes
  them — `GRX-QA-001` precedent of fabricated AI scores).
- `apps/web/.../company-settings/components/logo-uploader.tsx` — `logo_url` is a real,
  already-persisted field; URL-entry is a working mechanism, not a placeholder. "Upload a
  file" is disabled/labeled "coming soon" since no upload endpoint exists in `growixa_api`
  (checked) — no capability is faked (`DEC-GRX-016`).
- `apps/api/src/growixa_api/{company,brand}/{models,schemas}.py`, migration
  `72e376f46c26_brand_control_center_fields.py`.

## Tests

Frontend (`apps/web`):
```
npm run test          # 300 passed, 52 files (10 in company-settings)
npm run lint           # 0 errors, 2 pre-existing warnings unrelated to this feature
npm run typecheck      # clean
npm run format:check   # clean
npm run build          # succeeds, /dashboard/company-settings 8.48 kB
```
New/updated: `company-settings-form.test.tsx` (tab switching, view-only disabling,
save/discard round-trip, guardrail add/remove), `components/ai-copy-preview.test.tsx`
(connected/not-connected/error states).

Backend (`apps/api`, from commit `e9f4538`): `pytest apps/api/tests/company/` covering
the new nullable fields round-tripping — see that commit for the run.

## Known Issues / Evidence Gaps

- No Playwright e2e added for the new tab flows (existing e2e coverage for this route
  was not extended). Acceptance criteria list only frontend component tests, which are
  present.
- Responsive behavior is fluid (flex-wrap / CSS grid `auto-fill`, overflow-x on the tab
  bar) rather than breakpoint-based; not verified in an actual browser at this session —
  flagged for the reviewer/product-owner to eyeball at mobile width.
- This is a UI/UX customer-facing change — per `AGENTS.md` §4.5 it needs the product
  owner's explicit approval before merge, in addition to code review.

## Review Findings

Verified independently against the real branch (`git log`/`git diff` `ae1885..HEAD`, the
branch's true divergence point from `main` — `main..HEAD` alone is noisy because `main`
moved forward independently after that point; confirmed the noise is unrelated docs/tracker
commits, not this branch's work).

- **Migration/model consistency**: `72e376f46c26` adds exactly the 6 nullable/JSONB-default
  columns declared in `company/models.py` and `brand/models.py`; `downgrade()` reverses them
  correctly; it is the sole head off `f2a3b4c5d6e7` (no branching); both modules are already
  imported in `migrations/env.py`. Schemas (`CompanyProfileIn`, `BrandProfileIn`) match.
- **RBAC**: No new routes added. `company.settings.edit`/`.view` and `ai.manage`/`ai.view`
  permissions are pre-existing and reused unchanged (verified in
  `apps/api/src/growixa_api/{company,ai}/api.py`) — no hand-rolled checks introduced.
- **No placeholder/fabricated completion** (the specific risk called out for this task):
  - `AICopyPreview` calls the real, pre-existing `POST /ai/generate/{capability}` route
    (confirmed in `apps/api/src/growixa_api/ai/api.py`) — not mocked, not a fake preview
    endpoint. 409 (`AINotConfiguredError`) is surfaced as an honest "not connected" state,
    not a fabricated result. No tone/readability scores are shown (correctly avoided,
    since the API computes none).
  - `LogoUploader` disables "Upload a file" and is truthful that no upload backend exists
    (confirmed: no upload/media route anywhere in `growixa_api`); the working URL-entry
    path writes to the real, already-persisted `logo_url` field.
  - `GuardrailList` is a real structured editor over the existing `forbidden_claims`/
    `required_facts` JSONB `string[]` fields — wire format unchanged, confirmed via the
    extended round-trip test.
- **Tests actually assert behavior**: ran them myself, not trusting the handoff.
  - Backend: `pytest apps/api/tests/company/` → 5 passed. The extended test asserts a real
    round-trip of every new field (`support_email`, `sender_name`, `business_address`,
    `description`, `persona_tags`, `voice_settings`) through PUT then GET — not a
    tautological check.
  - Frontend: `npx vitest run .../company-settings` → 10 passed across 2 files. Tests cover
    tab switching, view-only disabling, dirty-state save/discard (asserts both PUTs fire in
    the right order), guardrail add/remove, and all three `AICopyPreview` states (success,
    forbidden-claim detection, honest 409 not-connected) — genuine behavioral assertions,
    not implementation-detail checks.
  - `npm run lint` (0 errors, 2 pre-existing unrelated warnings), `tsc --noEmit` (clean),
    `npm run format:check` (clean), `npm run build` (succeeds) — all reproduced myself.
  - `ruff check .` and `mypy src/growixa_api/{company,brand}` on the backend — both clean.
- **Secrets scan**: grepped the full `ae1885..HEAD` diff for credential/token/key patterns —
  no hits. No hardcoded secrets.
- **Scope**: the branch also pins `mypy==1.18.2` (was floating unpinned) and wraps one
  over-long comment in `apps/api/tests/analytics/test_analytics.py`, both justified in the
  commit message as blocking local CI. Note: an *identical* fix to that same comment was
  separately made and already merged to `main` via `b970760` (GRX-CI-FIX-001) after this
  branch's base — the two are content-identical, so there is no real conflict or
  regression, but it is a sign this branch should have rebased onto `main` before review
  (the skill's stated preference) rather than review flagging pre-existing skew. Not a
  blocker.
- **Known gaps** (as declared in the handoff, checked and accurate): no Playwright e2e
  added for the new tab flows; responsive layout not eyeballed in a real browser this
  session. Given tab/save/preview logic is well covered by component tests and this is a
  low-complexity CSS layout, this is acceptable to ship with a human visual check, not a
  blocker for independent code review — but it is exactly why product-owner sign-off
  (UI/UX gate) is required below.
- Tracker (`MASTER_TASK_TRACKER.md`/`.csv`) row added correctly at `IN_REVIEW`, matching
  the actual state (task not yet merged).

No secret leakage, no RBAC bypass, no fabricated AI output, no unauthorized scope creep of
consequence. This is a well-scoped, honestly-labeled UI redesign over already-approved data.

## Review Decision
APPROVED

## Reviewed Code Commit
3aa37c0f1d9fc5721627aa2ba01709aa056fe029

## Review Record Commit
(recorded in the commit that adds this verdict)

## Human Approval

**Signed Off** — Product owner (Ravi Kant Yadav) approved this UI/UX redesign for merge
to `main` on 2026-08-27, after being informed of the independent review's findings above
(tabbed Brand Control Center over already-approved data; no fabricated AI output; honest
"not connected" AI Preview state; logo upload correctly labeled "coming soon" rather than
faked; responsive layout is fluid CSS, not browser-verified this session; no Playwright
e2e added for the new tab flows). Approved with that as known, accepted follow-up rather
than a blocker.

Status: APPROVED — independent review complete; product-owner sign-off recorded; cleared
for merge
