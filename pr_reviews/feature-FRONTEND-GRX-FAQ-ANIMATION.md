Task: GRX-FAQ-ANIMATION (marketing FAQ accordion with hover-reveal animation)
Developer: Unknown — no handoff was filed and all commits carry the product owner's git
identity per AGENTS.md §2, so the authoring tool cannot be determined. Developer should
fill this in.
Reviewer: Claude Code (did not author this branch)
Branch: feature/FRONTEND/GRX-FAQ-ANIMATION
Worktree: none — reviewed the remote branch directly
Base Commit: main
Latest Commit: 466dfa9
Status: CHANGES_REQUESTED

## What Changed

Adds a five-item FAQ accordion to the marketing landing page: new `faq-section.tsx`
(+95), FAQ styles in `marketing.module.css` (+211), and a mount in `(marketing)/page.tsx`
(+2). No other files.

## Why

Reviewer's note: no handoff file existed for this branch — this one was created by the
reviewer so it could be reviewed at all, per AGENTS.md §4.1. Intent inferred from the diff
and commit message. The developer should replace this section.

## Tests

None supplied and **none added** — the diff contains no test file. Independently run by the
reviewer at `466dfa9`: dependency check first (`package.json`/`package-lock.json` identical
to `main`, so no install drift).

## Known Issues / Evidence Gaps

Reviewer could not view the page in a browser, so the animation itself and the visual
hover-reveal are unverified. All findings below come from the source and from comparing the
FAQ's claims against the shipped product.

## Review Findings

This is a **public marketing page making product and security claims**, so it was reviewed
the same way as `GRX-MARKETING-REDESIGN`: every factual assertion checked against the code.

### What is accurate — genuinely well researched

- **"Custom SMTP relay (Starter plan and above)"** — matches the seeded catalog exactly:
  `allow_byo_smtp` is `True` for Starter/Pro/Enterprise, `False` for Free.
- **"BYO AI keys … (Pro plan)"** — matches: `allow_byo_ai_key` is `True` only for
  Pro/Enterprise.
- **"OpenAI, Anthropic, Azure, or Ollama"** — all four are genuinely present in the `ai`
  module. No invented providers.
- **"These credits never expire"** — matches `DEC-GRX-030`.

Four non-trivial claims, all correct. That is a better hit rate than the pricing page or the
help centre managed, and worth saying.

### 1. BLOCKING (accessibility) — the FAQ buttons have no visible focus indicator

`marketing.module.css:805`, inside `.faqQuestionButton`:

```css
border: none;
outline: none;
```

`outline: none` removes the browser's default focus ring, and **no replacement is
provided** — `grep -c "focus-visible\|:focus"` across the entire file returns **0**. A
keyboard user tabbing through the FAQ has no indication of where they are.

This is **WCAG 2.2 Level AA, SC 2.4.7 Focus Visible** — squarely inside `GRX-NFR-003`,
which sets WCAG 2.2 AA as the target for user-facing UI. It is a genuine conformance
failure, not a nicety, and the fix is a few lines:

```css
.faqQuestionButton:focus-visible {
  outline: 2px solid #60a5fa;
  outline-offset: 2px;
}
```

### 2. BLOCKING (false security claim) — "Every single database table is keyed with a tenant account ID"

> "Growixa operates a secure multi-tenant architecture. **Every single database table is
> keyed with a tenant account ID**, and all queries enforce strict account-level isolation."

This is not true. **11 tables carry no `account_id`**: `permissions`, `roles`,
`role_permissions`, `platform_permissions`, `platform_role_permissions`,
`subscription_plans`, `credit_packs`, `coupon_codes`, and the three
`platform_*_provider_config` tables.

To be fair to the architecture: most of those are *correctly* global — a plan catalogue and
a permission registry are not tenant data, and the real customer-data tables **are**
account-scoped, which `test_cross_tenant_isolation.py` exercises. The isolation model is
sound. The sentence describing it is not.

That matters more than a normal inaccuracy, because it is a **security claim on a public
page**. A security-conscious prospect who checks will find it false, which devalues every
other claim on the page. It also conflicts with `PRD` §19 ("provider capabilities are never
overstated in the UI") and with `DEC-GRX-017`, which explicitly states Growixa is *not* the
traditional multi-tenant workspace pattern — isolation is an internal `account_id` concern.

Suggested wording that is both true and stronger: *"Every customer-data table is keyed to
your account ID, and every query is account-scoped. Cross-tenant isolation is enforced in
code and covered by automated tests."*

### 3. BLOCKING (unshipped feature) — "14-day free trial (no credit card required)"

There is **no trial implementation anywhere in the backend**. Grepping `trial` across
`apps/api/src/growixa_api/` returns a single hit — a comment in `platform_admin/api.py:299`
about manual, support-driven "trial extensions". No trial state, no trial period, no
trial-to-paid transition.

The FAQ states it as settled fact, with the added specificity of "no credit card required".
Note the pricing page carries a similar "Start 14-Day Free Trial" button on Starter, so this
may be a pre-existing product promise rather than something this branch invented — but it is
asserted here as a concrete customer guarantee. Either the trial needs building, or the
claim needs removing from both surfaces.

### 4. MEDIUM — "cancel at any time directly from your billing panel"

No cancel endpoint exists in `billing/api.py`. Cancellation appears to arrive via the
Razorpay webhook (`billing/scheduler.py` handles the resulting `CANCELED` state), meaning
the customer cancels in Razorpay, not in a Growixa billing panel. The claim describes a
control that is not there.

### 5. MEDIUM (accessibility) — collapsed answers stay in the accessibility tree

`.faqAnswerContainer` collapses with `grid-template-rows: 0fr` plus `overflow: hidden`.
That hides the text *visually*, but clipping is not hiding for assistive technology: all
five answers remain exposed, so a screen-reader user hears every answer regardless of which
item is open, and find-in-page matches invisible text. Add `hidden`/`inert` on the collapsed
state, or `visibility: hidden` at the end of the transition. Pairing `aria-controls` with
the existing `aria-expanded` would also help; `aria-expanded` alone is present and correct.

### 6. LOW — animation ignores `prefers-reduced-motion`

`grep -c "prefers-reduced-motion"` → **0**, on a feature whose stated purpose is animation
(0.45s row transitions). Users who ask their OS to reduce motion still get the full effect.

### 7. LOW — no tests, and no handoff was filed

The diff adds an interactive stateful component (`useState`, toggle, single-open behaviour)
with **zero tests**. One test asserting that opening item 2 closes item 1 would lock in the
accordion contract cheaply. Separately, no `pr_reviews/` file existed — per AGENTS.md §4.1
that is the developer's to create, not the reviewer's.

### Not findings

No secrets, no vendor credentials, no `dangerouslySetInnerHTML`, no data access, no
permission surface, no `account_id` handling. The component is static content plus local
state.

## Review Decision
CHANGES_REQUESTED

## Reviewed Code Commit
466dfa9

## Review Record Commit
(this commit)

## Human Approval
**Required** — customer-facing marketing page. Note that findings 2, 3 and 4 are product
decisions as much as copy fixes: the product owner needs to confirm whether the 14-day
trial and in-panel cancellation are things Growixa intends to build, or claims to withdraw.
Finding 1 is a straightforward WCAG AA conformance fix and should not need a decision.

Status: CHANGES_REQUESTED
