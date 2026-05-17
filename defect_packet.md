# Defect Packet

## Sendable Summary

This sample shows how a QA engineer can turn failing replay output into a compact evidence packet with ownership clues and release implications. It is intentionally small, but the format is meant to look like something a team could use in a real decision.

## Summary

Failures found: 3

| Case | Step | Failure class | Evidence | Root-cause bucket |
| --- | --- | --- | --- | --- |
| checkout-001 | apply_discount | Business logic regression | discount total mismatch | Calculation or rule change |
| checkout-002 | payment_authorize | Integration reliability | dependency timeout | Service dependency or retry policy |
| api-001 | fetch_account_summary | API contract violation | response schema mismatch: missing field balance_available | Schema drift or missing response field |

## Recommended Triage

1. Assign business logic regression (apply_discount) to feature owner for review.
2. Assign integration reliability (payment_authorize) to platform/API owner for review.
3. Assign api contract violation (fetch_account_summary) to API/platform owner for review.
4. Keep evidence packet attached to release decision so failures are reproducible.
