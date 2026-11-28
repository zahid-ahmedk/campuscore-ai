"""Academic early-warning model.

A Random Forest scores each student on attendance, midterm %, sessional % and
fee clearance. Until real outcome data (fail/drop-out records) is available the
model is bootstrapped from a synthetic baseline, so its output is a screening
aid for faculty, not a validated prediction. Replace `_bootstrap_data` with
historical records and call `train()` to retrain.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = Path(__file__).resolve().parent / "risk_model.joblib"
FEATURES = ["attendance", "midterm_pct", "sessional_pct", "unpaid_fees"]


def _bootstrap_data(n: int = 2000) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(42)
    X = pd.DataFrame({
        "attendance": rng.uniform(40, 100, n),
        "midterm_pct": rng.uniform(15, 100, n),
        "sessional_pct": rng.uniform(25, 100, n),
        "unpaid_fees": rng.choice([0, 1], n, p=[0.7, 0.3]),
    })
    signal = (
        2 * (X.attendance < 75) + 2 * (X.midterm_pct < 50)
        + (X.sessional_pct < 55) + X.unpaid_fees
        + rng.normal(0, 0.6, n)  # label noise so the forest learns a soft boundary
    )
    return X, (signal >= 3).astype(int).to_numpy()


class StudentRiskPredictor:
    def __init__(self):
        self.model: RandomForestClassifier | None = None

    def train(self, X: pd.DataFrame | None = None, y=None) -> None:
        if X is None:
            X, y = _bootstrap_data()
        self.model = RandomForestClassifier(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=-1)
        self.model.fit(X[FEATURES], y)
        joblib.dump(self.model, MODEL_PATH)

    def _ensure(self) -> RandomForestClassifier:
        if self.model is None:
            if MODEL_PATH.exists():
                self.model = joblib.load(MODEL_PATH)
            else:
                self.train()
        return self.model

    @staticmethod
    def _level(p: float) -> str:
        return "High" if p >= 0.65 else "Medium" if p >= 0.35 else "Low"

    def predict_batch(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Vectorised scoring for many students at once (used for 100k+ recompute)."""
        probs = self._ensure().predict_proba(frame[FEATURES])[:, 1]
        out = pd.DataFrame({"risk_score": probs.round(2)})
        out["risk_level"] = [self._level(p) for p in probs]
        return out

    def predict_student_risk(self, attendance: float, midterm_marks: float,
                             sessional_marks: float, has_unpaid_fees: bool) -> dict:
        midterm_pct = midterm_marks / 30.0 * 100.0
        sessional_pct = sessional_marks / 20.0 * 100.0
        frame = pd.DataFrame([{
            "attendance": attendance, "midterm_pct": midterm_pct,
            "sessional_pct": sessional_pct, "unpaid_fees": int(has_unpaid_fees),
        }])
        prob = float(self._ensure().predict_proba(frame[FEATURES])[0][1])

        factors = []
        if attendance < 75:
            factors.append(f"Attendance {attendance:.1f}% is below the 75% requirement")
        if midterm_pct < 50:
            factors.append(f"Midterm score {midterm_marks:g}/30 is below 50%")
        if sessional_pct < 55:
            factors.append(f"Sessional score {sessional_marks:g}/20 is below 55%")
        if has_unpaid_fees:
            factors.append("Semester fee not fully cleared")
        if not factors:
            factors.append("Attendance and assessment results are on track")
        return {"risk_score": round(prob, 2), "risk_level": self._level(prob), "factors": factors}


risk_predictor = StudentRiskPredictor()
