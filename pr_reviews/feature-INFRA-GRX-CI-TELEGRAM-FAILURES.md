# PR Review Handoff: CI Failure Diagnostics & Release Notes in Telegram Notifications (`feature/INFRA/GRX-CI-TELEGRAM-FAILURES`)

- **Branch**: `feature/INFRA/GRX-CI-TELEGRAM-FAILURES`
- **Developer**: Google Antigravity (DevOps/Infra Agent)
- **Reviewed Commit**: `5dcb15354964673898518ce52ca315024daeb0b9`
- **Target Components**:
  - `.github/workflows/ci.yml`
  - `.github/workflows/deploy-uat.yml`
  - `.github/workflows/deploy-production.yml`

---

## 🎯 Summary of Changes
1. **CI Failure Diagnostics**:
   - Added a `Determine Failed Stages` step in `notify-on-failure` within `.github/workflows/ci.yml`.
   - Accurately reports which specific pipeline stage failed (`Backend`, `Worker`, `Frontend`, or `E2E Smoke Tests`) directly in the Telegram alert message.
2. **Release Notes in Deployment Notifications**:
   - Added an `Extract Release Notes Summary` step to `.github/workflows/deploy-uat.yml` and `.github/workflows/deploy-production.yml`.
   - Automatically parses and includes the top release bullets from `RELEASE_NOTES.md` into the Telegram deployment message for UAT and Production releases.

---

## 🧪 Verification
- Validated YAML parsing for all modified workflow files (`ci.yml`, `deploy-uat.yml`, `deploy-production.yml`).
- Validated Python regex extraction logic for `RELEASE_NOTES.md`.
- All pre-commit security & lint checks passed.

---

## 📋 Independent Review Verdict

- **Reviewer**: _Pending Independent Review_
- **Verdict**: `PENDING`
- **Reviewed Code Commit**: `5dcb15354964673898518ce52ca315024daeb0b9`
