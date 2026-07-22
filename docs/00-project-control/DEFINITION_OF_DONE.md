# Definition of Done

- Document ID: DOC-DOD
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [AGENT_EXECUTION_RULES](../12-development/AGENT_EXECUTION_RULES.md), [DEVELOPMENT_READINESS](DEVELOPMENT_READINESS.md)

## No placeholder completion

A task or feature must **not** be marked `DONE` if it consists only of:

- Empty routes or static UI with no working logic behind it
- Hardcoded or fake results
- `TODO` comments standing in for real implementation
- Fake analytics or mocked data presented as real
- Database tables that exist but nothing writes to or reads from them
- Buttons or forms without a working implementation
- Mock-only provider adapters presented as production-ready
- Tests that only check HTTP status codes without checking behavior
- Documentation that claims functionality that doesn't exist yet

A foundation/scaffolding task is allowed to exist on its own, but must be explicitly
labeled as foundation work in the task tracker and feature status matrix — never marked
`DONE` as if it were a complete feature.

## A task is DONE only when all of the following are true

1. Acceptance criteria (as written in the relevant feature spec) pass.
2. Implementation is complete — not partial, not stubbed.
3. Required database migrations exist and run cleanly.
4. Unit tests pass.
5. Integration tests pass where the feature spec requires them.
6. End-to-end tests pass where the feature spec requires them.
7. Linting passes.
8. Formatting passes.
9. Type checking passes.
10. Security checks pass where applicable (see [08-security/SECURITY_CHECKLIST.md](../08-security/SECURITY_CHECKLIST.md), once created).
11. Error handling exists for realistic failure paths (not just the happy path).
12. Structured logging exists for the operation.
13. Audit events are recorded where the feature spec requires them.
14. Usage metering is recorded where the feature spec requires it (see PRD §18).
15. Documentation is updated to match what was actually built.
16. Feature status is updated in `FEATURE_STATUS_MATRIX.md`.
17. Project status is updated in `PROJECT_STATUS.md`.
18. `CHANGELOG.md` is updated.
19. Test evidence (what was run, what passed) is recorded in the task entry.
20. No critical `TODO` remains in the touched code.
21. No unrelated regression was introduced (verified, not assumed).

## A feature is DONE only when it works end to end

"End to end" means: the user can perform the action through the real UI, it hits the real
backend, it persists to the real database, and — where relevant — it produces a real
external effect (an email is actually deliverable via the configured provider, a social
post is actually publishable via the configured provider's API) in at least a sandbox/test
environment. Simulated success is not sufficient evidence of DONE.
