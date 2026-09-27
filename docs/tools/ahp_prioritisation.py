"""AHP requirement prioritisation for SmartClinic+ (run: python docs/tools/ahp_prioritisation.py).

Step 1  Pairwise-compare the five criteria on Saaty's 1-9 scale; derive weights from the
        principal eigenvector and check the consistency ratio (CR < 0.10 is acceptable).
Step 2  Rate every requirement 1-9 against each criterion (Saaty's absolute-measurement
        / ratings mode, which scales to many alternatives without n(n-1)/2 comparisons).
Step 3  Weighted score -> rank -> MoSCoW release band.
"""
import csv
import sys

import numpy as np

CRITERIA = ["Patient safety", "Security & privacy", "Operational value",
            "Technical dependency", "Delivery effort (inverse)"]

# A[i][j] = importance of criterion i over j. Agreed by the team in the Sprint 1 workshop.
A = np.array([
    [1,   2,   3,   3,   5],
    [1/2, 1,   2,   3,   4],
    [1/3, 1/2, 1,   2,   3],
    [1/3, 1/3, 1/2, 1,   2],
    [1/5, 1/4, 1/3, 1/2, 1],
])
RI = {3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32}

REQS = [  # id, name, ratings per criterion (1-9)
    ("FR-07", "Electronic health records (EHR)", [9, 9, 8, 8, 4]),
    ("NFR-01", "Concurrency: no double bookings", [8, 7, 9, 9, 6]),
    ("FR-09", "Role-based data privacy controls", [8, 9, 6, 9, 5]),
    ("FR-05", "E-prescription with allergy check", [9, 7, 7, 5, 5]),
    ("FR-01", "Online booking, reschedule, cancel", [7, 6, 9, 9, 6]),
    ("FR-04", "Doctor dashboard", [7, 5, 8, 6, 6]),
    ("FR-08", "Lab and test integration", [7, 6, 6, 4, 5]),
    ("FR-02", "Smart queue", [6, 3, 8, 5, 6]),
    ("FR-03", "Automated SMS/email notifications", [4, 4, 7, 4, 7]),
    ("FR-06", "Task assignment", [5, 3, 6, 3, 8]),
    ("FR-10", "Operational dashboard", [2, 2, 7, 2, 6]),
    ("FR-11", "Predictive staffing insights", [2, 2, 6, 1, 3]),
    ("FR-12", "Patient engagement and loyalty", [1, 2, 4, 1, 7]),
]


def weights(matrix):
    vals, vecs = np.linalg.eig(matrix)
    k = int(np.argmax(vals.real))
    w = np.abs(vecs[:, k].real)
    w = w / w.sum()
    lam = vals[k].real
    n = len(matrix)
    ci = (lam - n) / (n - 1)
    return w, lam, ci, ci / RI[n]


def band(rank):
    return "Must" if rank <= 6 else "Should" if rank <= 9 else "Could"


def main(out_csv=None):
    w, lam, ci, cr = weights(A)
    print("Criterion weights:")
    for c, x in zip(CRITERIA, w):
        print(f"  {c:<28}{x:.3f}")
    print(f"lambda_max={lam:.3f}  CI={ci:.3f}  CR={cr:.3f}  ({'consistent' if cr < 0.1 else 'REVISE'})")
    scored = sorted(((rid, name, float(np.dot(r, w))) for rid, name, r in REQS),
                    key=lambda t: -t[2])
    rows = [(i + 1, rid, name, round(s, 2), band(i + 1)) for i, (rid, name, s) in enumerate(scored)]
    for r in rows:
        print("  ", r)
    if out_csv:
        with open(out_csv, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(["rank", "id", "requirement", "ahp_score", "moscow"])
            wr.writerows(rows)
    return w, cr, rows


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
