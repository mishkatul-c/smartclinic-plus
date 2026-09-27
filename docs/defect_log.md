# Defect log

| ID | Found by | Severity | Summary | Root cause | Fix | Verified by |
|---|---|---|---|---|---|---|
| DEF-01 | TC-25 (security test) | High | A POST with no CSRF token was accepted when the session had no token yet | `request.form.get("_csrf") != session.get("_csrf")` compared `None` to `None`, which is equal | Require a stored token and compare with `secrets.compare_digest` | TC-25 now passes; regression test kept in suite |
