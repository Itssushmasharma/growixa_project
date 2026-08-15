Task: GRX-MARKETING-REDESIGN (no MASTER_TASK_TRACKER row — see finding 7)
Developer: Unknown — all commits carry the product owner's git identity per AGENTS.md §2,
so the authoring tool cannot be determined from git history. Developer should fill this in.
Reviewer: Claude Code (did not author this branch; independent of whoever did)
Branch: feature/FRONTEND/GRX-MARKETING-REDESIGN
Worktree: none (worktree removed or never created; reviewed the branch directly)
Base Commit: 0e99e38
Latest Commit: cc75eb6
Status: CHANGES_REQUESTED

## What Changed

Marketing pricing section reworked: plan set changed from Starter/Growth/Enterprise to
Free/Starter/Pro/Enterprise, a USD/INR currency switcher and Monthly/Annual billing toggle
added, and a new "Pay-As-You-Go Add-On Credit Packs" block appended. `.priceValue` /
`.pricePeriod` made responsive via `clamp()` to stop INR values overflowing their card.

## Why

Reviewer's note: no handoff file existed for this branch — this file was created by the
reviewer so the branch could be reviewed at all. Intent inferred from the diff and commit
messages, not from a developer statement. The developer should replace this section.

## Important Files

- `apps/web/src/app/(marketing)/pricing-section.tsx` (+269/−42, the whole change)
- `apps/web/src/app/(marketing)/marketing.module.css` (responsive price type)
- `apps/web/src/app/(marketing)/page.test.tsx` (one heading assertion updated)

## Tests

No test evidence was supplied by the developer. Independently run by the reviewer at
`cc75eb6`:

- `npm test` → 35 files, 191 tests passed.
- `npm run typecheck` → 0 errors.
- `npm run lint` → 0 errors, 4 warnings (all pre-existing `no-img-element` in
  `dashboard/social/*`, not from this branch).
- `npm run format:check` → **FAILS** on `src/app/(marketing)/pricing-section.tsx`.

## Known Issues / Evidence Gaps

Reviewer could not verify the page visually — no preview server was run. All findings below
are from the diff and from comparing displayed values against the seeded billing catalog.

## Review Findings

Verified against the actual diff at `cc75eb6` and against the real billing catalog in
`apps/api/migrations/versions/e926f73f7ece_billing_schema_rbac_seed.py` and
`b6eed962fd56_credit_packs_table.py` — not against any claim in this file.

**What is correct.** Plan slugs (`free`/`starter`/`pro`/`enterprise`) match the seeded
catalog, `/register?plan=` is genuinely honored (`register/page.tsx` + its test), and every
Free/Starter/Pro quota shown — contacts, emails, AI runs, seats — matches the seeded
`max_*` values exactly. Starter `$19` / Pro `$49` and `₹1,499` / `₹3,999` match
`price_usd`/`price_inr`. The "Save 20%" label is arithmetically honest (all six annual
figures are 20–21% off). Credit "never expires" matches DEC-GRX-030.

1. **BLOCKER — Enterprise is advertised at a fabricated price.** The card shows
   `$149`/`$119` and `₹11,999`/`₹9,599`. The seeded Enterprise row is
   `price_usd: None, price_inr: None`, and `models.py:41` states why: *"NULL for
   Enterprise — contact-sales, no fixed self-serve price (DEC-GRX-030 point 4)."*
   `register/page.tsx:13` carries the same rule. This publishes a price the product has
   explicitly decided not to have, on a public page. Violates DoD "No placeholder
   completion" (hardcoded/fake results) and PRD §19 (never overstate in the UI).
   The card also still says "Contact Sales" and links to `/login` while showing a
   concrete price — internally contradictory even on its own terms.

2. **BLOCKER — annual billing is advertised but cannot be bought.** The Monthly/Annual
   toggle offers `$15`/`$39`/`$119` and `₹1,199`/`₹3,199`/`₹9,599`. There is no annual
   concept anywhere in billing: `subscription_plans` has a single `price_usd`/`price_inr`
   and a single `razorpay_plan_id_usd`/`_inr`, and `SubscribeIn.plan_slug` is
   `Literal["starter", "pro"]` with no period field. A visitor selecting Annual and
   clicking through is checked out monthly at a different price than displayed.

3. **BLOCKER — every add-on USD price is fabricated, and the INR prices are wrong.**
   All five seeded packs have `price_usd: None` (the pack catalog is INR-only), yet the
   page shows `+$5` / `+$10`. The INR figures are also each ₹1 below the real values:

   | Page | Real seeded pack |
   |---|---|
   | AI Generation Pack `+₹399` — +250 AI runs | `ai_runs_250` — **₹400** |
   | Email Send Pack `+₹799` — +10,000 emails | `email_sends_10000` — **₹800** |
   | Extra Contacts Pack `+₹799` — +2,500 contacts | `contact_slots_2500` — **₹800** |

4. **BLOCKER — "Social Account Add-on" is a product that does not exist.** The page sells
   `+$5/mo` / `+₹399/mo` for "+3 Connected Social Accounts". No such pack is seeded. The
   nearest row is `social_posts_50` — 50 extra social *posts*, ₹400, one-time, not
   recurring, and not connected accounts. Three separate misstatements (unit, recurrence,
   what is bought). Also note the page's currency switcher offers USD across a catalog
   that has no USD prices at all — worth resolving as one decision with findings 1 and 3.

5. **BLOCKER (CI) — `npm run format:check` fails on `pricing-section.tsx`.** DoD item 8
   requires formatting to pass, and `ci.yml:156` runs this in the frontend job, so this
   branch turns CI red on merge. Fix: `npx prettier --write "src/app/(marketing)/pricing-section.tsx"`.

6. **MEDIUM — no tests for any of the new behavior.** The only test change is a heading
   string. The currency switcher, the period toggle, `getPriceDisplay()`'s branching, and
   the add-on block are entirely untested; `page.test.tsx` contains no reference to
   currency, INR, annual, or credit packs. For a component whose whole purpose is
   conditional price rendering, at least the USD↔INR and Monthly↔Annual paths need
   assertions — that is also what would have caught findings 1–4 as an intentional
   decision rather than an accident.

7. **LOW — process gaps.** No handoff file existed (created here by the reviewer); there
   is no `GRX-MARKETING-REDESIGN` row in `MASTER_TASK_TRACKER.md`; and no
   `WORKTREE_TRACKER.md` entry. Per AGENTS.md §4 the developer files the handoff, not the
   reviewer.

8. **LOW (non-blocking, style) — ~180 lines of inline `style={{…}}` replace the module's
   CSS-module convention.** Colors (`#38bdf8`, `#94a3b8`, `rgba(15,23,42,.8)`) and the
   `linear-gradient(135deg,#38bdf8,#a855f7)` accent are duplicated across many literals
   while `marketing.module.css` already owns this design language — note that the same
   change moved the *other* price styling into CSS, so the file is now inconsistent with
   itself. Not a merge blocker; flagged because it will be the expensive part to unwind
   once these values need to move.

No security issues found: this is an unauthenticated public marketing page with no data
access, no permission surface, no `account_id` scope, and no secrets or vendor identifiers
in the diff. RBAC.md and THREAT_MODEL.md have no applicable control here.

## Review Decision
CHANGES_REQUESTED

## Reviewed Code Commit
cc75eb6

## Review Record Commit
(this commit)

## Human Approval
Required (UI/UX and customer-facing pricing). Note that findings 1–4 are pricing
*accuracy*, not aesthetics: the product owner must confirm the intended real prices, and
whether Enterprise self-serve pricing and annual billing are being introduced as actual
product changes (which would need backend/catalog work and a DECISIONS.md entry
superseding DEC-GRX-030 point 4) or whether the page should be corrected to match the
catalog as seeded.

Status: CHANGES_REQUESTED
