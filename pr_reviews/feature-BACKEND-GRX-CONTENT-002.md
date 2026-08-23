# Pull Request Review Handoff: feature/BACKEND/GRX-CONTENT-002

- **Task ID**: `GRX-CONTENT-002`
- **Branch**: `feature/BACKEND/GRX-CONTENT-002`
- **Worktree**: `.worktrees/grx-template-token-validation`
- **Developer Agent**: Antigravity (Google DeepMind)
- **Reviewed Code Commit**: `c4069a8`
- **Review Decision**: `PENDING_REVIEW`
- **Date**: 2026-08-24

---

## 1. Summary of Changes

Implements upfront template token validation during campaign/template creation and update, first-class `{{unsubscribe_url}}` merge tag support, and user-friendly error formatting returning clean `HTTP 422 Unprocessable Content`:

1. **`unsubscribe_url` Standard Token**:
   - Added `"unsubscribe_url"` to `RECIPIENT_STANDARD_TOKENS` in `apps/api/src/growixa_api/personalization/renderer.py` and `apps/worker/src/growixa_worker/personalization.py`.
   - Injected `unsubscribe_url: f"{settings.api_public_url}/unsubscribe/{recipient.id}"` in `apps/worker/src/growixa_worker/send_campaign.py`.
   - Injected `unsubscribe_url: f"{settings.api_public_url}/unsubscribe/preview-test"` in `apps/api/src/growixa_api/email_delivery/services.py` for test email sends.

2. **User-Friendly Error Formatting**:
   - Enhanced `UnknownTokenError` to return a clear, informative message explicitly mentioning:
     - The invalid token name (e.g. `{{typo_token}}`).
     - Whether broadcast mode was used.
     - A full comma-separated list of all available recipient standard tokens, account-level tokens, and usable custom fields for that workspace (e.g. `Available tokens: {{first_name}}, {{last_name}}, {{email}}, {{phone}}, {{unsubscribe_url}}, {{company_name}}, {{website_url}}, {{sender_name}}`).

3. **Upfront Token Validation on API Endpoints**:
   - Added `_validate_campaign_personalization` in `apps/api/src/growixa_api/campaigns/services.py` for `create_campaign` and `update_campaign`.
   - Added `_validate_template_personalization` in `apps/api/src/growixa_api/templates/services.py` for `create_template` and `add_template_version`.
   - Catches `PersonalizationError` and returns `HTTPException(422, detail=str(exc))` in FastAPI route handlers (`campaigns/api.py`, `templates/api.py`).

4. **Integration & Unit Testing**:
   - Added unit test `test_unsubscribe_url_standard_token_rendered` in `test_personalization_renderer.py`.
   - Added unit test `test_unknown_typo_token_blocks_validation` verifying informative error messages.
   - Added integration test `test_create_campaign_with_invalid_token_returns_422` in `test_campaigns.py`.
   - Added integration test `test_create_campaign_with_standard_and_unsubscribe_tokens_succeeds` in `test_campaigns.py`.
   - Added integration test `test_create_template_with_invalid_token_returns_422` in `test_templates.py`.

---

## 2. Key Files Modified

- [`apps/api/src/growixa_api/personalization/renderer.py`](file:///Users/ravi/Projects/growixa/apps/api/src/growixa_api/personalization/renderer.py): Added `unsubscribe_url` to `RECIPIENT_STANDARD_TOKENS` and enhanced `UnknownTokenError`.
- [`apps/api/src/growixa_api/campaigns/services.py`](file:///Users/ravi/Projects/growixa/apps/api/src/growixa_api/campaigns/services.py): Upfront token validation for campaigns.
- [`apps/api/src/growixa_api/campaigns/api.py`](file:///Users/ravi/Projects/growixa/apps/api/src/growixa_api/campaigns/api.py): Handle `PersonalizationError` -> `HTTP 422`.
- [`apps/api/src/growixa_api/templates/services.py`](file:///Users/ravi/Projects/growixa/apps/api/src/growixa_api/templates/services.py): Upfront token validation for email templates.
- [`apps/api/src/growixa_api/templates/api.py`](file:///Users/ravi/Projects/growixa/apps/api/src/growixa_api/templates/api.py): Handle `PersonalizationError` -> `HTTP 422`.
- [`apps/worker/src/growixa_worker/send_campaign.py`](file:///Users/ravi/Projects/growixa/apps/worker/src/growixa_worker/send_campaign.py): Injected `unsubscribe_url` into recipient data.
- [`apps/api/src/growixa_api/email_delivery/services.py`](file:///Users/ravi/Projects/growixa/apps/api/src/growixa_api/email_delivery/services.py): Injected `unsubscribe_url` into preview test data.
- [`apps/api/tests/campaigns/test_campaigns.py`](file:///Users/ravi/Projects/growixa/apps/api/tests/campaigns/test_campaigns.py): Integration tests for campaign validation.
- [`apps/api/tests/templates/test_templates.py`](file:///Users/ravi/Projects/growixa/apps/api/tests/templates/test_templates.py): Integration tests for template validation.
- [`apps/api/tests/personalization/test_personalization_renderer.py`](file:///Users/ravi/Projects/growixa/apps/api/tests/personalization/test_personalization_renderer.py): Renderer tests.

---

## 3. Verification & Test Evidence

- `ruff check apps/api apps/worker`: **0 errors (clean pass)**
- `ruff format --check apps/api apps/worker`: **0 errors (clean pass)**
- `pytest apps/api/tests`: **449 passed, 8 skipped in 64s**
- `pytest apps/worker/tests`: **35 passed in 1.63s**
- Total automated tests passing: **484 tests**.

---

## 4. Review Focus Points

1. **Token Allowlist & Security**: Verify that `RECIPIENT_STANDARD_TOKENS` contains only authorized recipient attributes and `PROHIBITED_FIELDS` remain strictly blocked.
2. **Error Usability**: Verify that the HTTP 422 error detail clearly explains the invalid token and suggests valid available tags for the user's account.
3. **No Breaking Changes**: Existing campaigns and templates with standard tags continue to function and render seamlessly.
