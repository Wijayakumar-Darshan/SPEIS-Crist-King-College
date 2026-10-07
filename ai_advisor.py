"""ai_advisor.py – Career readiness and study suggestion engine."""
from statistics import mean


def average_marks_by_subject(marks_rows):
    buckets = {}
    for r in marks_rows:
        buckets.setdefault(r["subject_name"], []).append(r["marks"])
    return {k: round(mean(v), 2) for k, v in buckets.items()}


def build_improvement_plan(avg_marks: dict, cutoffs: list):
    plan = []
    for c in cutoffs:
        subj    = c["subject_name"]
        cutoff  = c["min_marks"]
        current = avg_marks.get(subj, 0.0)
        gap     = round(cutoff - current, 2)
        imp_pct = round(max(gap, 0) / cutoff * 100, 1) if cutoff > 0 else 0.0

        if gap <= 0:
            status  = "On Track"
            message = f"Meeting the {subj} requirement ({current}/{cutoff})."
        elif gap <= 5:
            status  = "Almost There"
            message = f"Only {gap} marks away in {subj}. A little revision will close the gap."
        elif gap <= 15:
            status  = "Needs Improvement"
            message = f"Needs ~{imp_pct}% improvement in {subj} (now {current}, target {cutoff})."
        else:
            status  = "Critical"
            message = f"Significant gap in {subj}: needs ~{imp_pct}% improvement to reach {cutoff}. Consider tutoring."

        plan.append({"subject": subj, "current": current, "cutoff": cutoff,
                     "gap": gap, "improvement_pct": imp_pct,
                     "status": status, "message": message})
    return plan


def overall_summary(plan):
    if not plan:
        return "No cutoff data available for this career yet."
    avg_gap = round(mean([p["improvement_pct"] for p in plan]), 1)
    on_track = [p for p in plan if p["status"] in ("On Track", "Almost There")]
    weakest  = max(plan, key=lambda p: p["improvement_pct"])
    if not [p for p in plan if p["status"] in ("Critical", "Needs Improvement")]:
        return f"Great progress! On track in all {len(plan)} subjects for this career path."
    return (f"Average {avg_gap}% improvement needed overall. "
            f"Weakest area: {weakest['subject']} (~{weakest['improvement_pct']}% to go). "
            f"{len(on_track)}/{len(plan)} subjects already on track.")


def readiness_score(plan):
    """0-100 score: how ready is the student for their career?"""
    if not plan: return 0
    scores = []
    for p in plan:
        if p["cutoff"] > 0:
            scores.append(min(100.0, p["current"] / p["cutoff"] * 100))
    return round(mean(scores), 1) if scores else 0


def study_suggestions(plan):
    """Return prioritised list of study tips."""
    tips = []
    critical = [p for p in plan if p["status"] == "Critical"]
    needs    = [p for p in plan if p["status"] == "Needs Improvement"]
    for p in critical:
        tips.append(f"PRIORITY: Dedicate extra sessions to {p['subject']} — {p['gap']:.1f} marks below the minimum cutoff.")
    for p in needs:
        tips.append(f"Focus on {p['subject']} — {p['gap']:.1f} marks below target.")
    if not tips:
        tips.append("You are on track for your career dream. Maintain consistency and aim higher.")
    return tips


def compare_career_progress(current_avg: dict, previous_avg: dict, cutoffs: list):
    """Compare current subject averages with the previous available year and career cutoffs."""
    rows = []
    for c in cutoffs:
        subject = c["subject_name"]
        current = float(current_avg.get(subject, 0.0))
        previous = float(previous_avg.get(subject, 0.0)) if previous_avg else 0.0
        cutoff = float(c["min_marks"])
        change = round(current - previous, 2) if subject in previous_avg else None
        gap = round(cutoff - current, 2)
        if change is None:
            trend = "New data"
        elif change > 0.5:
            trend = "Improved"
        elif change < -0.5:
            trend = "Declined"
        else:
            trend = "Stable"
        rows.append({
            "subject": subject, "current": round(current, 2),
            "previous": round(previous, 2) if subject in previous_avg else None,
            "change": change, "cutoff": round(cutoff, 2),
            "gap": gap, "trend": trend,
            "improvement_needed": round(max(gap, 0), 2),
        })
    improved = sum(1 for r in rows if r["trend"] == "Improved")
    declined = sum(1 for r in rows if r["trend"] == "Declined")
    on_target = sum(1 for r in rows if r["current"] >= r["cutoff"])
    total = len(rows)
    avg_change_values = [r["change"] for r in rows if r["change"] is not None]
    avg_change = round(mean(avg_change_values), 2) if avg_change_values else None
    return {
        "rows": rows, "improved": improved, "declined": declined,
        "on_target": on_target, "total": total, "avg_change": avg_change,
        "overall_trend": "Improving" if improved > declined else ("Declining" if declined > improved else "Stable"),
    }


def comparison_summary(comparison, career_name=""):
    if not comparison or not comparison.get("rows"):
        return "Not enough marks are available to compare career-path progress."
    c = comparison
    target = f" for {career_name}" if career_name else ""
    change_text = (f"Average subject change: {c['avg_change']:+.2f} marks."
                   if c["avg_change"] is not None else "No previous-year baseline is available.")
    return (f"Career-path progress{target}: {c['improved']} subject(s) improved, "
            f"{c['declined']} declined, and {c['on_target']}/{c['total']} meet the current career cutoffs. "
            f"{change_text}")
