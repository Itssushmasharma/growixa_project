# Phase 2 CRM and Audience Platform

Authorized by the product owner on 2026-09-15. Status: IN_PROGRESS.

Extend existing accounts/contacts/custom-fields/tags/lists/segments/imports/consent/suppression; do not create a second contact system. Phase 1 remains an unmerged prerequisite; this branch is stacked on its checkpoint to retain security fixes. Root checkout has unrelated UI changes and is preserved.

## Acceptance and implementation sequence

1. CRM companies, contact company/job/lifecycle metadata, tenant-scoped activity: additive schema, secure paginated APIs and real-data screens.
2. Complete tags editing/deletion/bulk assignment and filtering using existing tag tables.
3. Typed segment predicates, AND/OR, saved snapshots and count preview; identical API/worker evaluation.
4. CSV detection/mapping/preview/validation and durable background imports with row errors/history.
5. Separate email/phone consent history and account-scoped phone suppression; preserve existing email unsubscribe exclusions and never implicitly resubscribe imports.
6. Integrated UI, API/worker/web tests, reversible migrations, lint/types/build and independent review.

No fake production CRM data. No global suppression or retention/purge policy change: those remain separate unresolved product decisions. Every new list is SQL-paginated and all writes use contacts.manage with current account identity. Cross-account object references fail with 404. P0 Phase 1 recovery/revocation prevents a production-ready release claim until closed.

Expected paths: API contacts and new crm module, worker recipient evaluator/models, additive Alembic migrations, web contacts/companies/imports/segments/tag screens and tests, project-control docs.
