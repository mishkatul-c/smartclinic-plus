# SmartClinic+ Team Charter

| Member | ID | Scrum role | Technical ownership | Report ownership (A3) | Presentation segment (A4) |
|---|---|---|---|---|---|
| Mishkatul Abedin Chowdhury | K241095 | Team Leader & Scrum Master | Booking, concurrency control, notifications | Introduction, methodology, project management, timeline, budget, conclusion | Opening, problem, methodology, timeline, budget (slides 1–6) |
| Humayra Nushrat | K241086 | Product Owner & UX lead | Hi-fi prototype UI, e-prescription, engagement, AHP tool | Requirements elicitation, AHP prioritisation, use cases, prototype, ethics | Elicitation, AHP, use cases, prototype (slides 7–10) |
| Md Mahamudul Amin Maruf | K241071 | Solution Architect & Security lead | Data layer, schema, RBAC, encryption, EHR, labs | Architecture, ERD, component design, sequence diagrams, modern tools | Architecture, concurrency, security, live demo (slides 11–14) |
| Md Muhi Uddin Mukit | K240999 | QA & DevOps lead | CI pipeline, smart queue, tasks, analytics, system tests | Test plan, QA results, process metrics and capability, repository evidence | Tools, repository, testing, metrics, recommendations (slides 15–18) |

Each member carries an equal share (25%) of design, code, documentation and presentation work.

## Decision-making procedure
1. Proposals are raised in the team channel or at stand-up, with the requirement id they affect.
2. Discussion is time-boxed to one meeting. Aim for consensus.
3. If no consensus: majority vote. On a 2–2 tie, the Product Owner decides scope questions and the Architect decides
   technical questions; the Scrum Master records the decision and the reasons in the sprint log.
4. Any decision can be reopened at the next sprint review if new evidence appears.

## Conflict resolution
Raise it early and privately with the person; if unresolved, bring it to the retrospective; if still unresolved,
the Scrum Master facilitates a compromise and, as a last resort, consults the unit lecturer.

## Cadence
Sprint planning (Monday, 45 min) · stand-up (Mon/Wed/Fri, 10 min, online) · sprint review + retrospective
(every second Friday, 60 min). Minutes are kept in `docs/sprint_log.md`.

## Working agreements
Every change goes through a pull request reviewed by the module owner. Nobody merges their own PR.
Workload is checked at every retrospective against story points completed per person.
