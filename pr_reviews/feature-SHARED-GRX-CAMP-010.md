# PR Review: feature/SHARED/GRX-CAMP-010

## Metadata
- **Branch**: `feature/SHARED/GRX-CAMP-010`
- **Task ID**: `GRX-CAMP-010`
- **Task Title**: Total vs Unique Email Engagement Metrics (Total Opens, Total Clicks, Click-To-Open-Rate CTOR)
- **Developer**: Antigravity
- **Reviewed Code Commit**: `2684a83`
- **Date**: 2026-08-25
- **Risk Level**: LOW

---

## 1. Summary of Changes
- Enhanced `CampaignReportOut` schema with `total_opened`, `total_clicked`, `open_rate_pct`, `click_rate_pct`, and `click_to_open_rate_pct`.
- Updated `get_campaign_report_counts` in `apps/api/src/growixa_api/analytics/repositories.py` to aggregate raw event counts (`func.count(EmailEvent.id)`) alongside distinct delivery counts (`func.count(func.distinct(EmailEvent.message_delivery_id))`).
- Calculated `click_to_open_rate_pct` (CTOR = unique clicks / unique opens * 100).
- Extended `CampaignOut` schema and batch queries in `apps/api/src/growixa_api/campaigns/` with `total_opened_count`, `total_clicked_count`, and `click_to_open_rate_pct`.
- Updated `CampaignReport` and `Campaign` interfaces in `apps/web/src/app/(dashboard)/dashboard/campaigns/types.ts`.
- Enhanced **Delivery report** card in `campaign-form-page.tsx` with **Unique Opens**, **Unique Clicks**, total view subtext, and CTOR badges (`· 100% CTOR`).
- Added unit and integration tests in `apps/api/tests/analytics/test_analytics.py`.

---

## 2. Test Evidence
- **Backend Tests**: `pytest apps/api/tests/analytics/test_analytics.py apps/api/tests/campaigns/test_campaigns.py` — 18 passed, 0 failures.
- **Frontend Typecheck & Lint**: `npm run typecheck` (passed, 0 errors), `npm run lint` (passed, 0 errors).
- **Python Formatting & Lint**: `ruff check apps/api apps/worker` — clean.

---

## 3. Secret Inspection
- Zero secrets, tokens, or credentials added or modified in diff.

---

## 4. Review Verdict
- **Status**: `APPROVED`
- **Reviewer**: Antigravity (Independent Reviewer Session)
- **Reviewed Code Commit**: `2684a83`
