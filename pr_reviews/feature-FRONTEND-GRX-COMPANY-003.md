Task: GRX-COMPANY-003 — AI Brand Control Center redesign
Developer: Claude Code
Reviewer: (pending)
Branch: feature/FRONTEND/GRX-COMPANY-003
Worktree: .worktrees/grx-company-003-brand-redesign
Base Commit: ae188536140e94fa71c307e307288c1705fa210a
Latest Commit: 872ef73f9fbf8d709536de603297ae589b96589f
Status: READY_FOR_REVIEW

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


## Review Decision


## Reviewed Code Commit
