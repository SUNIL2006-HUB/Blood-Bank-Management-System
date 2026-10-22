# Contributing / team workflow

Work is organised by backlog story (PBI). `main` is always releasable and is only changed through pull requests.

## Flow for every story

1. Pick a PBI issue (e.g. `#5 PBI-01 — Donor Registration`).
2. Branch from an up-to-date `main`: `git checkout -b feature/pbi-01-donor-registration`
3. Implement backend **and** frontend for the story, with tests. Commit with a message like `feat(PBI-01): donor registration (#5)`.
4. Run locally: `ruff check .` and `python -m pytest`.
5. Push the branch and open a pull request into `main`. Fill in the PR template and write `Closes #5`.
6. **CI must be green** (lint, tests on Python 3.11/3.12, secret scan).
7. **At least one teammate reviews** the PR against the story's acceptance criteria. Address comments with new commits.
8. After approval, merge. The linked issue closes automatically. Delete the branch.
9. Merging to `main` triggers the CD workflow, which builds and publishes the Docker image.

## Branch protection (repo admin, Settings → Branches → Add rule for `main`)

- Require a pull request before merging, with **1 approval**
- Require review from Code Owners
- Dismiss stale approvals when new commits are pushed
- Require status checks to pass: `lint`, `test (3.11)`, `test (3.12)`, `secrets-scan`
- Require branches to be up to date before merging
- Do not allow bypassing the rules (apply to admins too)

## Conventions

- Layering: `routes` (UI) → `services` (business rules, validation) → `repositories` (SQL). No SQL outside repositories; parameterized queries only.
- Never commit credentials; use environment variables (see `.env.example`).
