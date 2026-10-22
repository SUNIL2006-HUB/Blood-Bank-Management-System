## Summary
<!-- What does this PR do? One or two sentences. -->

## Linked story
Closes #<!-- issue number, e.g. #5 for PBI-01 -->

## Changes
- [ ] Backend (services / repositories / routes)
- [ ] Frontend (templates / forms)
- [ ] CI / config / docs

## Requirements covered
<!-- FR-xx / NFR-xx / SEC-xx from the SRS and Security Requirements -->

## Checklist (author)
- [ ] Acceptance criteria of the linked story are met
- [ ] `ruff check .` passes
- [ ] `python -m pytest` passes locally
- [ ] Tests added/updated (Test Plan IDs where applicable)
- [ ] No secrets, passwords or `.env` files committed (SEC-15)
- [ ] Inputs validated on the server and queries parameterized (SEC-06, SEC-07)

## Review checklist (reviewer)
- [ ] Code is readable and follows the routes → services → repositories layering
- [ ] Acceptance criteria verified against the running app or tests
- [ ] CI is green
- [ ] No sensitive data in logs or error messages (SEC-12)
