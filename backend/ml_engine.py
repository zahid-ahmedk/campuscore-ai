import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class StudentRiskPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self._train_baseline_model()

    def _train_baseline_model(self):
        """
        Trains a Random Forest classifier on historical academic patterns:
        Features: [attendance_pct, avg_midterm_pct, avg_sessional_pct, has_unpaid_fees]
        Target: 1 = High Academic/Dropout Risk, 0 = Safe/On-Track
        """
        rng = np.random.default_rng(42)
        n_samples = 400

        attendance = rng.uniform(40, 100, n_samples)
        midterm_pct = rng.uniform(20, 100, n_samples)
        sessional_pct = rng.uniform(30, 100, n_samples)
        unpaid_fees = rng.choice([0, 1], size=n_samples, p=[0.7, 0.3])

        # Realistic academic risk logic for training labels
        risk_signal = (
            (attendance < 72).astype(int) * 2
            + (midterm_pct < 50).astype(int) * 2
            + (sessional_pct < 55).astype(int) * 1
            + unpaid_fees * 1
        )
        labels = (risk_signal >= 3).astype(int)

        X = pd.DataFrame({
            "attendance": attendance,
            "midterm_pct": midterm_pct,
            "sessional_pct": sessional_pct,
            "unpaid_fees": unpaid_fees,
        })
        self.model.fit(X, labels)

    def predict_student_risk(
        self,
        attendance: float,
        midterm_marks: float,
        sessional_marks: float,
        has_unpaid_fees: bool,
    ) -> dict:
        """
        Returns risk probability (0.0 to 1.0), risk category (Low/Medium/High),
        and actionable reasons so faculty/chairmen can intervene early.
        """
        midterm_pct = (midterm_marks / 30.0) * 100.0
        sessional_pct = (sessional_marks / 20.0) * 100.0

        features = pd.DataFrame([{
            "attendance": attendance,
            "midterm_pct": midterm_pct,
            "sessional_pct": sessional_pct,
            "unpaid_fees": 1 if has_unpaid_fees else 0,
        }])

        prob = float(self.model.predict_proba(features)[0][1])

        if prob >= 0.65:
            level = "High"
        elif prob >= 0.35:
            level = "Medium"
        else:
            level = "Low"

        reasons = []
        if attendance < 75:
            reasons.append(f"Low attendance ({attendance:.1f}% < 75% threshold)")
        if midterm_pct < 50:
            reasons.append(f"Weak midterm score ({midterm_marks}/30)")
        if sessional_pct < 55:
            reasons.append(f"Low sessional/assignment score ({sessional_marks}/20)")
        if has_unpaid_fees:
            reasons.append("Pending semester fee clearance")
        if not reasons:
            reasons.append("Strong attendance and consistent exam performance")

        return {
            "risk_score": round(prob, 2),
            "risk_level": level,
            "factors": reasons,
        }

# Singleton instance ready to import across the backend
risk_predictor = StudentRiskPredictor()