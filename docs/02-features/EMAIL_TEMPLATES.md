# Feature Specification: Email Templates

- Document ID: DOC-FEAT-012
- Feature Code: `GRX-FEAT-012`
- Status: ACTIVE (implemented)
- Owner: Coding agent
- Related Documents: [RBAC](../08-security/RBAC.md), [DECISIONS](../00-project-control/DECISIONS.md), [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md)

---

## 1. Summary

Reusable email content, versioned on every edit, that a campaign is built from
(`GRX-EMAIL-002`). Every template is owned by exactly one account — with one exception:
platform-published **default templates**, maintained by Growixa's own platform team and
browsable (read-only) by every account (`GRX-EMAIL-016`).

## 2. Data model

`apps/api/src/growixa_api/templates/models.py`:

- **`EmailTemplate`** — `account_id` (`NOT NULL`, FK → `accounts.id`), `name`,
  `is_platform_default` (`NOT NULL`, default `false`), `created_by_user_id` (nullable —
  `NULL` for platform-created rows, since platform admins are not `users` rows,
  `DEC-GRX-018`).
- **`EmailTemplateVersion`** — insert-only edit history, never updated after creation
  (mirrors `ConsentRecord`'s pattern). The "current" version is the row with the highest
  `version_number` for a template, not a separate mutable pointer. Denormalizes
  `account_id` from its parent template for schema consistency (`GRX-SAAS-001`).

### Platform-published default templates (`GRX-EMAIL-016`)

Every template is account-owned today except one exception: a reserved **platform
system account** (`accounts.is_platform_system`, a singleton enforced by a partial
unique index) owns every `EmailTemplate` row with `is_platform_default = true`. Seeded
by migration `b8704f3eeada`.

**Clone-not-edit is a hard requirement.** A customer never gets a direct reference to a
platform-owned template — "Use this template" creates an entirely independent,
account-owned `EmailTemplate`/`EmailTemplateVersion` copy. This is what lets the
platform update or retire a default template later without breaking, altering, or
silently mutating a campaign a customer already built from a previously-cloned copy.

Deliberately **not** an open "publish my template publicly" marketplace — only
Growixa's own platform team can publish a default, via `platform.templates.manage`.
Considered and rejected for this task: the sanitization/XSS surface, cross-tenant brand
leakage, IP conflict between accounts, and moderation burden an open user-publish
marketplace would add are a separate, higher-risk future decision.

## 3. Permissions

| Code | Scope |
|---|---|
| `campaigns.view` | List/preview own account's templates and browse platform defaults |
| `campaigns.manage` | Create/edit/delete own templates; clone a platform default into the account |
| `platform.templates.manage` | Create/update/retire platform-published default templates (`platform.owner`/`platform.admin` only — see [RBAC.md](../08-security/RBAC.md)) |

No account role, including account Admin, can create, edit, or delete a platform-owned
template directly — the only account-side interaction with one is browse (read-only) and
clone.

## 4. API

`apps/api/src/growixa_api/templates/api.py` (account-scoped, `/templates`):

- `GET /templates` — list the account's own templates with current version.
- `POST /templates` — create.
- `GET /templates/platform-defaults` — browse-only list of every platform default
  (not account-scoped; registered before `/{template_id}` to avoid the UUID path param
  swallowing the literal route).
- `GET /templates/{id}`, `GET /templates/{id}/versions`, `POST /templates/{id}/versions`
  (append a version), `DELETE /templates/{id}` — account-scoped; 404 for any
  `template_id` the caller's account doesn't own, including a platform default's id.
- `POST /templates/{id}/clone` — "Use this template": clones a platform default into the
  caller's account as a new, independent, editable row. 404 if `id` isn't a platform
  default (a regular template, including the account's own, is never a valid clone
  target).

`apps/api/src/growixa_api/platform_admin/api.py` (platform-admin, `/platform/templates`,
gated by `platform.templates.manage`):

- `GET /platform/templates` — every platform default (admin management view).
- `POST /platform/templates` — create.
- `POST /platform/templates/{id}/versions` — append a version (edit).
- `DELETE /platform/templates/{id}` — retire.

## 5. Frontend

`apps/web/src/app/(dashboard)/dashboard/templates/`:

- **My Templates** — the account's own library: create, edit, duplicate, delete,
  preview, plus starter presets (`presets.ts`).
- **Default Templates** — a separate, read-only section (rendered only when at least one
  platform default exists) showing platform-published templates: Preview and, for
  `campaigns.manage` holders, **Use this template**. Cloning navigates straight to the
  new copy's edit page so the customer can review or customize it immediately.

`apps/web/src/app/(platform)/platform/(protected)/templates/`:

- Platform admins (`platform.templates.manage`) publish, edit (append a new version), and
  retire default templates from a dedicated "Templates" sidebar page — list view, an
  inline create form, and a per-row edit form. Retiring asks for confirmation and makes
  clear that accounts which already cloned the template keep their own independent copy.

## 6. Personalization tokens

Both account-owned and platform-default templates validate subject/body against the
shared token renderer (`personalization/renderer.py`). Platform defaults are restricted
to the standard recipient/account tokens only (no account-scoped custom-field tokens),
since a platform template must resolve identically for every account regardless of that
account's own custom fields.
