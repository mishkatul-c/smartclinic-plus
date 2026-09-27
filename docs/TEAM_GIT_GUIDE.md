# Putting SmartClinic+ on GitHub so every member's work shows

The marker assesses the repository's history (20 marks for "code repository and project management"). That history
has to be real: each member should push their own modules from their own GitHub account. This takes about an hour.

## 1. Leader creates the repository (Mishkatul)
1. Create a private GitHub repo `smartclinic-plus`, add the other three members and the lecturer as collaborators.
2. Create a GitHub Project (board view) called *SmartClinic+ backlog* and import `docs/product_backlog.csv`
   (one item per row; add columns Todo / In progress / In review / Done and a Sprint field).
3. Push the scaffold only:
   `README.md, CONTRIBUTING.md, requirements.txt, .gitignore, .flake8, pytest.ini, .coveragerc, run.py,
    smartclinic/__init__.py, smartclinic/config.py, smartclinic/routes/__init__.py, smartclinic/services/__init__.py,
    tests/conftest.py, docs/team_charter.md, docs/sprint_log.md`
   ```bash
   git init && git add <files above> && git commit -m "chore: project scaffold and team charter"
   git branch -M main && git remote add origin <repo-url> && git push -u origin main
   ```
4. Settings → Branches → protect `main`: require a pull request, one approval, and the CI check.

## 2. Each member adds their own modules on a branch and opens a pull request
Copy your files from this package into your clone, then:
```bash
git checkout -b feature/<your-area>
git add <your files>
git commit -m "feat(<area>): <what it does> (FR-xx)"
git push -u origin feature/<your-area>
```
Open a PR using the template, link the backlog items, and ask another member to review. Split your work into
several small commits and PRs (one per backlog item) rather than one huge commit.

| Member | Suggested order of PRs |
|---|---|
| Maruf | 1 `db.py` + `schema.sql` + `security.py` → 2 `routes/auth.py` + `test_security.py` → 3 `ehr.py`, `labs.py`, `routes/clinical.py` → 4 `docs/schema_postgresql.sql` |
| Mishkatul | 1 `booking.py` + `test_booking.py` → 2 `test_concurrency.py` → 3 `notifications.py` → 4 `routes/patient.py` |
| Humayra | 1 `templates/` + `static/` → 2 `prescriptions.py` → 3 `engagement.py` → 4 `test_clinical.py` + `docs/tools/` |
| Mukit | 1 `.github/` (CI, templates, CODEOWNERS) → 2 `queue.py` + `test_queue.py` → 3 `tasks.py`, `analytics.py`, `routes/admin.py`, `test_analytics.py` → 4 `test_journey.py`, `seed.py`, `Dockerfile`, `docs/defect_log.md` |

Because modules depend on each other, merge in this order: Maruf 1 → Mishkatul 1–2 → Maruf 2–3 → the rest.

## 3. Show project management activity
Move board cards as PRs merge, close issues from PRs (`Closes #7`), tag a release at the end of each sprint
(`git tag v0.1-sprint1 && git push --tags`), and fill in `docs/sprint_log.md` after each review. Raise DEF-01 as an
issue and fix it through a PR so the defect workflow is visible.
