"""pdf_report.py – PDF generation with Unicode (NotoSansSinhala) font."""
import os, tempfile, datetime
from fpdf import FPDF
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import prediction_ai as pai

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansSinhala.ttf")
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _s(v): return "" if v is None else str(v)


def _fig_to_tmp(fig):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return tmp.name


class PDF(FPDF):
    def __init__(self):
        super().__init__()
        f = FONT if os.path.exists(FONT) else FALLBACK
        self.add_font("N", "",  f)
        self.add_font("N", "B", f)
        self.set_auto_page_break(True, 15)

    def header(self):
        self.set_font("N", "B", 12)
        self.cell(0, 9, "SPEIS - Student Performance Report", align="C",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_font("N", "", 8)
        self.cell(0, 6, f"Generated: {datetime.date.today().strftime('%d %B %Y')}",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-13)
        self.set_font("N", "", 8)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def section(self, title):
        self.set_font("N", "B", 11)
        self.set_fill_color(76, 114, 176)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kv(self, label, value, w1=55, w2=115):
        self.set_font("N", "B", 10)
        self.cell(w1, 7, f"{label}:", border="B")
        self.set_font("N", "", 10)
        self.cell(w2, 7, _s(value), border="B", new_x="LMARGIN", new_y="NEXT")

    def table_header(self, cols):
        """cols: list of (label, width, align)"""
        self.set_font("N", "B", 9)
        self.set_fill_color(230, 235, 245)
        for lbl, w, align in cols:
            self.cell(w, 7, lbl, border=1, align=align, fill=True)
        self.ln()

    def table_row(self, vals, cols, fill=False):
        self.set_font("N", "", 9)
        if fill:
            self.set_fill_color(245, 247, 252)
        for (_, w, align), val in zip(cols, vals):
            self.cell(w, 7, _s(val), border=1, align=align, fill=fill)
        self.ln()

    def img(self, path, w=180):
        self.image(path, x=15, w=w)
        os.unlink(path)
        self.ln(3)


# ── Chart helpers ─────────────────────────────────────────────────────────────
def _bar_vs_cutoff(labels, current, cutoffs, title):
    fig, ax = plt.subplots(figsize=(6, 3.2))
    x = range(len(labels)); w = 0.35
    ax.bar([i-w/2 for i in x], current, w, label="Student",  color="#4C72B0")
    ax.bar([i+w/2 for i in x], cutoffs,  w, label="Cutoff",  color="#DD8452")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
    ax.set_ylim(0, 100); ax.set_title(title, fontsize=9); ax.legend(fontsize=7)
    fig.tight_layout()
    return _fig_to_tmp(fig)


def _subj_bar(subject_avgs: dict, title: str):
    fig, ax = plt.subplots(figsize=(6, max(2.5, len(subject_avgs) * 0.4)))
    ax.barh(list(subject_avgs.keys()), list(subject_avgs.values()), color="#4C72B0")
    ax.set_xlim(0, 100); ax.set_title(title, fontsize=9)
    fig.tight_layout()
    return _fig_to_tmp(fig)


# ── Student term report ───────────────────────────────────────────────────────
def student_term_report(student, term, year, marks_rows, ai_plan=None, ai_summary=None, readiness=None):
    pdf = PDF(); pdf.add_page()

    pdf.section("Student Information")
    pdf.kv("Name",          student.get("full_name"))
    pdf.kv("Reg No",        student.get("reg_no"))
    pdf.kv("Grade",         f"{student.get('grade')}{student.get('class_section','')}")
    pdf.kv("Term / Year",   f"Term {term}  –  {year}")
    pdf.kv("Career Dream",  student.get("career_name") or "Not set")
    pdf.ln(3)

    pdf.section("Term Marks")
    cols = [("Subject", 100, "L"), ("Marks", 40, "C"), ("Grade", 30, "C")]
    pdf.table_header(cols)
    total = 0
    for i, r in enumerate(marks_rows):
        m = r["marks"]
        g = "A" if m >= 75 else ("B" if m >= 65 else ("C" if m >= 55 else ("S" if m >= 35 else "W")))
        pdf.table_row([r["subject_name"], str(m), g], cols, fill=(i % 2 == 0))
        total += m
    if marks_rows:
        avg = round(total / len(marks_rows), 2)
        pdf.set_font("N", "B", 10)
        pdf.cell(100, 7, "Average", border=1)
        pdf.cell(40,  7, str(avg), border=1, align="C")
        pdf.cell(30,  7, "", border=1); pdf.ln()

    if ai_plan:
        pdf.ln(4)
        pdf.section("AI Career-Readiness Insight")
        if ai_summary:
            pdf.set_font("N", "", 10)
            pdf.multi_cell(0, 6, _s(ai_summary))
        if readiness is not None:
            pdf.set_font("N", "B", 10)
            pdf.cell(0, 7, f"Readiness Score: {readiness}/100", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        path = _bar_vs_cutoff([p["subject"] for p in ai_plan],
                               [p["current"] for p in ai_plan],
                               [p["cutoff"]  for p in ai_plan],
                               "Marks vs Career Cutoff")
        pdf.img(path)

        cols2 = [("Subject", 65, "L"), ("Marks", 25, "C"),
                 ("Target", 25, "C"), ("Gap", 25, "C"), ("Status", 30, "C")]
        pdf.table_header(cols2)
        for i, p in enumerate(ai_plan):
            pdf.table_row([p["subject"], str(p["current"]), str(p["cutoff"]),
                           str(p["gap"]), p["status"]], cols2, fill=(i%2==0))

    return bytes(pdf.output())


# ── Student year summary ──────────────────────────────────────────────────────
def student_year_report(student, year, pivot_rows, overall_avg, ai_plan=None, ai_summary=None):
    pdf = PDF(); pdf.add_page()

    pdf.section("End-of-Year Summary")
    pdf.kv("Name",  student.get("full_name"))
    pdf.kv("Reg No",student.get("reg_no"))
    pdf.kv("Grade", f"{student.get('grade')}{student.get('class_section','')}")
    pdf.kv("Year",  year); pdf.ln(3)

    pdf.section("Subject Averages Across 3 Terms")
    cols = [("Subject",60,"L"),("Term 1",28,"C"),("Term 2",28,"C"),("Term 3",28,"C"),("Avg",28,"C")]
    pdf.table_header(cols)
    for i, r in enumerate(pivot_rows):
        pdf.table_row([r["subject_name"], r.get("term1","-"),
                       r.get("term2","-"), r.get("term3","-"), r["average"]],
                      cols, fill=(i%2==0))
    pdf.set_font("N","B",10)
    pdf.cell(144,7,"Overall Average",border=1)
    pdf.cell(28, 7,str(overall_avg),border=1,align="C"); pdf.ln()

    if ai_plan:
        pdf.ln(4); pdf.section("AI Career-Readiness")
        if ai_summary:
            pdf.set_font("N","",10); pdf.multi_cell(0,6,_s(ai_summary))
        path = _bar_vs_cutoff([p["subject"] for p in ai_plan],
                               [p["current"] for p in ai_plan],
                               [p["cutoff"]  for p in ai_plan],
                               "Yearly Average vs Career Cutoff")
        pdf.img(path)

    return bytes(pdf.output())


# ── Class performance report ──────────────────────────────────────────────────
def class_report(grade, cls, year, subj_rows, class_avg, student_count):
    pdf = PDF(); pdf.add_page()
    pdf.section(f"Class Report – Grade {grade}{cls}  ({year})")
    pdf.kv("Grade / Class", f"{grade}{cls}")
    pdf.kv("Year",          year)
    pdf.kv("Students",      student_count)
    pdf.kv("Class Average", round(class_avg, 2))
    pdf.ln(3)

    if subj_rows:
        avgs = {r["subject_name"]: round(r["avg_marks"], 2) for r in subj_rows}
        pdf.img(_subj_bar(avgs, f"Grade {grade}{cls} Subject Averages"))

        cols = [("Subject",100,"L"),("Avg Marks",40,"C"),("Students",30,"C")]
        pdf.table_header(cols)
        for i, r in enumerate(subj_rows):
            pdf.table_row([r["subject_name"], round(r["avg_marks"],2), r["n"]], cols, fill=(i%2==0))

    return bytes(pdf.output())


# ── AI prediction report ──────────────────────────────────────────────────────
def prediction_report(results, ol_summary):
    pdf = PDF(); pdf.add_page()
    pdf.section("AI Grade Performance Prediction")
    pdf.set_font("N","",10); pdf.multi_cell(0,6,_s(ol_summary)); pdf.ln(3)

    # Bar chart
    labels = [f"Gr {r['grade']}" for r in results]
    cur    = [r["current_avg"]   or 0 for r in results]
    pred   = [r["predicted_avg"] or 0 for r in results]
    colors = [pai.RISK_COLORS.get(r["status"],"#aaa") for r in results]
    fig, ax = plt.subplots(figsize=(8,4))
    x = np.arange(8); w = 0.38
    ax.bar(x-w/2, cur,  w, label="Current",   color="#4C72B0", alpha=0.85)
    ax.bar(x+w/2, pred, w, label="Predicted", color=colors,    alpha=0.85)
    for yv,col,ls,lb in [(75,"#2fa66b","--","Strong"),(60,"#4C72B0",":","On Track"),(45,"#f0a500","-.","Warning")]:
        ax.axhline(yv,color=col,linestyle=ls,linewidth=1,label=lb)
    ax.set_xticks(x); ax.set_xticklabels(labels,fontsize=8)
    ax.set_ylim(0,100); ax.legend(fontsize=7,loc="lower right")
    fig.tight_layout()
    pdf.img(_fig_to_tmp(fig))

    # Trend lines
    with_data = [r for r in results if r["data_points"]>0]
    if with_data:
        fig2, ax2 = plt.subplots(figsize=(8,4))
        cl = plt.cm.tab10.colors
        for i,r in enumerate(with_data):
            c = cl[i%len(cl)]
            hy=[h[0] for h in r["historical"]]; hm=[h[1] for h in r["historical"]]
            py=[p[0] for p in r["projection_series"]]; pm=[p[1] for p in r["projection_series"]]
            ax2.scatter(hy,hm,color=c,s=30,zorder=3)
            if len(py)>1:
                ax2.plot(py,pm,color=c,linewidth=1.8,
                         linestyle="--" if r["data_points"]==1 else "-",
                         label=f"Gr {r['grade']}")
        ax2.set_ylim(0,100); ax2.set_xlabel("Year"); ax2.set_ylabel("Avg Marks")
        ax2.legend(fontsize=7,ncol=4,loc="lower right"); fig2.tight_layout()
        pdf.add_page(); pdf.section("Grade Trend Lines (Historical + Projected)")
        pdf.img(_fig_to_tmp(fig2))

    # Detail table
    pdf.add_page(); pdf.section("Grade-by-Grade Details")
    cols = [("Grade",18,"C"),("Yrs",18,"C"),("Current",28,"C"),
            ("Predicted",28,"C"),("Trend",25,"C"),("Status",30,"C"),("Confidence",23,"C")]
    pdf.table_header(cols)
    for i,r in enumerate(results):
        pdf.table_row([r["grade"],r["data_points"],r["current_avg"] or "-",
                       r["predicted_avg"] or "-",r["trend_slope"] or "-",
                       r["status"],r["confidence"]], cols, fill=(i%2==0))
    pdf.ln(3); pdf.section("AI Insights by Grade")
    pdf.set_font("N","",9)
    for r in with_data:
        pdf.multi_cell(0,6,_s(f"  Grade {r['grade']}: {r['message']}")); pdf.ln(1)

    return bytes(pdf.output())

# ── Student performance chart report ──────────────────────────────────────────
def student_performance_report(student, year, marks_rows):
    pdf = PDF(); pdf.add_page()
    pdf.section("Student Performance Chart")
    pdf.kv("Name", student.get("full_name")); pdf.kv("Reg No", student.get("reg_no"))
    pdf.kv("Grade", f"{student.get('grade')}{student.get('class_section','')}" ); pdf.kv("Year", year)
    avgs = {}
    for r in marks_rows:
        avgs.setdefault(r["subject_name"], []).append(float(r["marks"]))
    avgs = {k: round(sum(v)/len(v),2) for k,v in avgs.items()}
    if avgs:
        pdf.section("Subject Average Chart")
        pdf.img(_subj_bar(avgs, f"{student.get('full_name','Student')} – {year}"))
        cols=[("Subject",100,"L"),("Average",40,"C"),("Grade",30,"C")]
        pdf.table_header(cols)
        for i,(name,avg) in enumerate(avgs.items()):
            g = "A" if avg>=75 else ("B" if avg>=65 else ("C" if avg>=55 else ("S" if avg>=35 else "W")))
            pdf.table_row([name,avg,g],cols,fill=(i%2==0))
    terms={}
    for r in marks_rows: terms.setdefault(r["term"],[]).append(float(r["marks"]))
    if terms:
        labels=[f"Term {k}" for k in sorted(terms)]; vals=[round(sum(terms[k])/len(terms[k]),2) for k in sorted(terms)]
        fig,ax=plt.subplots(figsize=(6,3)); ax.bar(labels,vals); ax.set_ylim(0,100); ax.set_ylabel("Average"); ax.set_title("Term Average Trend"); fig.tight_layout()
        pdf.section("Term Trend"); pdf.img(_fig_to_tmp(fig))
    return bytes(pdf.output())


def outcome_forecast_report(student, ol_forecast=None, al_forecast=None, ol_stats=None, al_stats=None):
    pdf=PDF(); pdf.add_page(); pdf.section("Exam Outcome Forecast")
    pdf.kv("Name",student.get("full_name") or "School-wide")
    pdf.kv("Reg No",student.get("reg_no") or "All Students")
    pdf.kv("Grade",f"{student.get('grade')}{student.get('class_section','')}" if student.get('grade') else "All Grades")
    for title, forecast, stats in (("O/L Forecast",ol_forecast,ol_stats),("A/L Forecast",al_forecast,al_stats)):
        pdf.ln(3); pdf.section(title)
        if forecast and forecast.get("pass_rate") is not None:
            pdf.kv("Estimated Pass Rate",f"{forecast['pass_rate']}%")
            pdf.kv("Confidence",forecast.get("confidence")); pdf.kv("Method",forecast.get("method"))
        else: pdf.kv("Status","Insufficient data")
        if stats:
            pdf.kv("Historical Pass Rate", f"{stats.get('pass_rate')}%" if stats.get('pass_rate') is not None else "-")
            pdf.kv("Historical Results", stats.get("total",0))
    pdf.ln(4); pdf.set_font("N","",9)
    pdf.multi_cell(0,6,"This is an internal planning estimate based on available school data. It is not an official examination result or guarantee.")
    return bytes(pdf.output())


def career_progress_report(student, career_name, current_year, comparison):
    """PDF report for career-path progress, comparison and improvement priorities."""
    pdf = PDF(); pdf.add_page()
    pdf.section("AI Career-Path Progress & Improvement")
    pdf.kv("Name", student.get("full_name") or "School-wide")
    pdf.kv("Reg No", student.get("reg_no") or "All Students")
    pdf.kv("Grade", f"{student.get('grade')}{student.get('class_section','')}" if student.get("grade") else "School-wide")
    pdf.kv("Career Path", career_name or "Not set")
    pdf.kv("Current Year", current_year)
    pdf.ln(3)

    if not comparison or not comparison.get("rows"):
        pdf.set_font("N", "", 10)
        pdf.multi_cell(0, 6, "Not enough marks are available to create a career-path comparison.")
        return bytes(pdf.output())

    avg_change = comparison.get("avg_change")
    pdf.section("Progress Summary")
    pdf.kv("Overall Trend", comparison.get("overall_trend"))
    pdf.kv("Improved Subjects", comparison.get("improved"))
    pdf.kv("Declined Subjects", comparison.get("declined"))
    pdf.kv("At/Above Cutoff", f"{comparison.get('on_target')}/{comparison.get('total')}")
    pdf.kv("Average Change", f"{avg_change:+.2f} marks" if avg_change is not None else "No previous baseline")
    pdf.ln(3)

    rows = comparison["rows"]
    labels = [r["subject"] for r in rows]
    current = [r["current"] for r in rows]
    previous = [r["previous"] if r["previous"] is not None else 0 for r in rows]
    cutoffs = [r["cutoff"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, max(3, len(rows) * 0.38)))
    x = np.arange(len(labels)); w = 0.27
    ax.barh(x-w, previous, w, label="Previous")
    ax.barh(x, current, w, label="Current")
    ax.barh(x+w, cutoffs, w, label="Career Cutoff")
    ax.set_yticks(x); ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlim(0, 100); ax.set_xlabel("Marks"); ax.legend(fontsize=7)
    ax.set_title("Previous vs Current vs Career Cutoff")
    fig.tight_layout(); pdf.img(_fig_to_tmp(fig))

    pdf.section("Subject Comparison & Improvement")
    cols = [("Subject", 53, "L"), ("Previous", 25, "C"), ("Current", 25, "C"),
            ("Change", 24, "C"), ("Cutoff", 23, "C"), ("Trend", 30, "C")]
    pdf.table_header(cols)
    for i, r in enumerate(rows):
        prev = "-" if r["previous"] is None else r["previous"]
        change = "-" if r["change"] is None else f"{r['change']:+.1f}"
        pdf.table_row([r["subject"], prev, r["current"], change, r["cutoff"], r["trend"]], cols, fill=(i % 2 == 0))

    pdf.ln(3); pdf.section("Improvement Priorities")
    priorities = sorted([r for r in rows if r["improvement_needed"] > 0],
                        key=lambda r: r["improvement_needed"], reverse=True)
    pdf.set_font("N", "", 9)
    if not priorities:
        pdf.multi_cell(0, 6, "All configured career-path subject cutoffs are currently met. Maintain consistency and continue improvement.")
    else:
        for r in priorities:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 6, f"{r['subject']}: {r['improvement_needed']:.1f} marks needed to reach the {r['cutoff']:.1f} cutoff.")
    return bytes(pdf.output())

# ── Student credential sheet ──────────────────────────────────────────────────
def student_credentials_report(rows, grade=None, class_section=None):
    """Admin-only class-wise student login credential sheet."""
    pdf = PDF(); pdf.add_page()
    title = f"Grade {grade}{class_section}" if grade and class_section else (f"Grade {grade}" if grade else "All Student Classes")
    pdf.section(f"Student Login Credentials – {title}")
    pdf.kv("Class", title)
    pdf.kv("Students", len(rows))
    pdf.ln(3)
    cols=[("Student ID",28,"L"),("Student Name",50,"L"),("Class",18,"C"),("Username",30,"L"),("Temporary Password",30,"L"),("Status",20,"C")]
    pdf.table_header(cols)
    for i,r in enumerate(rows):
        pwd=r.get("temporary_password") or "—"
        status="TEMP" if r.get("must_change_password") and r.get("temporary_password") else ("Changed" if r.get("username") else "No Account")
        pdf.table_row([r.get("reg_no"),r.get("full_name"),f"{r.get('grade')}{r.get('class_section','')}",r.get("username") or "—",pwd,status],cols,fill=(i%2==0))
    pdf.ln(4)
    pdf.set_font("N","",8)
    pdf.multi_cell(0,5,"Security note: Temporary passwords are displayed only for Admin credential management. Students should change a temporary password immediately after first login.")
    return bytes(pdf.output())
