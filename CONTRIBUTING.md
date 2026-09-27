# Contributing to SmartClinic+

## Branching (GitHub Flow)
`main` is protected: no direct pushes, at least one approving review from the CODEOWNER, and a green CI run.
Create one short-lived branch per backlog item: `feature/FR-05-allergy-check`, `fix/DEF-01-csrf`, `test/TC-08-race`.

## Commits
Conventional Commits: `feat(booking): prevent double booking with partial unique index`,
`test(queue): late arrivals go behind on-time patients`, `fix(security): reject POST without CSRF token`.
Reference the requirement id in the body.

## Definition of Ready
A story has a requirement id, AHP score, acceptance criteria in Given/When/Then form and an estimate.

## Definition of Done
Acceptance criteria met; unit tests written first or alongside; `flake8` and `pytest` green in CI; coverage stays at or
above 80%; RBAC decorator on every new route; clinical text encrypted; reviewed and merged; demoed at sprint review.

## Local checks before opening a PR
```bash
flake8 smartclinic tests docs/tools
pytest --cov=smartclinic
```
