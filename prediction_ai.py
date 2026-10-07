"""Lightweight, explainable school and student outcome forecasting.

No external ML framework is required.  Forecasts combine:
1) historical official exam pass rates (A/B/C/S = pass, W = fail), and
2) current/internal assessment performance when available.

The output is an estimate, not an official examination prediction.
"""
import numpy as np

RISK_COLORS = {"Strong": "#2fa66b", "On Track": "#4C72B0",
               "Warning": "#f0a500", "Critical": "#e03c3c", "No Data": "#aaaaaa"}
RISK_LABELS = {"Strong": "Excellent", "On Track": "Good",
               "Warning": "Needs Improvement", "Critical": "At Risk", "No Data": "No Data"}
PASS_GRADES = {"A", "B", "C", "S"}
FAIL_GRADES = {"W"}
GRADE_POINTS = {"A": 4.0, "B": 3.0, "C": 2.0, "S": 1.0, "W": 0.0}


def _classify(mark):
    if mark is None: return "No Data"
    if mark >= 75: return "Strong"
    if mark >= 60: return "On Track"
    if mark >= 45: return "Warning"
    return "Critical"


def predict_grade_performance(grade_year_rows, predict_years=2):
    by_grade = {}
    for r in grade_year_rows:
        by_grade.setdefault(r["grade"], []).append(r)
    results = []
    for grade in range(6, 14):
        rows = sorted(by_grade.get(grade, []), key=lambda r: r["year"])
        dp = len(rows)
        if dp == 0:
            results.append({"grade": grade, "data_points": 0, "years_seen": [],
                            "historical": [], "current_avg": None, "predicted_avg": None,
                            "trend_slope": None, "status": "No Data", "confidence": "None",
                            "message": f"Grade {grade}: No data yet.", "projection_series": []})
            continue
        years = [r["year"] for r in rows]; marks = [r["avg_marks"] for r in rows]
        cur = round(marks[-1], 2)
        if dp == 1:
            pred, slope, conf = cur, 0.0, "Low"
            proj = [(years[0], cur), (years[0] + 1, cur)]
        else:
            coef = np.polyfit(years, marks, 1); slope = round(float(coef[0]), 3)
            conf = "High" if dp >= 5 else ("Medium" if dp >= 3 else "Low")
            ny = years[-1] + 1
            proj = [(y, round(max(0, min(100, float(np.polyval(coef, y)))), 2))
                    for y in range(min(years), ny + predict_years + 1)]
            pred = round(max(0, min(100, float(np.polyval(coef, ny)))), 2)
        status = _classify(pred)
        trend = "improving" if slope > 0.5 else ("declining" if slope < -0.5 else "stable")
        arrow = "+" if slope >= 0 else ""
        msg = f"Grade {grade} is {trend} ({arrow}{slope:.1f} marks/yr). Predicted avg: {pred}. {RISK_LABELS.get(status,status)}."
        results.append({"grade": grade, "data_points": dp, "years_seen": years,
                        "historical": list(zip(years, [round(m,2) for m in marks])),
                        "current_avg": cur, "predicted_avg": pred, "trend_slope": slope,
                        "status": status, "confidence": conf, "message": msg,
                        "projection_series": proj})
    return results


def ol_risk_summary(results):
    ol = [r for r in results if r["grade"] in (10, 11)]
    if not ol or all(r["data_points"] == 0 for r in ol):
        return "No O/L data yet (Grade 10 & 11). Add marks to enable O/L predictions."
    parts = []
    for r in ol:
        if r["data_points"] == 0: parts.append(f"Grade {r['grade']}: No data")
        else: parts.append(f"Grade {r['grade']}: predicted {r['predicted_avg']} - {RISK_LABELS.get(r['status'],r['status'])} ({r['confidence']} confidence)")
    return "O/L Outlook: " + " | ".join(parts)


def _historical_pass_rate(result_rows):
    if not result_rows:
        return None, 0
    passed = sum(1 for r in result_rows if str(r.get("result_grade", "")).upper() in PASS_GRADES)
    return round(100.0 * passed / len(result_rows), 2), len(result_rows)


def _internal_pass_signal(mark_rows):
    if not mark_rows:
        return None
    vals = [float(r["marks"]) for r in mark_rows if r.get("marks") is not None]
    if not vals:
        return None
    # 35 is the internal pass boundary used by SPEIS's A/B/C/S/W conversion.
    return round(100.0 * sum(v >= 35 for v in vals) / len(vals), 2)


def forecast_exam_pass_rate(historical_results, current_mark_rows=None, target_year=None):
    """Return a conservative school/student pass-rate estimate.

    Historical official results are weighted 70% and current/internal marks 30%.
    With no official history, the internal signal is used alone and confidence is Low.
    """
    hist_rate, n = _historical_pass_rate(historical_results)
    internal_rate = _internal_pass_signal(current_mark_rows or [])
    if hist_rate is None and internal_rate is None:
        return {"pass_rate": None, "confidence": "None", "historical_rate": None,
                "internal_signal": None, "sample_size": 0, "target_year": target_year,
                "method": "No supporting data"}
    if hist_rate is not None and internal_rate is not None:
        rate = 0.70 * hist_rate + 0.30 * internal_rate
        confidence = "High" if n >= 50 else ("Medium" if n >= 15 else "Low")
    elif hist_rate is not None:
        rate, confidence = hist_rate, ("High" if n >= 50 else ("Medium" if n >= 15 else "Low"))
    else:
        rate, confidence = internal_rate, "Low"
    return {"pass_rate": round(max(0, min(100, rate)), 1),
            "confidence": confidence, "historical_rate": hist_rate,
            "internal_signal": internal_rate, "sample_size": n,
            "target_year": target_year,
            "method": "70% historical official results + 30% current internal pass signal" if hist_rate is not None and internal_rate is not None else "Historical official results" if hist_rate is not None else "Current internal assessment signal"}


def student_exam_forecast(historical_results, mark_rows, target_year=None):
    """Student-level forecast using official history plus current marks."""
    base = forecast_exam_pass_rate(historical_results, mark_rows, target_year)
    if base["pass_rate"] is None:
        return base
    avg = np.mean([float(r["marks"]) for r in mark_rows]) if mark_rows else None
    adjustment = 0.0 if avg is None else max(-12.0, min(12.0, (avg - 55.0) * 0.35))
    rate = round(max(0, min(100, base["pass_rate"] + adjustment)), 1)
    base.update({"pass_rate": rate, "student_avg": round(float(avg), 2) if avg is not None else None})
    return base
