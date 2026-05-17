# Release Risk Summary

This summary is designed for go/no-go discussion: what failed, what kind of failure it is, and whether the release can move with a compensating control.

- Events replayed: 11
- Failed cases: 3
- Risk level: High

## Failure Buckets

- Business logic regression: 1
- Integration reliability: 1
- API contract violation: 1

## Go / No-Go Note

Do not release: API contract violation / Business logic regression in api-001, checkout-001 (apply_discount / fetch_account_summary) requires an owner and fix or documented rollback. Conditional ship: integration failure in checkout-002 (payment_authorize) may proceed with an explicit compensating control if isolated and retry-safe.
